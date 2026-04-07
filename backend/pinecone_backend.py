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