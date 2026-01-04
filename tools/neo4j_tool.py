"""
Neo4j Graph Search Tool

This tool queries relationship data from Neo4j Aura database.
"""

import os
from typing import List, Dict, Any
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Neo4j driver once at module level
_driver = None


def _get_driver():
    """Get or create the Neo4j driver instance."""
    global _driver
    if _driver is None:
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")
        
        if not uri or not password:
            raise ValueError("NEO4J_URI and NEO4J_PASSWORD environment variables must be set")
        
        _driver = GraphDatabase.driver(uri, auth=(username, password))
    
    return _driver


def query(question: str) -> List[Dict[str, Any]]:
    """
    Query Neo4j graph database for relationship information.
    
    Args:
        question: The question to answer using graph relationships
        
    Returns:
        List of graph query results with person, relationship, and organization info
        
    Raises:
        RuntimeError: If graph query fails
    """
    
    try:
        # Get the driver
        driver = _get_driver()
        
        # Convert question to Cypher query
        cypher_query = _question_to_cypher(question)
        
        # Execute query
        with driver.session() as session:
            result = session.run(cypher_query)
            records = [dict(record) for record in result]
        
        return records
        
    except Exception as e:
        raise RuntimeError(f"Neo4j query failed: {e}")


def _question_to_cypher(question: str) -> str:
    """
    Convert a natural language question to a Cypher query.
    
    Focuses on leadership relationships in the organization.
    
    Args:
        question: Natural language question
        
    Returns:
        Cypher query string
    """
    
    question_lower = question.lower()
    
    # Detect organization name (default to OpenAI if not specified)
    org_name = "OpenAI"
    if "google" in question_lower:
        org_name = "Google"
    elif "microsoft" in question_lower:
        org_name = "Microsoft"
    elif "openai" in question_lower:
        org_name = "OpenAI"
    
    # Specific role queries - match exact relationship types for the organization
    if "ceo" in question_lower:
        return f"""
        MATCH (p:Person)-[:IS_CEO_OF]->(o:Organization {{name: '{org_name}'}})
        RETURN p.name AS name
        """
    
    elif "president" in question_lower:
        return f"""
        MATCH (p:Person)-[:IS_PRESIDENT_OF]->(o:Organization {{name: '{org_name}'}})
        RETURN p.name AS name
        """
    
    elif "chief scientist" in question_lower:
        return f"""
        MATCH (p:Person)-[:IS_CHIEF_SCIENTIST_AT]->(o:Organization {{name: '{org_name}'}})
        RETURN p.name AS name
        """
    
    # Product queries
    elif "product" in question_lower or "develop" in question_lower or "build" in question_lower:
        return f"""
        MATCH (p:Product)-[:BUILT_BY]->(o:Organization {{name: '{org_name}'}})
        RETURN p.name AS name
        """
    
    # Technology queries
    elif "technolog" in question_lower or "uses" in question_lower:
        return f"""
        MATCH (o:Organization {{name: '{org_name}'}})-[:USES]->(t:Technology)
        RETURN t.name AS name
        """
    
    # Default: Return all leadership relationships for the organization
    else:
        return f"""
        MATCH (p:Person)-[r]->(o:Organization {{name: '{org_name}'}})
        WHERE type(r) IN ['IS_CEO_OF', 'IS_PRESIDENT_OF', 'IS_CHIEF_SCIENTIST_AT', 'IS_FOUNDER_OF', 'IS_CTO_OF']
        RETURN p.name AS name, type(r) AS role
        ORDER BY role
        """
