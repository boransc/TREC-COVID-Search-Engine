from backend.pinecone_backend import (
    PineconeBackendError,
    dense_only_search,
    sparse_only_search,
    rrf_search,
    hybrid_rrf_mmr_search,
)
from utilities.text_utils import normalize_tokens
from utilities.results_normalise import normalize_result

def apply_filters(results, year_from, year_to, min_citations):
    return [
        r for r in results
        if (r.get("year", 0) == 0 or year_from <= int(r.get("year", 0)) <= year_to)
        and int(r.get("citations", 0)) >= min_citations
    ]


def sort_results(results, sort_by):
    if sort_by == "Date":
        return sorted(results, key=lambda r: int(r.get("year", 0)), reverse=True)

    if sort_by == "Citations":
        return sorted(results, key=lambda r: int(r.get("citations", 0)), reverse=True)

    return sorted(results, key=lambda r: float(r.get("score", 0.0)), reverse=True)


def search_all_modes(
    *,
    query: str,
    top_k: int,
    year_from: int,
    year_to: int,
    min_citations: int,
    pinecone_api_key: str,
    pinecone_index: str,
    pinecone_namespace: str,
):

    query_terms = normalize_tokens(query)

    try:
        results = {
            "Dense": dense_only_search(
                query=query,
                top_k=top_k,
                api_key=pinecone_api_key,
                index_name=pinecone_index,
                namespace=pinecone_namespace,
            ),
            "Sparse": sparse_only_search(
                query=query,
                top_k=top_k,
                api_key=pinecone_api_key,
                index_name=pinecone_index,
                namespace=pinecone_namespace,
            ),
            "RRF": rrf_search(
                query=query,
                top_k=top_k,
                api_key=pinecone_api_key,
                index_name=pinecone_index,
                namespace=pinecone_namespace,
            ),
            "RRF + MMR": hybrid_rrf_mmr_search(
                query=query,
                api_key=pinecone_api_key,
                index_name=pinecone_index,
                top_n_final=top_k,
                namespace=pinecone_namespace,
            ),
        }

    except PineconeBackendError as e:
        return {}, str(e)

    # Normalize + filter
    def process(res):
        normalized = [normalize_result(dict(r), query_terms) for r in res]

        return [
            r for r in normalized
            if (r.get("year", 0) == 0 or year_from <= int(r.get("year", 0)) <= year_to)
            and int(r.get("citations", 0)) >= min_citations
        ]

    return {k: process(v) for k, v in results.items()}, None