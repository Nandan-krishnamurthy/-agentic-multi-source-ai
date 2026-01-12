from pinecone import Pinecone
from config import PINECONE_API_KEY

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index("mcp-agentic-rag-index")

stats = index.describe_index_stats()
print(stats)
