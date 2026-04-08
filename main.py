from __future__ import annotations

import time
import html
import streamlit as st

from render.render import render_advanced_metrics, render_result_card
from services.search import search
from theme.theme import inject_theme


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
PINECONE_INDEX = "trec-covid"


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
        <div class="meta">Hybrid dense + sparse retrieval with projection fusion (B5)</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────
# SEARCH BAR
# ─────────────────────────────────────────────
query = st.text_input(
    label="Search papers",
    placeholder='Try: "long covid cognitive symptoms"',
    label_visibility="visible"
)
search_clicked = st.button("Search")


# ─────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")

    retrieval_mode = st.selectbox(
        "Retrieval Method",
        [
            "B5 (Projection)",
            "Hybrid (RRF + MMR)",
        ]
    )

    sort_by = st.selectbox("Sort by", ["Relevance", "Date", "Citations"])
    top_k = st.slider("Results", 5, 30, 10)

    year_from, year_to = st.slider("Year range", 2019, 2026, (2020, 2025))

    min_citations = st.slider("Minimum citations", 0, 500, 0, step=10)

    st.divider()
    st.subheader("Appearance")
    st.radio("Theme", ["Light", "Dark"], key="theme_choice")
    show_debug = st.toggle("Show debug info")
    advanced_view = st.toggle("Advanced metrics")


inject_theme(st.session_state.theme_choice)


# ─────────────────────────────────────────────
# SEARCH EXECUTION
# ─────────────────────────────────────────────
if search_clicked and query.strip():

    start = time.perf_counter()

    with st.spinner("Retrieving papers using hybrid search..."):
        results, err = search(
            query=query,
            mode=retrieval_mode,
            top_k=top_k,
            year_from=year_from,
            year_to=year_to,
            min_citations=min_citations,
            sort_by=sort_by,
            pinecone_api_key=st.secrets.get("PINECONE_API_KEY", ""),
            pinecone_namespace="",
        )
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    # ─────────────────────────────────────────
    # ERROR HANDLING
    # ─────────────────────────────────────────
    if err:
        st.error(f"Search failed: {err}")

    elif not results:
        st.warning("No results found. Try a broader query.")

    else:
        st.markdown(
            f"<h3>Results for: <span style='color: var(--accent);'>{html.escape(query)}</span></h3>",
            unsafe_allow_html=True
        )

        st.markdown(
            f"**{len(results)} papers found** • {elapsed_ms/1000:.2f}s"
        )

        # ─────────────────────────────────────
        # RESULTS
        # ─────────────────────────────────────
        for idx, paper in enumerate(results, start=1):
            render_result_card(
                paper,
                idx,
                show_debug=show_debug,
            )

        # ─────────────────────────────────────
        # ADVANCED METRICS
        # ─────────────────────────────────────
        if advanced_view:
            with st.expander("Advanced comparison"):
                render_advanced_metrics(results)


# ─────────────────────────────────────────────
# EMPTY STATE
# ─────────────────────────────────────────────
elif not query:
    st.info("Enter a query to start searching papers.")