import streamlit as st
from ui.components import two_panel_query_ui
from db.neo4j_client import run_query


def render_admin_view():

    st.header("Admin Dashboard")
    st.divider()

    # ======================================================
    # UC 1–6 placeholders
    # ======================================================
    for i in range(1, 7):
        st.subheader(f"UC-{i}: Placeholder")
        st.info("Team member implementation here.")
        st.divider()

    # ======================================================
    # TODO: UC-7: View User Connections -> THIS HAS BUGS
    # ======================================================
    st.subheader("UC-7: View User Connections")
    st.write("Select a user to view their followers and following lists.")

    # Load all users for dropdown
    users = run_query("""
        MATCH (u:User)
        RETURN u.userId AS id, u.username AS username
        ORDER BY username
    """)

    user_map = {f"{row['username']} ({row['id']})": row["id"] for row in (r.data() for r in users)}
    selected_label = st.selectbox("Select User", list(user_map.keys()))

    # Placeholder template queries shown to admin
    default_followers_query = """
    MATCH (u:User {userId: '<SELECT_USER_ID>', username: '<SELECT_USERNAME>'})<-[:FOLLOWS]-(f)
    RETURN 
        f.userId AS id,
        f.username AS username,
        f.name AS name,
        f.bio AS bio
    ORDER BY username
    """

    default_following_query = """
    MATCH (u:User {userId: '<SELECT_USER_ID>', username: '<SELECT_USERNAME>'})-[:FOLLOWS]->(t)
    RETURN 
        t.userId AS id,
        t.username AS username,
        t.name AS name,
        t.bio AS bio
    ORDER BY username
    """

    if selected_label:
        uid = user_map[selected_label]

        # Extract username from "Username (ID)"
        username = selected_label.split(" (")[0]

        st.write(f"### Viewing Connections for: **{username} ({uid})**")
        st.divider()

        # Followers
        rendered_followers_query = (
            default_followers_query
            .replace("<SELECT_USER_ID>", str(uid))
            .replace("<SELECT_USERNAME>", username)
        )

        two_panel_query_ui(
            f"UC-7 Followers of {username} ({uid})",
            rendered_followers_query
        )

        st.divider()

        # Following
        rendered_following_query = (
            default_following_query
            .replace("<SELECT_USER_ID>", str(uid))
            .replace("<SELECT_USERNAME>", username)
        )

        two_panel_query_ui(
            f"UC-7 Following of {username} ({uid})",
            rendered_following_query
        )

        st.divider()


    # ======================================================
    # UC-8 and UC-9 placeholders
    # ======================================================
    for i in range(8, 10):
        st.subheader(f"UC-{i}: Placeholder")
        st.info("Team member implementation here.")
        st.divider()

    # ======================================================
    # UC-10 Search Users
    # ======================================================
    q = st.text_input("Search Term")
    uc10 = """
    MATCH (u:User)
    WHERE toLower(u.username) CONTAINS toLower($q)
       OR toLower(u.name) CONTAINS toLower($q)
    RETURN u.userId AS id, u.username, u.name, u.bio
    LIMIT 50
    """
    two_panel_query_ui("UC-10: Search Users", uc10, params={"q": q})

    # ======================================================
    # UC-11 Popular Users
    # ======================================================
    uc11 = """
    MATCH (u:User)
    OPTIONAL MATCH (u)<-[:FOLLOWS]-(f)
    WITH u, count(f) AS followerCount
    RETURN u.userId AS id, u.username AS username, u.name AS name, followerCount
    ORDER BY followerCount DESC
    LIMIT 20
    """
    two_panel_query_ui("UC-11: Popular Users", uc11)
