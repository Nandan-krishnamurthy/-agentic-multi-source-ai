# Agentic Multi-Source AI

An intelligent multi-source Retrieval-Augmented Generation (RAG) system that combines Graph RAG, Vector RAG, and Web Search with an LLM-based agent for optimal tool routing and fallback strategies.

## Overview

This project implements an **agentic RAG system** that intelligently routes user queries to the most appropriate data source—Graph Database (Neo4j), Vector Database (Pinecone), or Web Search—based on question intent and knowledge scope. The agent automatically falls back to alternative sources when internal knowledge is insufficient, ensuring robust answers across internal and external domains.

## Key Features

- **🧠 Intelligent Agent Planning**: LLM-based routing that understands question intent and knowledge boundaries
- **🕸️ Graph RAG (Neo4j)**: Relationship queries for organizational structure, roles, and entity connections
- **📄 Vector RAG (Pinecone)**: Semantic search over document embeddings for descriptive and explanatory content
- **🌐 Web Search Fallback**: Universal fallback for external entities, general knowledge, and real-time information
- **🔄 Automatic Fallback Chain**: `graph_search → vector_search → web_search` with transparent user feedback
- **💬 Streamlit UI**: Interactive web interface for asking questions and viewing retrieval results
- **🎯 Scope-Aware Routing**: Internal knowledge (OpenAI-specific) vs. external/general knowledge

## Architecture

The system follows a **three-stage agentic workflow**:

```
User Question
     ↓
[1. Planner] ────→ Analyzes intent & knowledge scope
     ↓                Uses LLM to select tool
     ↓
[2. Executor] ───→ Executes selected tool
     ↓                Implements fallback chain
     ↓                (graph → vector → web)
     ↓
[3. Responder] ──→ Generates natural language answer
     ↓                Grounded in retrieved evidence
     ↓
Final Answer
```

### Routing Logic

| Question Type | Tool | Example |
|---------------|------|---------|
| Internal relationships | `graph_search` | "Who is the CEO of OpenAI?" |
| Internal documents | `vector_search` | "What is OpenAI's mission?" |
| External entities | `web_search` | "Who is the CEO of NVIDIA?" |
| General knowledge | `web_search` | "What is machine learning?" |
| Greetings | `direct_answer` | "Hello" |

## Tech Stack

- **Frontend**: Streamlit
- **Agent Framework**: Custom (Planner → Executor → Responder)
- **LLM**: Groq (Llama 3.3 70B)
- **Graph Database**: Neo4j Aura
- **Vector Database**: Pinecone
- **Web Search**: Tavily API
- **Embeddings**: OpenAI (text-embedding-3-small)

## Project Structure

```
agentic-multi-source-ai/
├── agent/
│   ├── planner.py      # LLM-based tool selection
│   ├── executor.py     # Tool execution with fallback
│   └── responder.py    # Answer generation
├── tools/
│   ├── neo4j_tool.py       # Graph search (Neo4j)
│   ├── pinecone_tool.py    # Vector search (Pinecone)
│   └── web_search_tool.py  # Web search (Tavily)
├── data/
│   ├── document_ingestion.py  # PDF → Pinecone
│   └── graph_ingestion.py     # Data → Neo4j
├── documents/          # PDF files for ingestion
├── app.py              # Streamlit UI
├── config.py           # Configuration
└── requirements.txt    # Dependencies
```

## Setup

### Prerequisites

- Python 3.9+
- Neo4j Aura account (or local Neo4j instance)
- Pinecone account
- Groq API key
- OpenAI API key (for embeddings)
- Tavily API key (for web search)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/agentic-multi-source-ai.git
   cd agentic-multi-source-ai
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   # LLM
   GROQ_API_KEY=your_groq_api_key_here

   # Embeddings
   OPENAI_API_KEY=your_openai_api_key_here

   # Neo4j
   NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_neo4j_password_here

   # Pinecone
   PINECONE_API_KEY=your_pinecone_api_key_here
   PINECONE_INDEX_NAME=your_index_name

   # Web Search
   TAVILY_API_KEY=your_tavily_api_key_here
   ```

5. **Ingest data**
   
   Populate Neo4j graph:
   ```bash
   python data/graph_ingestion.py
   ```
   
   Ingest documents to Pinecone:
   ```bash
   python data/document_ingestion.py
   ```

6. **Run the application**
   ```bash
   streamlit run app.py
   ```

7. **Open in browser**
   
   Navigate to `http://localhost:8501`

## Usage Examples

**Internal Queries (Graph/Vector):**
- "Who is the CEO of OpenAI?"
- "What is OpenAI's mission?"
- "Describe OpenAI's system architecture"

**External Queries (Web Search):**
- "Who is the CEO of Google?"
- "Toyota"
- "Apple revenue"
- "What is machine learning?"

**Fallback Scenarios:**
- Ask about internal data not in the database → automatic web search
- Single-word external entities → direct to web search

## Environment Variables

All API keys and credentials must be stored in a `.env` file. **Never commit secrets to version control.**

Required variables:
- `GROQ_API_KEY` - Groq LLM API key
- `OPENAI_API_KEY` - OpenAI embeddings API key
- `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` - Neo4j credentials
- `PINECONE_API_KEY`, `PINECONE_INDEX_NAME` - Pinecone credentials
- `TAVILY_API_KEY` - Tavily web search API key

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---
## 📌 Notes
Users can upload their own documents for vector-based querying.  
A sample document is included for demonstration.

**Note**: This project is designed for educational and demonstration purposes. Ensure proper security practices when deploying to production.
