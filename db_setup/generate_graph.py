import pandas as pd
import random

SEED = 42
random.seed(SEED)

NUM_CLUSTERS = 20
TOP_INFLUENCERS = 20
INFLUENCER_MIN = 1000
INFLUENCER_MAX = 3500
GHOST_ACCOUNTS = 800
NORMAL_MIN = 3
NORMAL_MAX = 50
CROSS_CLUSTER_PROB = 0.005

def generate_graph():
    users_df = pd.read_csv("users.csv")
    user_ids = users_df["userId"].tolist()
    num_users = len(user_ids)

    print(f"[INFO] Loaded {num_users} users.")

    # -----------------------------------------------
    # Create deterministic clusters
    # -----------------------------------------------
    clusters = {}
    cluster_size = num_users // NUM_CLUSTERS

    for cid in range(NUM_CLUSTERS):
        start = cid * cluster_size
        end = start + cluster_size if cid < NUM_CLUSTERS - 1 else num_users
        clusters[cid] = user_ids[start:end]

    # -----------------------------------------------
    # Pick influencers + ghosts deterministically
    # -----------------------------------------------
    influencers = random.sample(user_ids, TOP_INFLUENCERS)
    remaining = [u for u in user_ids if u not in influencers]
    ghosts = set(random.sample(remaining, GHOST_ACCOUNTS))

    print(f"[INFO] Influencers: {influencers}")
    print(f"[INFO] Ghost accounts: {len(ghosts)}")

    edges = set()

    # map user → cluster
    user_to_cluster = {}
    for cid, members in clusters.items():
        for u in members:
            user_to_cluster[u] = cid

    # -----------------------------------------------
    # Influencer edges
    # -----------------------------------------------
    for inf in influencers:
        count = random.randint(INFLUENCER_MIN, INFLUENCER_MAX)
        possible = [u for u in user_ids if u != inf and u not in ghosts]
        followers = random.sample(possible, count)
        for f in followers:
            edges.add((f, inf))

    # -----------------------------------------------
    # Normal users
    # -----------------------------------------------
    for idx, user in enumerate(user_ids, start=1):
        if user in ghosts or user in influencers:
            continue

        cluster_id = user_to_cluster[user]
        cluster_members = clusters[cluster_id]

        num_follows = random.randint(NORMAL_MIN, NORMAL_MAX)
        followees = set()

        while len(followees) < num_follows:
            if random.random() < CROSS_CLUSTER_PROB:
                other = random.choice([c for c in clusters.keys() if c != cluster_id])
                target = random.choice(clusters[other])
            else:
                target = random.choice(cluster_members)

            if target != user:
                followees.add(target)

        for t in followees:
            edges.add((user, t))

        if idx % 100 == 0:
            print(f"[INFO] Processed {idx} users. Edges: {len(edges)}")

    pd.DataFrame(list(edges), columns=["followerId", "followeeId"]).to_csv("follows.csv", index=False)

    print(f"[OK] Generated follows.csv with {len(edges)} edges.")

if __name__ == "__main__":
    generate_graph()
