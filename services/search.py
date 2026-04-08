from utilities.text_utils import normalize_tokens
from utilities.results_normalise import normalize_result
from backend.pinecone_backend import PineconeBackendError, pinecone_b5_search, hybrid_rrf_mmr_search


def apply_filters(results, year_from, year_to, min_citations):
    return [
        r for r in results
        if (r.get("year", 0) == 0 or year_from <= int(r.get("year", 0)) <= year_to)
        and int(r.get("citations", 0)) >= min_citations
    ]


def sort_results(results, sort_by):
    if sort_by == "Date":
        return sorted(results, key=lambda r: (int(r.get("year", 0)), float(r.get("score", 0.0))), reverse=True)

    if sort_by == "Citations":
        return sorted(results, key=lambda r: (int(r.get("citations", 0)), float(r.get("score", 0.0))), reverse=True)

    return sorted(results, key=lambda r: (float(r.get("score", 0.0)), int(r.get("citations", 0))), reverse=True)


def search(
    *,
    query: str,
    top_k: int,
    year_from: int,
    year_to: int,
    min_citations: int,
    sort_by: str,
    pinecone_api_key: str,
    pinecone_index: str,
    pinecone_namespace: str,
) -> tuple[list[dict], str | None]:

    query_terms = normalize_tokens(query)

    try:
        raw = hybrid_rrf_mmr_search(
            query=query,
            api_key=pinecone_api_key,
            index_name=pinecone_index,
            top_k_retrieve=50,
            top_n_final=top_k,
            mmr_lambda=0.7,
            namespace=pinecone_namespace or None,
        )

    except PineconeBackendError as exc:
        return [], str(exc)

    # Normalize
    normalized = [normalize_result(dict(item), query_terms) for item in raw]

    # Apply filters
    filtered = apply_filters(normalized, year_from, year_to, min_citations)

    # Sort
    sorted_results = sort_results(filtered, sort_by)

    return sorted_results[:top_k], None