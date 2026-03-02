from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from app.core.config import settings
import json
import re


llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0.7
)


# ─────────────────────────────────────────
# STATE
# ─────────────────────────────────────────

class RoadmapState(TypedDict):
    goal: str
    current_skills: List[str]
    hours_per_day: int
    target_months: int
    skill_gap_analysis: str          # what skills are missing
    phases: List[dict]               # final roadmap phases
    total_weeks: int


# ─────────────────────────────────────────
# NODES
# ─────────────────────────────────────────

def analyze_skill_gap_node(state: RoadmapState) -> RoadmapState:
    """
    Node 1 — Skill Gap Analysis.

    Compares student's current skills
    with what the goal requires.
    Identifies what needs to be learned.
    """
    print(f"🔍 Analyzing skill gap for: {state['goal']}")

    prompt = f"""
    Goal: {state['goal']}
    Current skills: {', '.join(state['current_skills']) if state['current_skills'] else 'Beginner level'}
    
    Analyze the skill gap. List:
    1. What skills this goal requires
    2. What the student already has
    3. What they need to learn
    
    Be specific and practical. Keep response under 200 words.
    """

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        state["skill_gap_analysis"] = response.content.strip()
        print("✅ Skill gap analyzed")
    except Exception as e:
        print(f"Skill gap error: {e}")
        state["skill_gap_analysis"] = f"Need to learn skills required for: {state['goal']}"

    return state


def generate_phases_node(state: RoadmapState) -> RoadmapState:
    """
    Node 2 — Phase Generator.

    Uses skill gap analysis to create
    a structured month-by-month learning plan.
    Each phase builds on the previous one.
    """
    print("📋 Generating roadmap phases...")

    prompt = f"""
    Create a detailed learning roadmap for this goal: {state['goal']}
    
    Skill gap analysis: {state['skill_gap_analysis']}
    Available time: {state['hours_per_day']} hours per day
    Target timeline: {state['target_months']} months
    
    Create 4-6 phases. Each phase should build on the previous.
    
    Return ONLY a valid JSON array like this:
    [
        {{
            "phase_number": 1,
            "title": "Phase title",
            "duration_weeks": 4,
            "topics": ["Topic 1", "Topic 2", "Topic 3", "Topic 4"],
            "resources": ["Resource 1", "Resource 2"],
            "milestone": "What student can do after this phase"
        }}
    ]
    
    Make topics specific and actionable.
    Resources should be real (Coursera, YouTube, books, etc.)
    No extra text, only JSON array.
    """

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        cleaned = response.content.strip()
        cleaned = re.sub(r'```json\s*', '', cleaned)
        cleaned = re.sub(r'```\s*', '', cleaned)
        cleaned = cleaned.strip()

        phases = json.loads(cleaned)
        state["phases"] = phases
        state["total_weeks"] = sum(p.get("duration_weeks", 4) for p in phases)
        print(f"✅ Generated {len(phases)} phases, {state['total_weeks']} total weeks")

    except Exception as e:
        print(f"Phase generation error: {e}")
        state["phases"] = _fallback_phases(state["goal"], state["target_months"])
        state["total_weeks"] = state["target_months"] * 4

    return state


def validate_roadmap_node(state: RoadmapState) -> RoadmapState:
    """
    Node 3 — Validation.

    Makes sure the roadmap is realistic
    based on available hours and timeline.
    Adjusts if needed.
    """
    phases = state["phases"]
    total_weeks = state["total_weeks"]
    target_weeks = state["target_months"] * 4

    # If roadmap is too long, compress phases
    if total_weeks > target_weeks * 1.2:
        compression_ratio = target_weeks / total_weeks
        for phase in phases:
            original = phase.get("duration_weeks", 4)
            phase["duration_weeks"] = max(2, int(original * compression_ratio))
        state["total_weeks"] = sum(p.get("duration_weeks", 4) for p in phases)
        print(f"⚡ Compressed roadmap to {state['total_weeks']} weeks")

    state["phases"] = phases
    return state


def _fallback_phases(goal: str, months: int) -> list:
    """Fallback if AI fails"""
    weeks_per_phase = max(2, (months * 4) // 4)
    return [
        {
            "phase_number": 1,
            "title": "Foundation",
            "duration_weeks": weeks_per_phase,
            "topics": ["Core concepts", "Basic tools", "Environment setup"],
            "resources": ["YouTube tutorials", "Official documentation"],
            "milestone": f"Ready to start working towards {goal}"
        },
        {
            "phase_number": 2,
            "title": "Core Skills",
            "duration_weeks": weeks_per_phase,
            "topics": ["Main skills", "Practical exercises", "Small projects"],
            "resources": ["Online courses", "Practice problems"],
            "milestone": "Can build basic projects"
        },
        {
            "phase_number": 3,
            "title": "Advanced Topics",
            "duration_weeks": weeks_per_phase,
            "topics": ["Advanced concepts", "Real projects", "Best practices"],
            "resources": ["Advanced courses", "GitHub projects"],
            "milestone": "Can work on real-world problems"
        },
        {
            "phase_number": 4,
            "title": "Portfolio & Job Prep",
            "duration_weeks": weeks_per_phase,
            "topics": ["Portfolio projects", "Interview prep", "Resume update"],
            "resources": ["LeetCode", "Mock interviews", "LinkedIn"],
            "milestone": f"Ready to apply for {goal}"
        }
    ]


# ─────────────────────────────────────────
# BUILD GRAPH
# ─────────────────────────────────────────

def build_roadmap_graph():
    graph = StateGraph(RoadmapState)

    graph.add_node("analyze_skill_gap", analyze_skill_gap_node)
    graph.add_node("generate_phases", generate_phases_node)
    graph.add_node("validate_roadmap", validate_roadmap_node)

    graph.set_entry_point("analyze_skill_gap")
    graph.add_edge("analyze_skill_gap", "generate_phases")
    graph.add_edge("generate_phases", "validate_roadmap")
    graph.add_edge("validate_roadmap", END)

    return graph.compile()


roadmap_graph = build_roadmap_graph()


def generate_roadmap(
    goal: str,
    current_skills: list = None,
    hours_per_day: int = 2,
    target_months: int = 6
) -> dict:
    """Run the roadmap agent and return phases"""

    initial_state: RoadmapState = {
        "goal": goal,
        "current_skills": current_skills or [],
        "hours_per_day": hours_per_day,
        "target_months": target_months,
        "skill_gap_analysis": "",
        "phases": [],
        "total_weeks": 0
    }

    result = roadmap_graph.invoke(initial_state)

    return {
        "phases": result["phases"],
        "total_weeks": result["total_weeks"],
        "skill_gap_analysis": result["skill_gap_analysis"]
    }