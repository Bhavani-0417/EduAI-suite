from typing import TypedDict, List, Optional, Annotated
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import operator

from app.core.config import settings
from app.services.ai.chroma_service import search_collection


# ─────────────────────────────────────────
# STATE — shared data flowing through graph
# ─────────────────────────────────────────

class ChatState(TypedDict):
    """
    State passed between all nodes in the LangGraph.
    Every node can read and update this.
    """
    student_id: str
    user_message: str
    mode: str                        # general / notes / auto
    subject_filter: Optional[str]
    conversation_history: List[dict]
    retrieved_context: str           # text from ChromaDB search
    sources: List[str]               # note file names used
    final_answer: str                # AI response
    decision: str                    # which path was taken


# ─────────────────────────────────────────
# LLM SETUP
# ─────────────────────────────────────────

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0.7
)


# ─────────────────────────────────────────
# NODES — each is one step in the graph
# ─────────────────────────────────────────

def decide_mode_node(state: ChatState) -> ChatState:
    """
    Node 1 — Decision Router.

    If mode is AUTO:
      Ask Gemini: does this question need notes or general knowledge?

    If mode is NOTES or GENERAL:
      Use whatever student specified.

    This is the 'brain' of the agent.
    """
    mode = state["mode"]

    if mode != "auto":
        # Student specified mode — use it directly
        state["decision"] = mode
        return state

    # AUTO mode — let AI decide
    decision_prompt = f"""
    A student asked: "{state['user_message']}"

    Decide if this question:
    A) Needs to search the student's uploaded study notes (academic/subject question)
    B) Can be answered from general knowledge (casual/general question)

    Reply with ONLY one word: NOTES or GENERAL
    """

    try:
        response = llm.invoke([HumanMessage(content=decision_prompt)])
        decision = response.content.strip().upper()

        if "NOTES" in decision:
            state["decision"] = "notes"
        else:
            state["decision"] = "general"

    except Exception as e:
        print(f"Decision error: {e}")
        state["decision"] = "general"

    print(f"🔀 Decision: {state['decision']} for question: {state['user_message'][:50]}")
    return state


def retrieve_notes_node(state: ChatState) -> ChatState:
    """
    Node 2 — RAG Retrieval.
    Only runs if decision = 'notes'.

    Searches ChromaDB for relevant content
    from student's uploaded notes.
    """
    print(f"📚 Searching notes for: {state['user_message'][:50]}")

    try:
        results = search_collection(
            student_id=state["student_id"],
            query=state["user_message"],
            n_results=5,
            subject_filter=state.get("subject_filter")
        )

        context_chunks = []
        sources = []

        if results.get("documents") and results["documents"][0]:
            context_chunks = results["documents"][0]

            if results.get("metadatas") and results["metadatas"][0]:
                for meta in results["metadatas"][0]:
                    source = f"{meta.get('subject', 'Notes')} — {meta.get('file_name', 'Unknown')}"
                    if source not in sources:
                        sources.append(source)

        state["retrieved_context"] = "\n\n".join(context_chunks)
        state["sources"] = sources

    except Exception as e:
        print(f"Retrieval error: {e}")
        state["retrieved_context"] = ""
        state["sources"] = []

    return state


def generate_answer_node(state: ChatState) -> ChatState:
    """
    Node 3 — Answer Generation.
    Always runs — generates final AI response.

    Uses:
    - retrieved_context if in notes mode
    - conversation_history for multi-turn memory
    - Gemini to generate the reply
    """
    messages = []

    # Build system prompt based on mode
    if state["decision"] == "notes" and state["retrieved_context"]:
        system_prompt = f"""You are EduAI, a helpful study assistant for students.
        
Answer the student's question using the provided context from their uploaded notes.
If the answer is not in the context, say so clearly and offer general help.
Be friendly, clear, and educational.

CONTEXT FROM STUDENT'S NOTES:
{state['retrieved_context']}"""
    else:
        system_prompt = """You are EduAI, a helpful AI assistant for students.
        
You help with academic questions, career advice, study tips, and general queries.
Be friendly, encouraging, and concise. Use examples when helpful."""

    messages.append(SystemMessage(content=system_prompt))

    # Add conversation history for memory
    for msg in state.get("conversation_history", [])[-6:]:  # last 6 messages
        if msg.get("role") == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg.get("role") == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    # Add current message
    messages.append(HumanMessage(content=state["user_message"]))

    try:
        response = llm.invoke(messages)
        state["final_answer"] = response.content.strip()
    except Exception as e:
        print(f"Generation error: {e}")
        state["final_answer"] = "Sorry, I couldn't process that right now. Please try again."

    return state


# ─────────────────────────────────────────
# CONDITIONAL EDGE — routing logic
# ─────────────────────────────────────────

def route_after_decision(state: ChatState) -> str:
    """
    After decide_mode_node runs,
    this function tells LangGraph which node to go to next.

    Returns node name as string.
    """
    if state["decision"] == "notes":
        return "retrieve_notes"    # go to retrieval node
    else:
        return "generate_answer"   # skip retrieval, go straight to generation


# ─────────────────────────────────────────
# BUILD THE GRAPH
# ─────────────────────────────────────────

def build_chat_graph():
    """
    Build and compile the LangGraph.

    Graph structure:
    decide_mode → [if notes] → retrieve_notes → generate_answer → END
    decide_mode → [if general] → generate_answer → END

    Think of it like a flowchart in code.
    """
    graph = StateGraph(ChatState)

    # Add all nodes
    graph.add_node("decide_mode", decide_mode_node)
    graph.add_node("retrieve_notes", retrieve_notes_node)
    graph.add_node("generate_answer", generate_answer_node)

    # Set entry point
    graph.set_entry_point("decide_mode")

    # Add conditional routing after decision
    graph.add_conditional_edges(
        "decide_mode",
        route_after_decision,
        {
            "retrieve_notes": "retrieve_notes",
            "generate_answer": "generate_answer"
        }
    )

    # After retrieval always goes to generation
    graph.add_edge("retrieve_notes", "generate_answer")

    # Generation is the end
    graph.add_edge("generate_answer", END)

    return graph.compile()


# Compile graph once at startup
chat_graph = build_chat_graph()


# ─────────────────────────────────────────
# MAIN FUNCTION TO CALL FROM ROUTES
# ─────────────────────────────────────────

def run_chat_agent(
    student_id: str,
    user_message: str,
    mode: str = "auto",
    subject_filter: str = None,
    conversation_history: list = None
) -> dict:
    """
    Run the LangGraph chat agent.
    Called from the API route.
    """

    initial_state: ChatState = {
        "student_id": student_id,
        "user_message": user_message,
        "mode": mode,
        "subject_filter": subject_filter,
        "conversation_history": conversation_history or [],
        "retrieved_context": "",
        "sources": [],
        "final_answer": "",
        "decision": ""
    }

    result = chat_graph.invoke(initial_state)

    return {
        "message": result["final_answer"],
        "mode_used": result["decision"],
        "sources": result["sources"]
    }