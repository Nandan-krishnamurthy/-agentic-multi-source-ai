"""
Response Generator for Agentic AI System

This module generates final natural language responses based on tool results.
It does not decide which tool to use or execute tools.
"""

import json
import os
from typing import Dict, Any, Union, List
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def respond(
    user_question: str,
    tool_name: str,
    tool_reason: str,
    tool_result: Union[Dict, List, None]
) -> Dict[str, Any]:
    """
    Generate a final natural language response based on tool results.
    
    Args:
        user_question: The user's original question
        tool_name: Name of the tool that was used
        tool_reason: Reason why this tool was chosen
        tool_result: Raw results from the tool execution
        
    Returns:
        Dict containing:
            - answer: Final natural language answer
            - explanation: How the answer was formed
            - tool_used: Name of the tool used
            - evidence: Summarized tool result
            
    Raises:
        RuntimeError: If response generation fails
    """
    
    try:
        if tool_name == "direct_answer":
            return _generate_direct_answer(user_question, tool_reason)
        
        elif tool_name in ["vector_search", "graph_search", "web_search"]:
            return _generate_evidence_based_answer(
                user_question,
                tool_name,
                tool_reason,
                tool_result
            )
        
        else:
            # Fallback for unknown tool
            return {
                "answer": "I'm not sure how to process this request.",
                "explanation": f"Unknown tool '{tool_name}' was specified.",
                "tool_used": tool_name,
                "evidence": None
            }
            
    except Exception as e:
        raise RuntimeError(f"Error generating response: {e}")


def _generate_direct_answer(user_question: str, tool_reason: str) -> Dict[str, Any]:
    """
    Generate a direct answer without external data retrieval.
    
    Used for greetings, simple reasoning, or questions that don't require
    external data sources.
    """
    
    # Build prompt for LLM
    prompt = f"""You are a helpful AI assistant. Answer the following question directly and naturally.

Question: {user_question}

Provide a clear, concise, and friendly response."""
    
    # Call LLM to generate answer (direct_answer tool)
    answer = call_llm_for_answer(prompt, "direct_answer")
    
    return {
        "answer": answer,
        "explanation": "Responded directly without needing external data retrieval.",
        "tool_used": "direct_answer",
        "evidence": None
    }


