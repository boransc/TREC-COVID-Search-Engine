import html
import streamlit as st
from typing import Any
from utilities.results_normalise import _to_int

def _metric_val(result: dict[str, Any], key: str) -> str:
    value = result.get(key)
    if isinstance(value, (float, int)):
        return f"{float(value):.3f}"
    return "n/a"


def render_advanced_metrics(results: list[dict[str, Any]]) -> None:
    rows = []
    for i, item in enumerate(results, start=1):
        rows.append(
            "".join(
                [
                    f"<tr><td>{i}</td>",
                    f"<td>{html.escape(str(item.get('doc_id', f'doc-{i}')))}</td>",
                    f"<td>{_metric_val(item, 'score')}</td>",
                    f"<td>{_metric_val(item, 'sparse_score')}</td>",
                    f"<td>{_metric_val(item, 'dense_score')}</td>",
                    f"<td>{_metric_val(item, 'temporal_score')}</td>",
                    f"<td>{_metric_val(item, 'mmr_score')}</td>",
                    "</tr>",
                ]
            )
        )

    st.markdown(
        """
<table class="metrics-table">
  <thead>
    <tr>
      <th>Rank</th>
      <th>Doc ID</th>
      <th>Final</th>
      <th>Sparse</th>
      <th>Dense</th>
      <th>Temporal</th>
      <th>MMR</th>
    </tr>
  </thead>
  <tbody>
"""
        + "".join(rows)
        + """
  </tbody>
</table>
""",
        unsafe_allow_html=True,
    )


def render_result_card(result: dict, rank: int) -> None:
    import html
    import streamlit as st

    title = html.escape(str(result.get("title", "Untitled paper")))
    url = str(result.get("url", "#"))

    venue = html.escape(str(result.get("venue", "Unknown venue")))
    year = result.get("year", "?")
    score = float(result.get("score", 0.0))

    # ONLY metadata fields (as you wanted)
    metadata_fields = [
        "_id",
        "doi",
        "journal",
        "pmcid",
        "publish_time",
        "publish_year",
        "pubmed_id",
        "source_x",
        "title",
        "url",
    ]

    with st.container():

        # --- CARD ---
        st.markdown(f"""
<div class="result-card">
  <div class="result-title">
    {rank}. <a href="{html.escape(url)}" target="_blank">{title}</a>
  </div>
  <div class="meta">{venue} — {year}</div>
  <div style="margin-top:8px;">Relevance {score:.2f}</div>
</div>
""", unsafe_allow_html=True)

        # --- EXPANDER (visually inside card) ---
        with st.expander("Show more"):

            for field in metadata_fields:
                value = result.get(field)

                if value not in (None, "", []):
                    st.markdown(
                        f"**{field}:** {html.escape(str(value))}"
                    )