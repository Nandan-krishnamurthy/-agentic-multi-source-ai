import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# LLM
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Vector DB (Pinecone v3.0+ - no PINECONE_ENVIRONMENT needed)
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# Graph DB
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Web Search
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
