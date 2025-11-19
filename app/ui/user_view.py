import streamlit as st
from db.neo4j_client import run_query
from graph.graph_render import graph_from_rows
from ui.components import dataframe

def render_user_view(user):
    st.header(f"Profile — {user['username']}")
    st.write(f"**Name:** {user['name']}")
    st.write(f"**Bio:** {user['bio']}")

    # counts = run_query("""
    #     MATCH (u:User {userId: $id})
    #     RETURN SIZE((u)-[:FOLLOWS]->()) AS following,
    #            SIZE((u)<-[:FOLLOWS]-()) AS followers
    # """, {"id": user["id"]})[0].data()
    counts = run_query("""
        MATCH (u:User {userId: $id})
        RETURN 
            SIZE([(u)-[:FOLLOWS]->(t) | t]) AS following,
            SIZE([(f)-[:FOLLOWS]->(u) | f]) AS followers
    """, {"id": user["id"]})[0].data()

    st.write(f"Followers: {counts['followers']}  |  Following: {counts['following']}")
    st.divider()

    tabs = st.tabs(["Followers", "Following"])

    with tabs[0]:
        rows = run_query("""
            MATCH (u:User {userId: $id})<-[:FOLLOWS]-(f)
            RETURN f.userId AS id, f.username AS username, f.name AS name
        """, {"id": user["id"]})
        df = dataframe(rows)
        st.dataframe(df, use_container_width=True)

        if df.size:
            path = graph_from_rows(rows)
            with open(path) as f:
                st.components.v1.html(f.read(), height=500)

    with tabs[1]:
        rows = run_query("""
            MATCH (u:User {userId: $id})-[:FOLLOWS]->(t)
            RETURN t.userId AS id, t.username AS username, t.name AS name
        """, {"id": user["id"]})
        df = dataframe(rows)
        st.dataframe(df, use_container_width=True)

        if df.size:
            path = graph_from_rows(rows)
            with open(path) as f:
                st.components.v1.html(f.read(), height=500)