def _generate_evidence_based_answer(
    user_question: str,
    tool_name: str,
    tool_reason: str,
    tool_result: Union[Dict, List, None]
) -> Dict[str, Any]:
    """
    Generate an answer based on retrieved data from tools.
    
    Ensures the answer is grounded in the tool results and doesn't hallucinate.
    """
    
    # Handle empty or None results
    if not tool_result:
        return _generate_fallback_response(user_question, tool_name, tool_reason)
    
    # Extract relevant information from tool results
    if isinstance(tool_result, dict) and "results" in tool_result:
        evidence = tool_result["results"]
    else:
        evidence = tool_result
    
    # Handle empty evidence
    if not evidence:
        return _generate_fallback_response(user_question, tool_name, tool_reason)
    
    # Format evidence for summarization
    evidence_summary = _summarize_evidence(evidence, tool_name)
    
    # Build tool-specific prompt with proper grounding
    if tool_name == "web_search":
        prompt = f"""You are a helpful AI assistant. Answer the question based on web search results.

Question: {user_question}

Web search results:
{json.dumps(evidence, indent=2)}

Provide a factual answer summarizing the most relevant information from the search results. Be concise and cite key facts."""
    
    elif tool_name == "vector_search":
        # Extract text chunks for RAG
        context_chunks = []
        if isinstance(evidence, list):
            for item in evidence:
                if isinstance(item, dict) and "text" in item:
                    context_chunks.append(item["text"])
        
        context = "\n\n".join(context_chunks)
        
        prompt = f"""Answer the question using ONLY the context below.
If the answer is not present in the context, say you do not know.

Context:
{context}

Question:
{user_question}

Answer:"""
    
    elif tool_name == "graph_search":
        # Extract names from graph results
        names = []
        if isinstance(evidence, list):
            for item in evidence:
                if isinstance(item, dict) and "name" in item:
                    names.append(item["name"])
        
        # If we have names, format them properly
        if names:
            # Construct a clear answer based on the question type
            if "ceo" in user_question.lower():
                if len(names) == 1:
                    prompt = f"""Question: {user_question}

The graph database returned: {names[0]}

Provide a clear, direct answer in the format: 'The CEO of [organization] is [name].'"""
                else:
                    prompt = f"""Question: {user_question}

The graph database returned these CEOs: {', '.join(names)}

Provide a clear answer listing the CEOs found."""
            elif "president" in user_question.lower():
                if len(names) == 1:
                    prompt = f"""Question: {user_question}

The graph database returned: {names[0]}

Provide a clear, direct answer in the format: 'The President of [organization] is [name].'"""
                else:
                    prompt = f"""Question: {user_question}

The graph database returned these Presidents: {', '.join(names)}

Provide a clear answer listing the Presidents found."""
            elif "chief scientist" in user_question.lower():
                if len(names) == 1:
                    prompt = f"""Question: {user_question}

The graph database returned: {names[0]}

Provide a clear, direct answer in the format: 'The Chief Scientist at [organization] is [name].'"""
                else:
                    prompt = f"""Question: {user_question}

The graph database returned these Chief Scientists: {', '.join(names)}

Provide a clear answer listing the Chief Scientists found."""
            elif "product" in user_question.lower() or "develop" in user_question.lower():
                prompt = f"""Question: {user_question}

The graph database returned these products: {', '.join(names)}

Provide a clear answer listing the products developed by the organization."""
            else:
                # Generic relationship answer
                prompt = f"""Question: {user_question}

Graph database results:
{json.dumps(evidence, indent=2)}

Provide a clear answer about the relationships or organizational structure based on this data."""
        else:
            # No names found, use generic format
            prompt = f"""Question: {user_question}

Graph database results:
{json.dumps(evidence, indent=2)}

Provide a clear answer based on this relationship data."""
    
    else:
        # Generic evidence-based prompt
        prompt = f"""You are a helpful AI assistant. Answer the question using ONLY the provided evidence.

Question: {user_question}

Evidence:
{json.dumps(evidence, indent=2)}

Provide a natural language answer based on this evidence."""
    
    # Call LLM to generate answer
    answer = call_llm_for_answer(prompt, tool_name)
    
    return {
        "answer": answer,
        "explanation": f"Answer generated using {tool_name}. {tool_reason}",
        "tool_used": tool_name,
        "evidence": evidence_summary
    }


def _generate_fallback_response(
    user_question: str,
    tool_name: str,
    tool_reason: str
) -> Dict[str, Any]:
    """
    Generate a tool-specific fallback response when no results are found.
    """
    
    # Generate tool-specific error messages
    if tool_name == "vector_search":
        answer = "No relevant information was found in the uploaded documents. Please try rephrasing your question or check if the information exists in the knowledge base."
    elif tool_name == "graph_search":
        answer = "No relevant relationship data was found in the graph. The requested information may not be in our organizational database."
    elif tool_name == "web_search":
        answer = "No relevant information was found from web sources. Please try rephrasing your query or using different search terms."
    else:
        answer = f"I attempted to find information using {tool_name}, but no relevant data was found. Could you rephrase your question or provide more context?"
    
    return {
        "answer": answer,
        "explanation": f"No results found from {tool_name}. {tool_reason}",
        "tool_used": tool_name,
        "evidence": None
    }


