"""
Document Ingestion Script for Vector Search

This script reads PDF documents, extracts text, generates embeddings,
and stores them in Pinecone for semantic search.
"""

import os
import glob
from typing import List, Dict, Any
from pathlib import Path
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Initialize embedding model globally for reuse
_embedding_model = None


def get_embedding_model():
    """Get or initialize the embedding model."""
    global _embedding_model
    if _embedding_model is None:
        print("Loading embedding model...")
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✓ Embedding model loaded")
    return _embedding_model


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text as a single string
    """
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from {pdf_path}: {e}")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Text to split
        chunk_size: Size of each chunk in characters
        overlap: Number of overlapping characters between chunks
        
    Returns:
        List of text chunks
    """
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        
        # Only add non-empty chunks
        if chunk.strip():
            chunks.append(chunk.strip())
        
        start += (chunk_size - overlap)
    
    return chunks


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts.
    
    Args:
        texts: List of text strings
        
    Returns:
        List of embedding vectors
    """
    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_tensor=False, show_progress_bar=True)
    return [emb.tolist() for emb in embeddings]


def ingest_documents(documents_dir: str = "../documents"):
    """
    Main ingestion function that processes PDFs and stores them in Pinecone.
    
    Args:
        documents_dir: Directory containing PDF files
    """
    
    # Read environment variables
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME")
    
    if not api_key or not index_name:
        raise ValueError("PINECONE_API_KEY and PINECONE_INDEX_NAME environment variables must be set")
    
    print(f"\nStarting document ingestion from: {documents_dir}")
    
    # Find all PDF files
    pdf_pattern = os.path.join(documents_dir, "*.pdf")
    pdf_files = glob.glob(pdf_pattern)
    
    if not pdf_files:
        print(f"⚠️  No PDF files found in {documents_dir}")
        return
    
    print(f"✓ Found {len(pdf_files)} PDF file(s)")
    
    # Initialize Pinecone
    print("\nConnecting to Pinecone...")
    pc = Pinecone(api_key=api_key)
    
    # Check if index exists, create if needed
    existing_indexes = [idx.name for idx in pc.list_indexes()]
    
    if index_name not in existing_indexes:
        print(f"Creating new index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=384,  # all-MiniLM-L6-v2 produces 384-dimensional embeddings
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        print(f"✓ Index '{index_name}' created")
    else:
        print(f"✓ Using existing index: {index_name}")
    
    index = pc.Index(index_name)
    
    # Process each PDF file
    total_chunks = 0
    
    for pdf_file in pdf_files:
        filename = os.path.basename(pdf_file)
        print(f"\n📄 Processing: {filename}")
        
        try:
            # Extract text
            print("  - Extracting text...")
            text = extract_text_from_pdf(pdf_file)
            print(f"  ✓ Extracted {len(text)} characters")
            
            # Chunk text
            print("  - Chunking text...")
            chunks = chunk_text(text, chunk_size=500, overlap=50)
            print(f"  ✓ Created {len(chunks)} chunks")
            
            if not chunks:
                print(f"  ⚠️  No content extracted from {filename}")
                continue
            
            # Generate embeddings
            print("  - Generating embeddings...")
            embeddings = generate_embeddings(chunks)
            print(f"  ✓ Generated {len(embeddings)} embeddings")
            
            # Prepare vectors for upsert
            vectors = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = f"{Path(filename).stem}_chunk_{i}"
                vectors.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": {
                        "text": chunk,
                        "filename": filename,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                })
            
            # Upsert to Pinecone in batches
            print("  - Uploading to Pinecone...")
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                index.upsert(vectors=batch, namespace="agentic-multi-source")
            
            print(f"  ✓ Uploaded {len(vectors)} vectors to Pinecone")
            total_chunks += len(chunks)
            
        except Exception as e:
            print(f"  ❌ Error processing {filename}: {e}")
            continue
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"✅ Document ingestion completed!")
    print(f"   - Total PDFs processed: {len(pdf_files)}")
    print(f"   - Total chunks created: {total_chunks}")
    print(f"   - Index: {index_name}")
    print("=" * 60)


def main():
    """Main entry point for the ingestion script."""
    try:
        # Get the documents directory path (relative to script location)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        documents_dir = os.path.join(script_dir, "..", "documents")
        
        # Create documents directory if it doesn't exist
        os.makedirs(documents_dir, exist_ok=True)
        
        ingest_documents(documents_dir)
        
    except Exception as e:
        print(f"\n❌ Error during document ingestion: {e}")
        raise


if __name__ == "__main__":
    main()
