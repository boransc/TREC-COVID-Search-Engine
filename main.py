from __future__ import annotations

import time
import html
import streamlit as st

from render.render import render_advanced_metrics, render_result_card
from services.search import search_all_modes
from theme.theme import inject_theme


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
PINECONE_INDEXES = ["trec-covid", "trec-covid-b5"]
st.session_state.setdefault("pinecone_index", PINECONE_INDEXES[0])

# ─────────────────────────────────────────────
# PAGE SETUP
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="TREC-COVID Scholar Search",
    page_icon="📚",
    layout="wide",
)

st.session_state.setdefault("theme_choice", "Light")
inject_theme(st.session_state.theme_choice)


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown(
    """
    <div class="hero">
        <h2 style="margin:0;">TREC-COVID Scholar Search</h2>
    </div>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────
# SEARCH BAR
# ─────────────────────────────────────────────
with st.form("search_form", clear_on_submit=False):
    query = st.text_input(
        label="Search papers",
        placeholder='Try: "long covid cognitive symptoms"',
        label_visibility="visible"
    )
    search_clicked = st.form_submit_button("Search")


# ─────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")

    # retrieval_mode = st.selectbox(
    #     "Retrieval Method",
    #     [
    #         "B5 (Projection)",
    #         "Hybrid (RRF + MMR)",
    #     ]
    # )

    # sort_by = st.selectbox("Sort by", ["Relevance", "Date", "Citations"])

    pinecone_index = st.selectbox(
        "Pinecone Index",
        PINECONE_INDEXES,
        key="pinecone_index",
    )
    top_k = st.slider("Results", 5, 30, 10)

    # min_citations = st.slider("Minimum citations", 0, 500, 0, step=10)

    # st.divider()
    st.subheader("Appearance")
    st.radio("Theme", ["Light", "Dark"], key="theme_choice")
    # show_debug = st.toggle("Show debug info")
    # advanced_view = st.toggle("Advanced metrics")


inject_theme(st.session_state.theme_choice)


# ─────────────────────────────────────────────
# SEARCH EXECUTION
# ─────────────────────────────────────────────
if search_clicked and query.strip():

    start = time.perf_counter()

    with st.spinner("Retrieving papers please wait..."):
        results_by_mode, err = search_all_modes(
            query=query,
            top_k=top_k,
            min_citations=0,
            pinecone_api_key=st.secrets.get("PINECONE_API_KEY", ""),
            pinecone_index=st.session_state.pinecone_index,
            pinecone_namespace="",
        )
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    # ─────────────────────────────────────────
    # ERROR HANDLING
    # ─────────────────────────────────────────
    if err:
        st.error(f"Search failed: {err}")

    elif not results_by_mode:
        st.warning("No results found. Try a broader query.")

    else:
        st.markdown(
            f"<h3>Results for: <span style='color: var(--accent);'>{html.escape(query)}</span></h3>",
            unsafe_allow_html=True
        )

        st.markdown(f"**{elapsed_ms/1000:.2f}s total latency**")


        # Create tabs for each retrieval system
        tabs = st.tabs(list(results_by_mode.keys()))

        for tab, (mode, results) in zip(tabs, results_by_mode.items()):
            with tab:
                st.markdown(f"## {mode}")

                if not results:
                    st.warning("No results found for this method.")
                    continue

                for idx, paper in enumerate(results, start=1):
                    render_result_card(
                        paper,
                        idx,
                    )

        # ─────────────────────────────────────
        # ADVANCED METRICS
        # ─────────────────────────────────────
        # if advanced_view:
        #     with st.expander("Advanced comparison"):
        #         render_advanced_metrics(results_by_mode)


# ─────────────────────────────────────────────
# EMPTY STATE
# ─────────────────────────────────────────────
elif not query:
    st.info("Enter a query to start searching papers.")