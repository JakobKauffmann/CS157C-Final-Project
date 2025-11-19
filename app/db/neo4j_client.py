from neo4j import GraphDatabase

NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "neo4juser"
DB_NAME = "socialnetworkdb"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def run_query(cypher, params=None):
    print("\n=== Cypher ===")
    print(cypher)
    print("Params:", params)
    print("=============\n")
    
    with driver.session(database=DB_NAME) as session:
        return list(session.run(cypher, params or {}))
