import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings


def get_chroma_client():
    """
    Create and return ChromaDB client.
    ChromaDB is our vector database —
    stores text as mathematical vectors for similarity search.
    
    persist_directory = saves data to disk so it survives restarts
    """
    client = chromadb.PersistentClient(
        path=settings.CHROMA_PERSIST_DIR
    )
    return client


def get_or_create_collection(student_id: str):
    """
    Each student gets their own ChromaDB collection.
    Think of collection = a folder of vectors for that student.
    
    Collection name format: student_{id}
    ChromaDB collection names must be alphanumeric + underscores only
    """
    client = get_chroma_client()
    
    # Replace hyphens in UUID with underscores for ChromaDB
    collection_name = f"student_{student_id.replace('-', '_')}"
    
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}  # use cosine similarity
    )
    return collection


def add_to_collection(
    student_id: str,
    note_id: str,
    chunks: list[str],
    metadata: dict
):
    """
    Add text chunks to student's ChromaDB collection.
    
    chunks = list of text pieces (each 500 chars max)
    metadata = info about where this text came from
    """
    collection = get_or_create_collection(student_id)
    
    # Each chunk needs a unique ID
    ids = [f"{note_id}_chunk_{i}" for i in range(len(chunks))]
    
    # Add same metadata to all chunks from this note
    metadatas = [metadata for _ in chunks]
    
    collection.add(
        ids=ids,
        documents=chunks,
        metadatas=metadatas
    )
    
    print(f"✅ Added {len(chunks)} chunks to ChromaDB for student {student_id}")


def search_collection(
    student_id: str,
    query: str,
    n_results: int = 5,
    subject_filter: str = None
) -> dict:
    """
    Search student's notes using semantic similarity.
    Returns most relevant chunks for the query.
    
    This is the RAG (Retrieval) part —
    find relevant text before sending to AI.
    """
    collection = get_or_create_collection(student_id)
    
    # Build filter if subject specified
    where = None
    if subject_filter:
        where = {"subject": subject_filter}
    
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )
        return results
    except Exception as e:
        print(f"ChromaDB search error: {e}")
        return {"documents": [[]], "metadatas": [[]]}


def delete_from_collection(student_id: str, note_id: str):
    """Delete all chunks of a specific note from ChromaDB"""
    collection = get_or_create_collection(student_id)
    
    # Get all chunk IDs for this note
    results = collection.get(where={"note_id": note_id})
    
    if results["ids"]:
        collection.delete(ids=results["ids"])
        print(f"✅ Deleted note {note_id} from ChromaDB")