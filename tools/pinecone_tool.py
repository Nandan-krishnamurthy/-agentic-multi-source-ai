"""
Pinecone Vector Search Tool

This tool performs semantic search on documents stored in Pinecone vector database.
Uses the new Pinecone Python SDK (v3.0+) with direct client initialization.
"""

import os
from typing import List, Dict, Any
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer


# Initialize embedding model (cached for reuse)
_embedding_model = None


def _get_embedding_model():
    """Get or initialize the embedding model."""
    global _embedding_model
    if _embedding_model is None:
        # Using a lightweight model for fast embeddings
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model


def _generate_embedding(text: str) -> List[float]:
    """
    Generate embedding vector for the given text.
    
    Args:
        text: Text to embed
        
    Returns:
        List of floats representing the embedding vector
    """
    model = _get_embedding_model()
    embedding = model.encode(text, convert_to_tensor=False)
    return embedding.tolist()


def search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Search for relevant documents in Pinecone vector database.
    
    Args:
        query: The search query
        top_k: Number of top results to return
        
    Returns:
        List of matching documents with metadata and scores
        
    Raises:
        RuntimeError: If vector search fails
    """
    
    try:
        # Read Pinecone credentials from environment
        api_key = os.getenv("PINECONE_API_KEY")
        index_name = os.getenv("PINECONE_INDEX_NAME")
        
        if not api_key or not index_name:
            raise ValueError("PINECONE_API_KEY and PINECONE_INDEX_NAME environment variables must be set")
        
        # Initialize Pinecone
        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)
        
        # Generate query embedding
        query_embedding = _generate_embedding(query)
        
        # Query Pinecone with namespace
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            namespace="agentic-multi-source"
        )
        
        # Format results
        matched_documents = [
            {
                "id": match.id,
                "score": match.score,
                "text": match.metadata.get("text", ""),
                "metadata": match.metadata
            }
            for match in results.matches
        ]
        
        return matched_documents
        
    except Exception as e:
        raise RuntimeError(f"Pinecone vector search failed: {e}")
