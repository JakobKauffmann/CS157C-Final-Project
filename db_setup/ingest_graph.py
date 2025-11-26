import pandas as pd
from neo4j import GraphDatabase

# ============================================================
# Neo4j Config
# ============================================================
NEO4J_URI = "neo4j://127.0.0.1:7687"      # change if needed
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "neoneo21"              # change to your actual password
DB_NAME = "socialnetworkdb"

USERS_CSV = "users.csv"
FOLLOWS_CSV = "follows.csv"

# ============================================================
# Ingestion Class
# ============================================================
class GraphIngestor:

    def __init__(self, uri, user, password, db):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.db = db

    def close(self):
        self.driver.close()

    # ---------------------------------------------------------
    # Check if DB has existing data
    # ---------------------------------------------------------
    def database_has_data(self):
        query = "MATCH (n) RETURN COUNT(n) > 0 AS hasData;"
        with self.driver.session(database=self.db) as session:
            result = session.run(query).single()
            return result["hasData"]

    # ---------------------------------------------------------
    # Clean slate: wipe everything
    # ---------------------------------------------------------
    def wipe_database(self):
        print("[INFO] Cleaning database...")
        query = "MATCH (n) DETACH DELETE n;"
        with self.driver.session(database=self.db) as session:
            session.run(query)
        print("[OK] Database wiped.")

    # ---------------------------------------------------------
    # Create constraints
    # ---------------------------------------------------------
    def create_constraints(self):
        print("[INFO] Creating constraints...")

        constraints = [
            """
            CREATE CONSTRAINT user_id_unique IF NOT EXISTS
            FOR (u:User)
            REQUIRE u.userId IS UNIQUE;
            """,
            """
            CREATE CONSTRAINT username_unique IF NOT EXISTS
            FOR (u:User)
            REQUIRE u.username IS UNIQUE;
            """
        ]

        with self.driver.session(database=self.db) as session:
            for q in constraints:
                session.run(q)

        print("[OK] Constraints ready.")

    # ---------------------------------------------------------
    # Load users into Neo4j
    # ---------------------------------------------------------
    def load_users(self, df, batch_size=200):
        print(f"[INFO] Loading {len(df)} users...")

        with self.driver.session(database=self.db) as session:
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i + batch_size].to_dict("records")
                session.execute_write(self._insert_users_batch, batch)
                print(f"[INFO] Inserted {min(i + batch_size, len(df))} users")

        print("[OK] User import complete.")

    @staticmethod
    def _insert_users_batch(tx, rows):
        query = """
        UNWIND $rows AS row
        MERGE (u:User {userId: row.userId})
        SET u.username = row.username,
            u.email = row.email,
            u.name = row.name,
            u.bio = row.bio,
            u.passwordHash = row.passwordHash;
        """
        tx.run(query, rows=rows)

    # ---------------------------------------------------------
    # Load edges into Neo4j
    # ---------------------------------------------------------
    def load_follows(self, df, batch_size=500):
        print(f"[INFO] Loading {len(df)} follow edges...")

        with self.driver.session(database=self.db) as session:
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i + batch_size].to_dict("records")
                session.execute_write(self._insert_edges_batch, batch)
                print(f"[INFO] Inserted {min(i + batch_size, len(df))} edges")

        print("[OK] Follow edge import complete.")

    @staticmethod
    def _insert_edges_batch(tx, rows):
        query = """
        UNWIND $rows AS row
        MATCH (f:User {userId: row.followerId})
        MATCH (t:User {userId: row.followeeId})
        MERGE (f)-[:FOLLOWS]->(t);
        """
        tx.run(query, rows=rows)

# ============================================================
# Main Executable
# ============================================================
def main():

    users_df = pd.read_csv(USERS_CSV)
    follows_df = pd.read_csv(FOLLOWS_CSV)

    loader = GraphIngestor(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, DB_NAME)

    print("[STEP] Checking existing database state...")
    if loader.database_has_data():
        print("[WARN] Database is not empty. Cleaning up...")
        loader.wipe_database()
    else:
        print("[INFO] Database is already empty. Proceeding...")

    loader.create_constraints()
    loader.load_users(users_df)
    loader.load_follows(follows_df)

    loader.close()
    print("[DONE] All data ingested successfully. Fresh database ready!")

if __name__ == "__main__":
    main()
