from backend.pinecone_backend import (
    PineconeBackendError,
    dense_only_search,
    sparse_only_search,
    rrf_search,
    hybrid_rrf_mmr_search,
    pinecone_b5_search,
    pinecone_b5_search_mmr,
)
from utilities.text_utils import normalize_tokens
from utilities.results_normalise import normalize_result


def search_all_modes(
    *,
    query: str,
    top_k: int,
    min_citations: int,
    pinecone_api_key: str,
    pinecone_index: str,
    pinecone_namespace: str,
):

    query_terms = normalize_tokens(query)

    try:
        # Conditional search based on selected index
        if pinecone_index == "trec-covid-b5":
            # B5 projection index → run B5 variants
            results = {
                "B5 (Projection)": pinecone_b5_search(
                    query=query,
                    top_k=top_k,
                    api_key=pinecone_api_key,
                    index_name=pinecone_index,
                    namespace=pinecone_namespace,
                ),
                "B5 + MMR": pinecone_b5_search_mmr(
                    query=query,
                    top_k=top_k,
                    api_key=pinecone_api_key,
                    index_name=pinecone_index,
                    namespace=pinecone_namespace,
                ),
            }
        else:
            # Hybrid index (trec-covid) → run all 4 hybrid methods
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
            if int(r.get("citations", 0)) >= min_citations
        ]

    return {k: process(v) for k, v in results.items()}, None