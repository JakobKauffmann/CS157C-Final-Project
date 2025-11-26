from neo4j import GraphDatabase

# ============================================================
# Neo4j Configuration
# ============================================================
NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "neo4juser"     # Change this to your actual password
DB_NAME = "socialnetworkdb"

# Create driver instance
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def run_query(cypher, params=None):
    """
    Execute a Cypher query and return results as a list.
    
    Args:
        cypher: The Cypher query string
        params: Optional dictionary of query parameters
    
    Returns:
        List of Neo4j Record objects
    """
    print("\n=== Cypher ===")
    print(cypher)
    print("Params:", params)
    print("=============\n")
    
    with driver.session(database=DB_NAME) as session:
        return list(session.run(cypher, params or {}))


def run_write_query(cypher, params=None):
    """
    Execute a write Cypher query (CREATE, MERGE, DELETE).
    
    Args:
        cypher: The Cypher query string
        params: Optional dictionary of query parameters
    
    Returns:
        List of Neo4j Record objects
    """
    print("\n=== Write Cypher ===")
    print(cypher)
    print("Params:", params)
    print("====================\n")
    
    with driver.session(database=DB_NAME) as session:
        return list(session.run(cypher, params or {}))


def close_driver():
    """Close the Neo4j driver connection."""
    driver.close()