def _summarize_evidence(evidence: Union[Dict, List], tool_name: str) -> Union[Dict, List]:
    """
    Summarize and clean evidence for inclusion in the response.
    
    This prevents exposing overly verbose raw data in the final response.
    """
    
    if tool_name == "vector_search":
        # Summarize vector search results
        if isinstance(evidence, list):
            return [
                {
                    "text": item.get("text", "")[:200] + "..." if len(item.get("text", "")) > 200 else item.get("text", ""),
                    "score": item.get("score"),
                    "source": item.get("metadata", {}).get("title", "Unknown")
                }
                for item in evidence[:3]  # Limit to top 3 results
            ]
    
    elif tool_name == "graph_search":
        # Summarize graph query results
        if isinstance(evidence, list):
            return evidence[:5]  # Limit to top 5 results
    
    elif tool_name == "web_search":
        # Summarize web search results
        if isinstance(evidence, list):
            return [
                {
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "snippet": item.get("snippet", "")[:150] + "..." if len(item.get("snippet", "")) > 150 else item.get("snippet", "")
                }
                for item in evidence[:3]  # Limit to top 3 results
            ]
    
    # Default: return as is
    return evidence


def call_llm_for_answer(prompt: str, tool_name: str = "direct_answer") -> str:
    """
    Call the Groq LLM to generate an answer.
    
    Args:
        prompt: The prompt for answer generation
        tool_name: The tool being used (for context)
        
    Returns:
        str: The generated answer
        
    Raises:
        RuntimeError: If GROQ_API_KEY is not set or LLM call fails
    """
    
    # Get API key from environment
    api_key = os.getenv("GROQ_API_KEY")
    
    # Guard clause: ensure API key is set
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY environment variable is not set. "
            "Please set it in your .env file or environment."
        )
    
    try:
        # Initialize Groq client
        client = Groq(api_key=api_key)
        
        # Build system prompt based on tool type
        if tool_name == "direct_answer":
            system_content = "You are a friendly and helpful AI assistant. Respond conversationally and naturally to greetings and simple questions."
            temperature = 0.7
            max_tokens = 150
        elif tool_name == "graph_search":
            system_content = "You are a helpful AI assistant. Answer questions based ONLY on the provided graph database results. Be specific about relationships and roles. If the data doesn't contain the answer, say so clearly."
            temperature = 0.1
            max_tokens = 300
        elif tool_name == "web_search":
            system_content = "You are a helpful AI assistant. Summarize web search results into a clear, concise, and factual answer. Cite key information from the sources."
            temperature = 0.3
            max_tokens = 400
        elif tool_name == "vector_search":
            system_content = "You are a helpful AI assistant. Answer questions based ONLY on the provided document chunks. Be concise and factual. If the documents don't contain the answer, say so clearly."
            temperature = 0.1
            max_tokens = 400
        else:
            system_content = "You are a helpful AI assistant. Provide clear and accurate answers based on the available information."
            temperature = 0.3
            max_tokens = 300
        
        # Create chat completion
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Return the generated answer
        return response.choices[0].message.content
        
    except Exception as e:
        raise RuntimeError(f"Failed to generate answer with Groq LLM: {e}")


if __name__ == "__main__":
    # Test the responder with different scenarios
    print("Testing Responder:\n")
    
    # Test 1: Direct answer
    print("Test 1: Direct Answer")
    result = respond(
        user_question="Hello, how are you?",
        tool_name="direct_answer",
        tool_reason="This is a greeting",
        tool_result=None
    )
    print(f"Answer: {result['answer']}")
    print(f"Explanation: {result['explanation']}\n")
    
    # Test 2: Vector search
    print("Test 2: Vector Search")
    result = respond(
        user_question="What is the vacation policy?",
        tool_name="vector_search",
        tool_reason="Question about internal documentation",
        tool_result={
            "tool": "vector_search",
            "results": [
                {
                    "id": "doc_001",
                    "score": 0.92,
                    "text": "Employees are entitled to 15 days of paid vacation per year.",
                    "metadata": {"title": "HR Policy", "page": 12}
                }
            ]
        }
    )
    print(f"Answer: {result['answer']}")
    print(f"Tool Used: {result['tool_used']}")
    print(f"Evidence: {result['evidence']}\n")
    
    # Test 3: Empty results
    print("Test 3: Empty Results")
    result = respond(
        user_question="Who invented the wheel?",
        tool_name="graph_search",
        tool_reason="Relationship query",
        tool_result={"tool": "graph_search", "results": []}
    )
    print(f"Answer: {result['answer']}")
    print(f"Explanation: {result['explanation']}")
