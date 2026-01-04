"""
LLM-based Planner for Agentic AI System

This module determines which tool to use based on the user's question intent.
It uses an LLM to reason about the question rather than hard-coded rules.
"""

import json
import os
from typing import Dict
from groq import Groq
from dotenv import load_dotenv

# Load environment variables at module import
load_dotenv()


def plan(user_question: str) -> Dict[str, str]:
    """
    Analyze user question and determine which tool to use.
    
    Args:
        user_question: The user's input question
        
    Returns:
        Dict with keys:
            - tool: one of ["direct_answer", "vector_search", "graph_search", "web_search"]
            - reason: explanation of why this tool was chosen
            
    Raises:
        ValueError: If LLM returns invalid tool or malformed JSON
        RuntimeError: If LLM call fails
    """
    
    # Build the system prompt for the LLM
    system_prompt = """You are a routing assistant for an AI system. 
Your job is to analyze the user's question and decide which tool should handle it.

KNOWLEDGE SCOPE - CRITICAL:
Our internal knowledge (vector_search + graph_search) contains information ONLY about:
- OpenAI (the organization)
- OpenAI's products (GPT-4, ChatGPT)
- OpenAI's leadership (CEO, President, Chief Scientist)
- OpenAI's system architecture and technologies
- OpenAI's mission and approach

ANYTHING ELSE requires web_search, including:
- Other companies (Google, Microsoft, Apple, NVIDIA, Tesla, Toyota, etc.)
- General world knowledge, history, finance, science
- Real-world facts, statistics, current events
- People not affiliated with OpenAI
- Products not made by OpenAI

Available tools:
1. direct_answer - For greetings (hi, hello, hey), casual messages (thanks, bye), simple math, or questions answerable without external data
2. vector_search - For OpenAI document-based questions: mission, vision, architecture, technologies, explanations, limitations, descriptions
3. graph_search - ONLY for explicit OpenAI relationship queries: who is the CEO/President/Chief Scientist, which products are built by OpenAI
4. web_search - For ALL external entities, general knowledge, current events, non-OpenAI organizations/people/products

CRITICAL ROUTING RULES:

WEB SEARCH (Universal Fallback - Use FIRST for External Knowledge):
Use web_search for:
- ANY question about companies other than OpenAI (Google, Microsoft, Apple, NVIDIA, Tesla, Toyota, Amazon, etc.)
- ANY question about people not affiliated with OpenAI (Elon Musk, Bill Gates, Sundar Pichai, etc.)
- ANY question about products not made by OpenAI (iPhone, Windows, Chrome, etc.)
- General world knowledge: history, geography, science, finance, statistics
- Current events, latest news, recent announcements, real-time information
- Questions that could be answered by Google search
- Single-word queries about entities ("Toyota", "NVIDIA", "Apple")
- CEO/leadership queries for companies other than OpenAI

VECTOR SEARCH (OpenAI Internal Documents ONLY):
Use vector_search ONLY when the question is specifically about OpenAI:
- OpenAI's mission, vision, goals, objectives, values, purpose
- OpenAI's system architecture, design, structure, how OpenAI's systems work
- Technologies OpenAI uses, OpenAI's technical stack
- How OpenAI does something, explanations about OpenAI's approach
- Limitations, challenges mentioned in OpenAI documents
- What OpenAI does, OpenAI's capabilities, features

GRAPH SEARCH (OpenAI Relationships ONLY):
Use graph_search ONLY for explicit OpenAI relationship queries:
- Who is the CEO/President/Chief Scientist of OpenAI (must be OpenAI)
- Who works at OpenAI (must be OpenAI)
- Which products are built by OpenAI (must be OpenAI)
- OpenAI organizational hierarchy

EXAMPLES:
✓ "hi" → direct_answer (greeting)
✓ "What can you do?" → direct_answer (simple question)

✓ "Who is the CEO of OpenAI?" → graph_search (OpenAI relationship)
✓ "Who is the President of OpenAI?" → graph_search (OpenAI relationship)
✓ "Which products are built by OpenAI?" → graph_search (OpenAI relationship)

✓ "What is OpenAI's mission?" → vector_search (OpenAI document content)
✓ "What is OpenAI?" → vector_search (OpenAI information)
✓ "What does OpenAI do?" → vector_search (OpenAI information)
✓ "Describe OpenAI's system architecture" → vector_search (OpenAI technical description)
✓ "How does OpenAI use vector databases?" → vector_search (OpenAI explanation)

✓ "Toyota" → web_search (external company)
✓ "What is Toyota" → web_search (external company)
✓ "NVIDIA" → web_search (external company)
✓ "Who is the CEO of Google?" → web_search (external organization)
✓ "Who is the CEO of NVIDIA?" → web_search (external organization)
✓ "Apple revenue" → web_search (external company financial data)
✓ "Tesla cars" → web_search (external company products)
✓ "Elon Musk" → web_search (external person)
✓ "iPhone" → web_search (external product)
✓ "Latest news about OpenAI" → web_search (current events)
✓ "History of AI" → web_search (general knowledge)
✓ "What is machine learning?" → web_search (general knowledge)

CRITICAL: You must respond with ONLY valid JSON in this exact format:
{
  "tool": "tool_name_here",
  "reason": "brief explanation here"
}

Do not include any other text, markdown formatting, code blocks, or explanations outside the JSON."""

    user_prompt = f"Question: {user_question}\n\nWhich tool should handle this question?"
    
    try:
        # Call LLM to determine the appropriate tool
        llm_response = call_llm(system_prompt, user_prompt)
        
        # Parse the JSON response
        result = json.loads(llm_response)
        
        # Validate the response structure
        if "tool" not in result or "reason" not in result:
            raise ValueError("LLM response missing required keys 'tool' or 'reason'")
        
        # Validate the tool choice
        valid_tools = ["direct_answer", "vector_search", "graph_search", "web_search"]
        if result["tool"] not in valid_tools:
            raise ValueError(f"Invalid tool '{result['tool']}'. Must be one of {valid_tools}")
        
        return result
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse LLM response as JSON: {e}")
    except Exception as e:
        raise RuntimeError(f"Error during planning: {e}")


def call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    Call the Groq LLM with the given prompts.
    
    Args:
        system_prompt: The system instruction for the LLM
        user_prompt: The user's question/prompt
        
    Returns:
        str: The LLM's response
        
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
    
    # Initialize Groq client with explicit API key
    client = Groq(api_key=api_key)
    
    # Create chat completion
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,
        max_tokens=200
    )
    
    # Return the raw text response
    return response.choices[0].message.content


if __name__ == "__main__":
    # Test the planner with sample questions
    test_questions = [
        "Hello, how are you?",
        "What is our vacation policy?",
        "Who does John Smith report to?",
        "What are the latest developments in AI?",
    ]
    
    print("Testing Planner:\n")
    for question in test_questions:
        print(f"Question: {question}")
        try:
            result = plan(question)
            print(f"Tool: {result['tool']}")
            print(f"Reason: {result['reason']}\n")
        except Exception as e:
            print(f"Error: {e}\n")
