from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import torch

from functools import lru_cache
from typing import Any

from pinecone import Pinecone
from scipy.sparse import csr_matrix
from sklearn.preprocessing import normalize
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForMaskedLM


class PineconeBackendError(RuntimeError):
    pass


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
DENSE_MODEL = "BAAI/bge-base-en-v1.5"
SPARSE_MODEL = "naver/splade-cocondenser-ensembledistil"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
VOCAB_SIZE = 30522

PROJ_PATH = Path(__file__).resolve().parents[1] / "data" / "projection_config.pkl"


DEVICE = (
    "cuda" if torch.cuda.is_available()
    else "mps" if torch.backends.mps.is_available()
    else "cpu"
)


# ─────────────────────────────────────────────
# LOAD MODELS (cached)
# ─────────────────────────────────────────────
@lru_cache(maxsize=1)
def load_models():
    try:
        dense_model = SentenceTransformer(DENSE_MODEL, device=DEVICE)

        tokenizer = AutoTokenizer.from_pretrained(SPARSE_MODEL)
        splade_model = AutoModelForMaskedLM.from_pretrained(SPARSE_MODEL).to(DEVICE)
        splade_model.eval()

        return dense_model, tokenizer, splade_model

    except Exception as e:
        raise PineconeBackendError(f"Failed to load models: {e}")


@lru_cache(maxsize=1)
def load_projection():
    try:
        with open(PROJ_PATH, "rb") as f:
            data = pickle.load(f)

        return data["projector"], data["alpha"]

    except Exception as e:
        raise PineconeBackendError(f"Projection file not found: {e}")


# ─────────────────────────────────────────────
# ENCODERS
# ─────────────────────────────────────────────
def encode_dense(query: str) -> np.ndarray:
    dense_model, _, _ = load_models()
    vec = dense_model.encode([QUERY_PREFIX + query], normalize_embeddings=True)[0]
    return np.array(vec, dtype=np.float32)


def encode_sparse(query: str):
    _, tokenizer, splade_model = load_models()

    tokens = tokenizer(
        [query],
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=512,
    ).to(DEVICE)

    with torch.no_grad():
        output = splade_model(**tokens)

    vec = torch.max(
        torch.log(1 + torch.relu(output.logits))
        * tokens["attention_mask"].unsqueeze(-1),
        dim=1,
    ).values[0]

    indices = vec.nonzero(as_tuple=True)[0].tolist()
    values = vec[indices].tolist()

    return indices, values


# ─────────────────────────────────────────────
# MAIN B5 ENCODING
# ─────────────────────────────────────────────
def encode_query_b5(query: str) -> np.ndarray:
    projector, alpha = load_projection()

    # Dense
    q_dense = encode_dense(query)

    # Sparse
    indices, values = encode_sparse(query)

    q_sp = csr_matrix(
        (np.array(values, dtype=np.float32), ([0] * len(indices), indices)),
        shape=(1, VOCAB_SIZE),
    )

    q_proj = projector.transform(q_sp)
    if hasattr(q_proj, "toarray"):
        q_proj = q_proj.toarray()

    q_proj = normalize(np.asarray(q_proj, dtype=np.float32), norm="l2")[0]

    # Combine
    q_combined = alpha * q_dense + (1 - alpha) * q_proj
    q_combined = q_combined / np.linalg.norm(q_combined)

    return q_combined


# ─────────────────────────────────────────────
# PINECONE SEARCH
# ─────────────────────────────────────────────
@lru_cache(maxsize=4)
def get_index(api_key: str, index_name: str):
    pc = Pinecone(api_key=api_key)
    return pc.Index(index_name)


