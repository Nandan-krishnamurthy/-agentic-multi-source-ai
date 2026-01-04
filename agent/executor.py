"""
Tool Executor for Agentic AI System

This module executes tools based on the planner's decision.
It does not decide which tool to use or generate final answers.
"""

from typing import Dict, Any
from tools import pinecone_tool, neo4j_tool, web_search_tool


def execute(tool_name: str, user_question: str, fallback_to_vector: bool = True, fallback_to_web: bool = True) -> Dict[str, Any]:
    """
    Execute the specified tool with the user's question.
    
    Implements automatic fallback chain:
    - graph_search -> vector_search -> web_search
    - vector_search -> web_search
    
    Args:
        tool_name: Name of the tool to execute 
                   ("direct_answer", "vector_search", "graph_search", "web_search")
        user_question: The user's input question
        fallback_to_vector: If True, fallback to vector_search when graph_search returns empty
        fallback_to_web: If True, fallback to web_search when internal tools return empty
        
    Returns:
        Dict containing raw results from the tool execution
        Includes 'fallback_used' and 'original_tool' keys when fallback occurs
        
    Raises:
        ValueError: If tool_name is invalid
        RuntimeError: If tool execution fails
    """
    
    valid_tools = ["direct_answer", "vector_search", "graph_search", "web_search"]
    
    if tool_name not in valid_tools:
        raise ValueError(f"Invalid tool '{tool_name}'. Must be one of {valid_tools}")
    
    try:
        if tool_name == "direct_answer":
            # No tool execution needed for direct answers
            return {
                "tool": "direct_answer",
                "results": None,
                "message": "No external data required"
            }
        
        elif tool_name == "vector_search":
            # Execute vector search on Pinecone
            results = pinecone_tool.search(user_question)
            
            # Check if results are empty and web fallback is enabled
            if fallback_to_web and (not results or len(results) == 0):
                # Vector search returned nothing - fallback to web search
                print("Vector search returned no results. Falling back to web search...")
                web_results = web_search_tool.search(user_question)
                return {
                    "tool": "web_search",
                    "results": web_results,
                    "source": "web",
                    "fallback_used": True,
                    "original_tool": "vector_search"
                }
            
            return {
                "tool": "vector_search",
                "results": results,
                "source": "pinecone"
            }
        
        elif tool_name == "graph_search":
            # Execute graph search on Neo4j
            results = neo4j_tool.query(user_question)
            
            # Check if results are empty and fallback is enabled
            if fallback_to_vector and (not results or len(results) == 0):
                # Graph search returned nothing - fallback to vector search
                print("Graph search returned no results. Falling back to vector search...")
                vector_results = pinecone_tool.search(user_question)
                
                # If vector also returns nothing, fallback to web
                if fallback_to_web and (not vector_results or len(vector_results) == 0):
                    print("Vector search also returned no results. Falling back to web search...")
                    web_results = web_search_tool.search(user_question)
                    return {
                        "tool": "web_search",
                        "results": web_results,
                        "source": "web",
                        "fallback_used": True,
                        "original_tool": "graph_search",
                        "fallback_chain": "graph_search -> vector_search -> web_search"
                    }
                
                return {
                    "tool": "vector_search",
                    "results": vector_results,
                    "source": "pinecone",
                    "fallback_used": True,
                    "original_tool": "graph_search"
                }
            
            return {
                "tool": "graph_search",
                "results": results,
                "source": "neo4j"
            }
        
        elif tool_name == "web_search":
            # Execute web search
            results = web_search_tool.search(user_question)
            return {
                "tool": "web_search",
                "results": results,
                "source": "web"
            }
            
    except Exception as e:
        raise RuntimeError(f"Error executing tool '{tool_name}': {e}")


if __name__ == "__main__":
    # Test the executor with different tools
    print("Testing Executor:\n")
    
    test_cases = [
        ("direct_answer", "Hello!"),
        ("vector_search", "What is the vacation policy?"),
        ("graph_search", "Who reports to the CEO?"),
        ("web_search", "Latest AI news"),
    ]
    
    for tool, question in test_cases:
        print(f"Tool: {tool}")
        print(f"Question: {question}")
        try:
            result = execute(tool, question)
            print(f"Result: {result}\n")
        except Exception as e:
            print(f"Error: {e}\n")
