"""
Web Search Tool

This tool performs web searches using Tavily API to retrieve external information.
"""

import os
from typing import Dict, Any
from tavily import TavilyClient


def search(query: str) -> Dict[str, Any]:
    """
    Search the web for information using Tavily.
    
    Args:
        query: The search query
        
    Returns:
        Dict containing:
            - answer: Short summary/answer from Tavily
            - results: List of source URLs with titles and content
            - query: The original query
            
    Raises:
        RuntimeError: If web search fails
    """
    
    try:
        # Initialize Tavily client
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable not set")
        
        client = TavilyClient(api_key=api_key)
        
        # Perform search
        response = client.search(query=query, max_results=5)
        
        # Extract answer and sources
        answer = response.get("answer", "")
        results = response.get("results", [])
        
        # Format results
        formatted_results = [
            {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
                "score": result.get("score", 0)
            }
            for result in results
        ]
        
        return {
            "answer": answer,
            "results": formatted_results,
            "query": query,
            "sources": [r["url"] for r in formatted_results if r.get("url")]
        }
        
    except Exception as e:
        raise RuntimeError(f"Web search failed: {e}")