def pinecone_b5_search(
    *,
    query: str,
    top_k: int,
    api_key: str,
    index_name: str,
    namespace: str | None = None,
) -> list[dict[str, Any]]:

    if not api_key:
        raise PineconeBackendError("Missing Pinecone API key")

    if not index_name:
        raise PineconeBackendError("Missing Pinecone index name")

    vector = encode_query_b5(query)

    index = get_index(api_key, index_name)

    resp = index.query(
        vector=vector.tolist(),
        top_k=top_k,
        include_metadata=True,
        namespace=namespace or None,
    )

    results = []
    for m in resp.matches:
        meta = m.metadata or {}

        results.append(
            {
                "doc_id": m.id,
                "score": m.score,
                "title": meta.get("title", ""),
                "abstract": meta.get("abstract", ""),
                "publish_time": meta.get("publish_time", ""),
                "journal": meta.get("journal", ""),
                "authors": meta.get("authors", ""),
                "url": meta.get("url", ""),
            }
        )

    return results


# ─────────────────────────────────────────────
# RRF FUSION
# ─────────────────────────────────────────────
def rrf_fuse(
    ranked_lists: list[list[dict]], weights: list[float] | None = None, k: int = 60
) -> list[dict]:
    """Reciprocal Rank Fusion over multiple Pinecone result lists.

    Args:
        ranked_lists: list of Pinecone match lists (each from .query()["matches"])
        weights:      per-list weights (default: equal)
        k:            RRF constant (default 60, per Cormack et al. 2009)

    Returns:
        Fused list sorted by RRF score, each dict has 'id', 'rrf_score', 'metadata'.
    """
    if weights is None:
        weights = [1.0] * len(ranked_lists)

    scores = {}  # doc_id → rrf score
    meta_map = {}  # doc_id → metadata (keep first seen)

    for w, matches in zip(weights, ranked_lists):
        for rank, m in enumerate(matches, start=1):
            did = m["id"]
            scores[did] = scores.get(did, 0.0) + w / (k + rank)
            if did not in meta_map:
                meta_map[did] = m.get("metadata", {})

    fused = [
        {"id": did, "rrf_score": sc, "metadata": meta_map[did]}
        for did, sc in scores.items()
    ]
    fused.sort(key=lambda x: x["rrf_score"], reverse=True)
    return fused


# ─────────────────────────────────────────────
# MMR RE-RANKING
# ─────────────────────────────────────────────
def mmr_rerank(
    query_vec: list[float] | np.ndarray,
    candidates: list[dict],
    doc_vecs: dict[str, list[float]],
    lam: float = 0.7,
    top_n: int = 10,
) -> list[dict]:
    """Maximal Marginal Relevance (Carbonell & Goldstein, 1998).

    Args:
        query_vec:   dense query embedding (normalised)
        candidates:  list of dicts with 'id', 'rrf_score', 'metadata'
        doc_vecs:    {doc_id: dense_embedding} for similarity computation
        lam:         trade-off: 1.0 = pure relevance, 0.0 = pure diversity
        top_n:       how many docs to select

    Returns:
        Re-ranked list of top_n dicts with added 'mmr_score'.
    """
    q = np.array(query_vec)
    selected = []
    remaining = list(candidates)

    for _ in range(min(top_n, len(remaining))):
        best_score = -np.inf
        best_idx = 0

        for i, cand in enumerate(remaining):
            dvec = doc_vecs.get(cand["id"])
            if dvec is None:
                continue
            d = np.array(dvec)

            # Relevance: cosine(query, doc) — both normalised so dot product = cosine
            rel = float(q @ d)

            # Diversity: max similarity to already-selected docs
            div = 0.0
            for s in selected:
                svec = doc_vecs.get(s["id"])
                if svec is not None:
                    div = max(div, float(d @ np.array(svec)))

            mmr = lam * rel - (1 - lam) * div

            if mmr > best_score:
                best_score = mmr
                best_idx = i

        chosen = remaining.pop(best_idx)
        chosen["mmr_score"] = best_score
        selected.append(chosen)

    return selected


