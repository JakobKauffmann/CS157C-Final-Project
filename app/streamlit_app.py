import streamlit as st
from ui.sidebar import render_sidebar
from ui.user_view import render_user_view
from ui.admin_view import render_admin_view

st.set_page_config(page_title="Social Graph System", layout="wide")

mode = render_sidebar()

st.title("Social Network — Neo4j System")
st.divider()

if mode == "Admin":
    render_admin_view()

elif mode == "User":
    user = st.session_state.logged_in_user
    if not user:
        st.warning("Please login from the sidebar.")
    else:
        render_user_view(user)
