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


def render_result_card(result: dict[str, Any], rank: int, *, show_debug: bool) -> None:
    title = html.escape(str(result.get("title", "Untitled paper")))
    url = str(result.get("url", "#"))
    pdf_url = str(result.get("pdf_url", url))

    authors_list = result.get("authors", [])
    if isinstance(authors_list, list):
        authors = ", ".join(str(a) for a in authors_list) if authors_list else "Unknown authors"
    else:
        authors = str(authors_list)

    year = result.get("year", "?")
    venue = html.escape(str(result.get("venue", "Unknown venue")))
    citations = _to_int(result.get("citations", 0), 0)
    score = float(result.get("score", 0.0))
    snippet = str(result.get("snippet", html.escape(str(result.get("abstract", "No abstract available.")))))
    doc_id = html.escape(str(result.get("doc_id", "unknown")))

    chips = f"<span class='chip'>Cited by {citations}</span><span class='chip'>Relevance {score:.2f}</span>"
    if show_debug:
        chips += f"<span class='chip'>ID {doc_id}</span>"

    st.markdown(
        f"""
<div class="result-card">
  <div class="result-title">{rank}. <a href="{html.escape(url)}" target="_blank" rel="noreferrer">{title}</a></div>
  <div class="meta">{html.escape(authors)} — {venue} — {html.escape(str(year))}</div>
  <div class="snippet">{snippet}</div>
  <div style="margin-top:10px;">{chips}</div>
  <div class="link-row">
    <a href="{html.escape(url)}" target="_blank" rel="noreferrer">Related articles</a>
    <a href="{html.escape(pdf_url)}" target="_blank" rel="noreferrer">View PDF</a>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )