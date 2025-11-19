import streamlit as st
from db.neo4j_client import run_query
import bcrypt

def render_sidebar():
    st.sidebar.title("Mode")

    mode = st.sidebar.radio("View as", ["Admin", "User"])

    if "logged_in_user" not in st.session_state:
        st.session_state.logged_in_user = None

    if mode == "User":
        st.sidebar.subheader("Login")

        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")

        if st.sidebar.button("Login"):
            rows = run_query("""
                MATCH (u:User {username: $u})
                RETURN u.userId AS id, u.username AS username, 
                       u.passwordHash AS phash,
                       u.name AS name, u.bio AS bio
            """, {"u": username})

            if not rows:
                st.sidebar.error("User not found.")
            else:
                data = rows[0].data()
                if bcrypt.checkpw(password.encode(), data["phash"].encode()):
                    st.session_state.logged_in_user = data
                    st.sidebar.success("Logged in")
                else:
                    st.sidebar.error("Invalid password")

        if st.sidebar.button("Logout"):
            st.session_state.logged_in_user = None

    return mode
