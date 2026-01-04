"""
Neo4j Graph Data Ingestion Script

This script populates a Neo4j graph database with organizational and technology relationships.
Models OpenAI's products, leadership, and technology stack.
"""

import os
from neo4j import GraphDatabase


def create_graph_data():
    """
    Create company data model in Neo4j.
    
    Creates Organization, Product, Person, and Technology nodes with their relationships.
    Uses MERGE to ensure idempotency (can be run multiple times safely).
    """
    
    # Read Neo4j credentials from environment
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not uri or not password:
        raise ValueError("NEO4J_URI and NEO4J_PASSWORD environment variables must be set")
    
    print(f"Connecting to Neo4j at {uri}...")
    
    # Initialize Neo4j driver
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    try:
        with driver.session() as session:
            # Create Organization node
            print("\nCreating Organization node...")
            
            session.run("""
                MERGE (o:Organization {name: 'OpenAI'})
                SET o.industry = 'Artificial Intelligence',
                    o.founded = 2015,
                    o.description = 'AI research and deployment company'
            """)
            print("✓ Created/Updated: OpenAI")
            
            # Create Product nodes
            print("\nCreating Product nodes...")
            
            session.run("""
                MERGE (p:Product {name: 'GPT-4'})
                SET p.type = 'Language Model',
                    p.category = 'AI',
                    p.releaseYear = 2023
            """)
            print("✓ Created/Updated: GPT-4")
            
            session.run("""
                MERGE (p:Product {name: 'ChatGPT'})
                SET p.type = 'Conversational AI',
                    p.category = 'AI Application',
                    p.releaseYear = 2022
            """)
            print("✓ Created/Updated: ChatGPT")
            
            # Create Person node
            print("\nCreating Person node...")
            
            session.run("""
                MERGE (p:Person {name: 'Sam Altman'})
                SET p.title = 'CEO',
                    p.role = 'Chief Executive Officer'
            """)
            print("✓ Created/Updated: Sam Altman")
            
            session.run("""
                MERGE (p:Person {name: 'Greg Brockman'})
                SET p.title = 'President',
                    p.role = 'President and Co-Founder'
            """)
            print("✓ Created/Updated: Greg Brockman")
            
            session.run("""
                MERGE (p:Person {name: 'Ilya Sutskever'})
                SET p.title = 'Chief Scientist',
                    p.role = 'Chief Scientist and Co-Founder'
            """)
            print("✓ Created/Updated: Ilya Sutskever")
            
            # Create Technology nodes
            print("\nCreating Technology nodes...")
            
            session.run("""
                MERGE (t:Technology {name: 'Vector Database'})
                SET t.category = 'Database',
                    t.purpose = 'Semantic search and embeddings storage',
                    t.type = 'NoSQL'
            """)
            print("✓ Created/Updated: Vector Database")
            
            session.run("""
                MERGE (t:Technology {name: 'Graph Database'})
                SET t.category = 'Database',
                    t.purpose = 'Relationship and knowledge graph storage',
                    t.type = 'NoSQL'
            """)
            print("✓ Created/Updated: Graph Database")
            
            # Create DEVELOPS relationships
            print("\nCreating DEVELOPS relationships...")
            
            session.run("""
                MATCH (org:Organization {name: 'OpenAI'})
                MATCH (prod:Product {name: 'GPT-4'})
                MERGE (org)-[r:DEVELOPS]->(prod)
                SET r.status = 'active'
            """)
            print("✓ Created: OpenAI DEVELOPS GPT-4")
            
            session.run("""
                MATCH (org:Organization {name: 'OpenAI'})
                MATCH (prod:Product {name: 'ChatGPT'})
                MERGE (org)-[r:DEVELOPS]->(prod)
                SET r.status = 'active'
            """)
            print("✓ Created: OpenAI DEVELOPS ChatGPT")
            
            # Create IS_CEO_OF relationship
            print("\nCreating IS_CEO_OF relationship...")
            
            session.run("""
                MATCH (person:Person {name: 'Sam Altman'})
                MATCH (org:Organization {name: 'OpenAI'})
                MERGE (person)-[r:IS_CEO_OF]->(org)
                SET r.since = '2019'
            """)
            print("✓ Created: Sam Altman IS_CEO_OF OpenAI")
            
            session.run("""
                MATCH (person:Person {name: 'Greg Brockman'})
                MATCH (org:Organization {name: 'OpenAI'})
                MERGE (person)-[r:IS_PRESIDENT_OF]->(org)
                SET r.since = '2015'
            """)
            print("✓ Created: Greg Brockman IS_PRESIDENT_OF OpenAI")
            
            session.run("""
                MATCH (person:Person {name: 'Ilya Sutskever'})
                MATCH (org:Organization {name: 'OpenAI'})
                MERGE (person)-[r:IS_CHIEF_SCIENTIST_AT]->(org)
                SET r.since = '2015'
            """)
            print("✓ Created: Ilya Sutskever IS_CHIEF_SCIENTIST_AT OpenAI")
            
            # Create USES relationships
            print("\nCreating USES relationships...")
            
            session.run("""
                MATCH (org:Organization {name: 'OpenAI'})
                MATCH (tech:Technology {name: 'Vector Database'})
                MERGE (org)-[r:USES]->(tech)
                SET r.purpose = 'Embeddings and semantic search'
            """)
            print("✓ Created: OpenAI USES Vector Database")
            
            session.run("""
                MATCH (org:Organization {name: 'OpenAI'})
                MATCH (tech:Technology {name: 'Graph Database'})
                MERGE (org)-[r:USES]->(tech)
                SET r.purpose = 'Knowledge representation'
            """)
            print("✓ Created: OpenAI USES Graph Database")
            
            # Verify data
            print("\nVerifying data...")
            
            result = session.run("""
                MATCH (o:Organization)
                RETURN count(o) as count
            """)
            print(f"✓ Organization nodes: {result.single()['count']}")
            
            result = session.run("""
                MATCH (p:Product)
                RETURN count(p) as count
            """)
            print(f"✓ Product nodes: {result.single()['count']}")
            
            result = session.run("""
                MATCH (p:Person)
                RETURN count(p) as count
            """)
            print(f"✓ Person nodes: {result.single()['count']}")
            
            result = session.run("""
                MATCH (t:Technology)
                RETURN count(t) as count
            """)
            print(f"✓ Technology nodes: {result.single()['count']}")
            
            result = session.run("""
                MATCH ()-[r:DEVELOPS]->()
                RETURN count(r) as count
            """)
            print(f"✓ DEVELOPS relationships: {result.single()['count']}")
            
            result = session.run("""
                MATCH ()-[r:IS_CEO_OF]->()
                RETURN count(r) as count
            """)
            print(f"✓ IS_CEO_OF relationships: {result.single()['count']}")
            
            result = session.run("""
                MATCH ()-[r:IS_PRESIDENT_OF]->()
                RETURN count(r) as count
            """)
            print(f"✓ IS_PRESIDENT_OF relationships: {result.single()['count']}")
            
            result = session.run("""
                MATCH ()-[r:IS_CHIEF_SCIENTIST_AT]->()
                RETURN count(r) as count
            """)
            print(f"✓ IS_CHIEF_SCIENTIST_AT relationships: {result.single()['count']}")
            
            result = session.run("""
                MATCH ()-[r:USES]->()
                RETURN count(r) as count
            """)
            print(f"✓ USES relationships: {result.single()['count']}")
            
            print("\n✅ Graph data ingestion completed successfully!")
            
    finally:
        driver.close()


def main():
    """Main entry point for the ingestion script."""
    try:
        create_graph_data()
    except Exception as e:
        print(f"\n❌ Error during graph ingestion: {e}")
        raise


if __name__ == "__main__":
    main()
