import re
from typing import Any
from utilities.text_utils import build_snippet


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if isinstance(value, bool):
            return default
        if isinstance(value, (int, float)):
            return int(value)
        s = str(value).strip()
        return int(float(s)) if s else default
    except Exception:
        return default

def _clean_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return ", ".join(str(x) for x in value if x not in (None, ""))
    return str(value)

def _pick(item: dict[str, Any], keys: list[str], default: Any = "") -> Any:
    for k in keys:
        if k in item and item[k] not in (None, ""):
            return item[k]
    return default


def _year_from_publish_time(publish_time: str) -> int:
    m = re.match(r"^(\\d{4})", (publish_time or "").strip())
    return int(m.group(1)) if m else 0

import re

def clean_url(raw_url: str, title: str) -> str:
    if not raw_url:
        return f"https://scholar.google.com/scholar?q={title.replace(' ', '+')}"

    # Split on common separators
    parts = re.split(r"[;\s]+", raw_url)

    for part in parts:
        part = part.strip()

        # If it's a DOI
        if part.startswith("10."):
            return f"https://doi.org/{part}"

        # If it's already a valid URL
        if part.startswith("http"):
            return part

    # fallback
    return f"https://scholar.google.com/scholar?q={title.replace(' ', '+')}"

def normalize_result(item: dict[str, Any], query_terms: list[str]) -> dict[str, Any]:
    title = _clean_str(_pick(item, ["title", "paper_title", "document_title"], "Untitled paper"))
    abstract = _clean_str(_pick(item, ["abstract", "summary", "text"], ""))
    publish_time = _clean_str(_pick(item, ["publish_time", "published", "date"], ""))
    year = _to_int(_pick(item, ["year", "publish_year"], 0), 0)
    if not year and publish_time:
        year = _year_from_publish_time(publish_time)
    venue = _clean_str(_pick(item, ["venue", "journal", "source"], "Unknown venue"))

    authors = _pick(item, ["authors", "author"], [])
    if not isinstance(authors, list):
        authors = [a.strip() for a in str(authors).split(",") if a.strip()]

    citations = _to_int(_pick(item, ["citations", "cited_by", "citation_count"], 0), 0)
    score = float(item.get("score", 0.0)) if isinstance(item.get("score", 0.0), (int, float, str)) else 0.0

    url = clean_url(
        _clean_str(_pick(item, ["url", "doi", "link"], "")),
        title
    )
    if url.startswith("10."):
        url = f"https://doi.org/{url}"
    pdf_url = _clean_str(_pick(item, ["pdf_url", "pdf", "pdfUrl"], url))

    doc_id = _clean_str(_pick(item, ["doc_id", "id"], "unknown"))
    snippet = build_snippet(abstract if abstract else title, query_terms)

    return {
        "doc_id": doc_id,
        "title": title,
        "authors": authors,
        "year": year,
        "venue": venue,
        "abstract": abstract or "No abstract available.",
        "citations": citations,
        "url": url or "#",
        "pdf_url": pdf_url or (url or "#"),
        "score": float(score),
        "snippet": snippet,
        **{k: v for k, v in item.items() if k in ("sparse_score", "dense_score", "temporal_score", "mmr_score")},
    }