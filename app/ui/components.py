import streamlit as st
import pandas as pd
from db.neo4j_client import run_query
from graph.graph_render import graph_from_rows

def dataframe(rows):
    """Convert Neo4j result rows to a pandas DataFrame."""
    return pd.DataFrame([r.data() for r in rows]) if rows else pd.DataFrame()


def two_panel_query_ui(title, default_cypher, params=None):
    """
    Reusable two-panel query UI component.
    Left panel: Cypher query editor with Edit/Reset/Run buttons
    Right panel: Output table and graph visualization
    """
    st.subheader(title)
    st.divider()

    base = title.replace(" ", "_").replace(":", "").replace("-", "_")
    prefix = "admin_"

    text_key = prefix + base + "_text"
    editable_key = prefix + base + "_editable"
    reset_key = prefix + base + "_reset"

    # Initialize state
    if editable_key not in st.session_state:
        st.session_state[editable_key] = False
    if reset_key not in st.session_state:
        st.session_state[reset_key] = True

    # Handle reset before UI renders
    if st.session_state[reset_key]:
        st.session_state[text_key] = default_cypher
        st.session_state[reset_key] = False

    left, right = st.columns([1, 2])

    with left:
        st.write("### Cypher Query")
        disabled = not st.session_state[editable_key]

        st.text_area("Query Editor", key=text_key, height=300, disabled=disabled)

        c1, c2, c3 = st.columns(3)

        if c1.button("Edit", key=base+"_edit"):
            st.session_state[editable_key] = True

        if c2.button("Reset", key=base+"_reset_btn"):
            st.session_state[editable_key] = False
            st.session_state[reset_key] = True
            st.rerun()

        run_pressed = c3.button("Run", key=base+"_run")

    with right:
        st.write("### Output")

        if run_pressed:
            try:
                cypher = st.session_state[text_key]
                rows = run_query(cypher, params)
                df = dataframe(rows)

                tab1, tab2 = st.tabs(["Table", "Graph"])

                with tab1:
                    if df.empty:
                        st.info("No results returned.")
                    else:
                        st.dataframe(df, use_container_width=True)

                with tab2:
                    if df.empty:
                        st.write("No graph results.")
                    else:
                        path = graph_from_rows(rows)
                        with open(path) as f:
                            st.components.v1.html(f.read(), height=600)

            except Exception as e:
                st.error(f"Cypher Error: {e}")


def user_selector(key_prefix, label="Select User"):
    """
    Reusable user selector dropdown component.
    Returns the selected user dict or None.
    """
    users = run_query("""
        MATCH (u:User)
        RETURN u.userId AS id, u.username AS username
        ORDER BY u.username
        LIMIT 500
    """)
    
    user_list = [""] + [f"{r.data()['username']} ({r.data()['id']})" for r in users]
    user_map = {f"{r.data()['username']} ({r.data()['id']})": r.data() for r in users}
    
    selected = st.selectbox(label, user_list, key=f"{key_prefix}_selector")
    
    if selected and selected in user_map:
        return user_map[selected]
    return None


def success_message(msg):
    """Display a success message with emoji."""
    st.success(f"✅ {msg}")


def warning_message(msg):
    """Display a warning message with emoji."""
    st.warning(f"⚠️ {msg}")


def error_message(msg):
    """Display an error message with emoji."""
    st.error(f"❌ {msg}")
