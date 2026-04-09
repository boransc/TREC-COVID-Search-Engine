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

def clean_url(raw_url: str, title: str, doi: str | None = None) -> str:
    # PRIORITY 1 → DOI
    if doi:
        doi = str(doi).strip()
        if doi.startswith("10."):
            return f"https://doi.org/{doi}"

    if raw_url:
        parts = re.split(r"[;\s]+", raw_url)

        for part in parts:
            part = part.strip()

            if part.startswith("https://doi.org"):
                return part

            if part.startswith("http"):
                return part

            if part.startswith("10."):
                return f"https://doi.org/{part}"

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

    score = float(item.get("score", 0.0)) if isinstance(item.get("score", 0.0), (int, float, str)) else 0.0

    doi = _clean_str(_pick(item, ["doi"], ""))

    url = clean_url(
        _clean_str(_pick(item, ["url", "link"], "")),
        title,      
        doi
    )
    if url.startswith("10."):
        url = f"https://doi.org/{url}"
    # pdf_url = _clean_str(_pick(item, ["pdf_url", "pdf", "pdfUrl"], url))

    doc_id = _clean_str(_pick(item, ["doc_id", "id"], "unknown"))
    snippet = build_snippet(abstract if abstract else title, query_terms)

    # KEEP ORIGINAL METADATA
    metadata_fields = {
        "doi": _clean_str(item.get("doi")),
        "pmcid": _clean_str(item.get("pmcid")),
        "pubmed_id": _clean_str(item.get("pubmed_id")),
        "source_x": _clean_str(item.get("source_x")),
        "journal": _clean_str(item.get("journal")),
        "publish_year": _to_int(item.get("publish_year")),
        "_id": _clean_str(item.get("_id")),
    }

    return {
        "doc_id": doc_id,
        "title": title,
        "year": year,
        "publish_time": publish_time,
        "venue": venue,
        "url": url or "#",
        "score": float(score),
        "snippet": snippet,

        # 👇 ADD THIS
        **metadata_fields,

        # existing scores
        **{
            k: v for k, v in item.items()
            if k in ("sparse_score", "dense_score", "temporal_score", "mmr_score")
        },
    }