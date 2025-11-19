from neo4j import GraphDatabase

NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "neo4juser"     # change this
DB_NAME = "socialnetworkdb"

class DBCleanup:
    def __init__(self, uri, user, password, db):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.db = db

    def close(self):
        self.driver.close()

    def wipe_database(self):
        query = """
        MATCH (n)
        DETACH DELETE n;
        """
        with self.driver.session(database=self.db) as session:
            session.run(query)
        print("[OK] All nodes and relationships deleted from the database.")

if __name__ == "__main__":
    cleaner = DBCleanup(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, DB_NAME)
    cleaner.wipe_database()
    cleaner.close()
