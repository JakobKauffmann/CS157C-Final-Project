import streamlit as st
from db.neo4j_client import run_query
from graph.graph_render import graph_from_rows, mutual_graph, recommendation_graph
from ui.components import dataframe


def render_user_view(user):
    """
    Render the user view with profile and social graph features.
    Includes Jakob's UC-5 through UC-9 implementations.
    """
    # Profile Header
    st.header(f"👤 {user['username']}")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.write(f"**Name:** {user['name']}")
        st.write(f"**Bio:** {user['bio']}")

    with col2:
        counts = run_query("""
            MATCH (u:User {userId: $id})
            RETURN
                SIZE([(u)-[:FOLLOWS]->(t) | t]) AS following,
                SIZE([(f)-[:FOLLOWS]->(u) | f]) AS followers
        """, {"id": user["id"]})[0].data()

        st.metric("Followers", counts['followers'])
        st.metric("Following", counts['following'])

    st.divider()

    # Tabs for all features
    tabs = st.tabs([
        "👥 My Connections",
        "➕ Follow Users",
        "➖ Unfollow",
        "🤝 Mutual Friends",
        "💡 Recommendations"
    ])

    # Tab 0: My Connections (UC-7)
    with tabs[0]:
        render_my_connections(user)

    # Tab 1: Follow Users (UC-5)
    with tabs[1]:
        render_follow_user(user)

    # Tab 2: Unfollow (UC-6)
    with tabs[2]:
        render_unfollow_user(user)

    # Tab 3: Mutual Friends (UC-8)
    with tabs[3]:
        render_mutual_friends(user)

    # Tab 4: Recommendations (UC-9)
    with tabs[4]:
        render_recommendations(user)


# ==============================================================================
# UC-7: My Connections
# ==============================================================================
def render_my_connections(user):
    st.subheader("My Connections")

    sub_tabs = st.tabs(["👥 Followers", "➡️ Following"])

    with sub_tabs[0]:
        st.write("**People who follow you:**")
        rows = run_query("""
            MATCH (u:User {userId: $id})<-[:FOLLOWS]-(f)
            RETURN f.userId AS id, f.username AS username, f.name AS name, f.bio AS bio
            ORDER BY f.username LIMIT 100
        """, {"id": user["id"]})

        df = dataframe(rows)
        if df.empty:
            st.info("No followers yet.")
        else:
            st.dataframe(df, use_container_width=True)
            if st.checkbox("Show Graph", key="my_followers_graph"):
                path = graph_from_rows(rows)
                with open(path) as f:
                    st.components.v1.html(f.read(), height=500)

    with sub_tabs[1]:
        st.write("**People you follow:**")
        rows = run_query("""
            MATCH (u:User {userId: $id})-[:FOLLOWS]->(t)
            RETURN t.userId AS id, t.username AS username, t.name AS name, t.bio AS bio
            ORDER BY t.username LIMIT 100
        """, {"id": user["id"]})

        df = dataframe(rows)
        if df.empty:
            st.info("Not following anyone yet.")
        else:
            st.dataframe(df, use_container_width=True)
            if st.checkbox("Show Graph", key="my_following_graph"):
                path = graph_from_rows(rows)
                with open(path) as f:
                    st.components.v1.html(f.read(), height=500)


# ==============================================================================
# UC-5: Follow Users
# ==============================================================================
def render_follow_user(user):
    st.subheader("Follow a User")
    st.write("Search for users to follow.")

    search = st.text_input("Search by username or name", key="follow_search")

    if search:
        results = run_query("""
            MATCH (target:User)
            WHERE (toLower(target.username) CONTAINS toLower($q)
               OR toLower(target.name) CONTAINS toLower($q))
              AND target.userId <> $myId
              AND NOT EXISTS { MATCH (me:User {userId: $myId})-[:FOLLOWS]->(target) }
            RETURN target.userId AS id, target.username AS username,
                   target.name AS name, target.bio AS bio
            ORDER BY target.username LIMIT 20
        """, {"q": search, "myId": user["id"]})

        if not results:
            st.info("No users found matching your search (or you already follow them).")
        else:
            st.write(f"**Found {len(results)} user(s):**")
            for r in results:
                data = r.data()
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{data['username']}** - {data['name']}")
                    if data['bio']:
                        st.caption(data['bio'][:100])
                with col2:
                    if st.button("Follow", key=f"follow_{data['id']}"):
                        run_query("""
                            MATCH (me:User {userId: $myId}), (target:User {userId: $tid})
                            MERGE (me)-[:FOLLOWS]->(target)
                        """, {"myId": user["id"], "tid": data["id"]})
                        st.success(f"✅ Now following {data['username']}!")
                        st.rerun()
    else:
        st.info("Enter a search term above to find users to follow.")