# ─────────────────────────────────────────────
# HYBRID SEARCH WITH TWO-PASS RRF + MMR
# ─────────────────────────────────────────────
def hybrid_rrf_mmr_search(
    *,
    query: str,
    api_key: str,
    index_name: str,
    top_k_retrieve: int = 50,
    top_n_final: int = 10,
    rrf_k: int = 60,
    rrf_weights: list[float] | None = None,
    mmr_lambda: float = 0.7,
    namespace: str | None = None,
) -> list[dict[str, Any]]:
    """Two-pass hybrid retrieval with RRF fusion and MMR re-ranking.

    Args:
        query:          search query
        api_key:        Pinecone API key
        index_name:     Pinecone index name
        top_k_retrieve: candidates per pass (default 50)
        top_n_final:    final results after MMR (default 10)
        rrf_k:          RRF constant (default 60)
        rrf_weights:    weights for [dense, sparse] (default [0.6, 0.4])
        mmr_lambda:     MMR trade-off (default 0.7, 1.0=pure relevance)
        namespace:      Pinecone namespace

    Returns:
        List of top results with 'doc_id', 'score', 'mmr_score', and metadata.
    """
    if rrf_weights is None:
        rrf_weights = [0.6, 0.4]  # 60% dense, 40% sparse

    if not api_key:
        raise PineconeBackendError("Missing Pinecone API key")
    if not index_name:
        raise PineconeBackendError("Missing Pinecone index name")

    # ─ Step 1: Encode query (dense + sparse) ─
    q_dense = encode_dense(query)
    q_sparse_indices, q_sparse_values = encode_sparse(query)

    index = get_index(api_key, index_name)

    # ─ Step 2: Dense-only pass ─
    dense_results = index.query(
        vector=q_dense.tolist(),
        top_k=top_k_retrieve,
        include_metadata=True,
        namespace=namespace or None,
    )
    dense_matches = [
        {
            "id": m.id,
            "score": m.score,
            "metadata": m.metadata or {},
        }
        for m in dense_results.matches
    ]

    # ─ Step 3: Sparse-only pass ─
    zero_dense = [0.0] * len(q_dense)
    sparse_results = index.query(
        vector=zero_dense,
        sparse_vector={"indices": q_sparse_indices, "values": q_sparse_values},
        top_k=top_k_retrieve,
        include_metadata=True,
        namespace=namespace or None,
    )
    sparse_matches = [
        {
            "id": m.id,
            "score": m.score,
            "metadata": m.metadata or {},
        }
        for m in sparse_results.matches
    ]

    # ─ Step 4: RRF Fusion ─
    fused = rrf_fuse(
        [dense_matches, sparse_matches],
        weights=rrf_weights,
        k=rrf_k,
    )

    # ─ Step 5: Fetch dense vectors for MMR ─
    candidate_ids = [d["id"] for d in fused[:top_k_retrieve]]
    fetched = index.fetch(ids=candidate_ids, namespace=namespace or None)

    doc_vecs = {}
    for did, data in fetched.vectors.items():
        doc_vecs[did] = data.values

    # ─ Step 6: MMR Re-ranking ─
    final = mmr_rerank(
        query_vec=q_dense,
        candidates=fused[:top_k_retrieve],
        doc_vecs=doc_vecs,
        lam=mmr_lambda,
        top_n=top_n_final,
    )

    # ─ Step 7: Format results ─
    results = []
    for doc in final:
        meta = doc["metadata"]
        results.append(
            {
                "doc_id": doc["id"],
                "rrf_score": doc["rrf_score"],
                "mmr_score": doc["mmr_score"],
                "title": meta.get("title", ""),
                "abstract": meta.get("abstract", ""),
                "publish_time": meta.get("publish_time", ""),
                "journal": meta.get("journal", ""),
                "authors": meta.get("authors", ""),
                "url": meta.get("url", ""),
                "doi": meta.get("doi", ""),
            }
        )

    return results   