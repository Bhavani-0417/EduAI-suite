import logging

import chromadb
from app.core.config import settings
from app.services.vault.encryption_service import decrypt_notes_text, encrypt_notes_text

logger = logging.getLogger(__name__)


def get_chroma_client():
    """Create and return the persistent ChromaDB client."""
    return chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)


def get_or_create_collection(student_id: str):
    """Each student gets an isolated ChromaDB collection."""
    client = get_chroma_client()
    collection_name = f"student_{student_id.replace('-', '_')}"
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def add_to_collection(
    student_id: str,
    note_id: str,
    chunks: list[str],
    metadata: dict,
):
    """Embed plaintext in memory, but persist only encrypted document text."""
    if not chunks:
        return

    collection = get_or_create_collection(student_id)
    ids = [f"{note_id}_chunk_{index}" for index in range(len(chunks))]
    embedding_function = getattr(collection, "_embedding_function", None)
    if embedding_function is None:
        raise RuntimeError("ChromaDB collection has no configured embedding function.")

    # Keep the existing collection's embedding model so pre-existing vectors
    # remain comparable with new queries; plaintext never reaches Chroma storage.
    embeddings = embedding_function(chunks)
    if hasattr(embeddings, "tolist"):
        embeddings = embeddings.tolist()

    # Store the stable Note primary key only; avoid filenames and OCR metadata.
    safe_metadata = {"note_id": note_id}
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=[encrypt_notes_text(chunk) for chunk in chunks],
        metadatas=[safe_metadata.copy() for _ in chunks],
    )
    logger.info("Indexed %d encrypted note chunks for student %s", len(chunks), student_id)


def search_collection(
    student_id: str,
    query: str,
    n_results: int = 5,
    subject_filter: str = None,
) -> dict:
    """Search vectors and decrypt returned text in memory for the RAG pipeline."""
    collection = get_or_create_collection(student_id)
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
        )
        document_batches = results.get("documents") or []
        if document_batches and document_batches[0]:
            results["documents"][0] = [
                decrypt_notes_text(document) or ""
                for document in document_batches[0]
            ]
        return results
    except Exception:
        # Fail closed: never send undeciphered text/ciphertext to the LLM.
        logger.exception("ChromaDB note search/decryption failed.")
        return {"documents": [[]], "metadatas": [[]], "ids": [[]]}


def delete_from_collection(student_id: str, note_id: str):
    """Delete the encrypted text and vectors associated with one note ID."""
    collection = get_or_create_collection(student_id)
    results = collection.get(where={"note_id": note_id}, include=[])
    if results.get("ids"):
        collection.delete(ids=results["ids"])