# ==============================================================================
# UC-6: Unfollow Users
# ==============================================================================
def render_unfollow_user(user):
    st.subheader("Unfollow a User")

    following = run_query("""
        MATCH (u:User {userId: $id})-[:FOLLOWS]->(t)
        RETURN t.userId AS id, t.username AS username, t.name AS name
        ORDER BY t.username
    """, {"id": user["id"]})

    if not following:
        st.info("You're not following anyone.")
    else:
        options = [f"{r.data()['username']} ({r.data()['id']})" for r in following]
        opt_map = {f"{r.data()['username']} ({r.data()['id']})": r.data() for r in following}

        selected = st.selectbox("Select user to unfollow", options, key="unfollow_select")

        if selected:
            target = opt_map[selected]
            st.write(f"**Username:** {target['username']}")
            st.write(f"**Name:** {target['name']}")

            if st.button("🚫 Unfollow", key="confirm_unfollow"):
                run_query("""
                    MATCH (me:User {userId: $myId})-[r:FOLLOWS]->(t:User {userId: $tid})
                    DELETE r
                """, {"myId": user["id"], "tid": target["id"]})
                st.success(f"✅ Unfollowed {target['username']}")
                st.rerun()


# ==============================================================================
# UC-8: Mutual Friends
# ==============================================================================
def render_mutual_friends(user):
    st.subheader("Mutual Friends")
    st.write("Find users that you and another person both follow.")

    following = run_query("""
        MATCH (u:User {userId: $id})-[:FOLLOWS]->(t)
        RETURN t.userId AS id, t.username AS username
        ORDER BY t.username
    """, {"id": user["id"]})

    if not following:
        st.info("Follow some users first to find mutual connections.")
        return

    options = [f"{r.data()['username']} ({r.data()['id']})" for r in following]
    opt_map = {f"{r.data()['username']} ({r.data()['id']})": r.data() for r in following}

    selected = st.selectbox("Select a friend to compare with", options, key="mutual_select")

    if selected and st.button("Find Mutual Friends", key="find_mutual"):
        other = opt_map[selected]

        rows = run_query("""
            MATCH (me:User {userId: $myId})-[:FOLLOWS]->(mutual:User)<-[:FOLLOWS]-(other:User {userId: $otherId})
            RETURN DISTINCT mutual.userId AS id, mutual.username AS username,
                   mutual.name AS name, mutual.bio AS bio
            ORDER BY mutual.username LIMIT 50
        """, {"myId": user["id"], "otherId": other["id"]})

        df = dataframe(rows)
        st.write(f"**{len(df)} mutual connection(s) with {other['username']}**")

        if df.empty:
            st.info("No mutual connections found.")
        else:
            tab1, tab2 = st.tabs(["📊 List", "🔗 Graph"])
            with tab1:
                st.dataframe(df, use_container_width=True)
            with tab2:
                me_data = {"id": user["id"], "username": user["username"]}
                path = mutual_graph(rows, me_data, other)
                with open(path) as f:
                    st.components.v1.html(f.read(), height=500)
                st.caption("🔴 You | 🟢 Friend | 🔵 Mutual Connections")


# ==============================================================================
# UC-9: Recommendations
# ==============================================================================
def render_recommendations(user):
    st.subheader("Friend Recommendations")
    st.write("People you might want to follow based on mutual connections.")

    limit = st.slider("Number of recommendations", 5, 30, 10, key="rec_limit")

    if st.button("🔍 Get Recommendations", key="get_recs"):
        rows = run_query("""
            MATCH (me:User {userId: $myId})-[:FOLLOWS]->(friend)-[:FOLLOWS]->(rec)
            WHERE NOT (me)-[:FOLLOWS]->(rec) AND me <> rec
            WITH rec, count(DISTINCT friend) AS mutualCount
            RETURN rec.userId AS id, rec.username AS username,
                   rec.name AS name, rec.bio AS bio, mutualCount
            ORDER BY mutualCount DESC LIMIT $limit
        """, {"myId": user["id"], "limit": limit})

        df = dataframe(rows)

        if df.empty:
            st.info("No recommendations found. Try following more users first!")
        else:
            st.write(f"**Found {len(df)} recommendation(s):**")

            tab1, tab2 = st.tabs(["📊 List", "🔗 Graph"])

            with tab1:
                for r in rows:
                    data = r.data()
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{data['username']}** ({data['mutualCount']} mutual)")
                        if data.get('name'):
                            st.caption(data['name'])
                    with col2:
                        if st.button("Follow", key=f"rec_{data['id']}"):
                            run_query("""
                                MATCH (me:User {userId: $myId}), (t:User {userId: $tid})
                                MERGE (me)-[:FOLLOWS]->(t)
                            """, {"myId": user["id"], "tid": data["id"]})
                            st.success(f"✅ Following {data['username']}!")
                            st.rerun()

            with tab2:
                me_data = {"id": user["id"], "username": user["username"]}
                path = recommendation_graph(rows, me_data)
                with open(path) as f:
                    st.components.v1.html(f.read(), height=500)
                st.caption("🔴 You | 🟡 Recommended (size = mutual count)")