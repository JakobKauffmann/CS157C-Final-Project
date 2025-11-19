import streamlit as st
import pandas as pd
from db.neo4j_client import run_query
from graph.graph_render import graph_from_rows

def dataframe(rows):
    return pd.DataFrame([r.data() for r in rows]) if rows else pd.DataFrame()

def two_panel_query_ui(title, default_cypher, params=None):
    st.subheader(title)
    st.divider()

    base = title.replace(" ", "_")
    # text_key = base + "_text"
    # editable_key = base + "_editable"
    # reset_key = base + "_reset"
    prefix = "admin_"

    text_key = prefix + base + "_text"
    editable_key = prefix + base + "_editable"
    reset_key = prefix + base + "_reset"

    # init state
    if editable_key not in st.session_state:
        st.session_state[editable_key] = False
    if reset_key not in st.session_state:
        st.session_state[reset_key] = True

    # handle reset before UI renders
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
                    st.dataframe(df, width="stretch")

                with tab2:
                    if df.empty:
                        st.write("No graph results.")
                    else:
                        path = graph_from_rows(rows)
                        with open(path) as f:
                            st.components.v1.html(f.read(), height=600)

            except Exception as e:
                st.error(f"Cypher Error: {e}")
