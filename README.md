# Streamlit UI (TREC-COVID)

This folder contains a Streamlit UI for searching your indexed TREC-COVID corpus.

This version uses a Pinecone-backed hybrid query encoder (dense + SPLADE + projection fusion / B5) implemented in [backend/pinecone_backend.py](backend/pinecone_backend.py).

## Run

Option A — from the repo root:

```bash
.venv\Scripts\activate
pip install -r UI/requirements.txt
streamlit run UI/main.py
```

In this mode, Streamlit reads secrets from `.streamlit/secrets.toml` in the repo root.

Option B — from inside the `UI/` folder:

```bash
cd UI
..\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run main.py
```

In this mode, Streamlit reads secrets from `UI/.streamlit/secrets.toml`.

## Configuration

This UI queries Pinecone directly and requires:

- A Pinecone API key in `.streamlit/secrets.toml` (see Run section for where this file should live)
- A Pinecone index name (currently hard-coded in [main.py](main.py) as `trec-covid-b5`)
- The projection config file at `data/projection_config.pkl` (used for the projection-fusion step)

Example `secrets.toml`:

```toml
PINECONE_API_KEY = "..."
PINECONE_INDEX = "trec-covid-b5"
PINECONE_NAMESPACE = ""
```

## Project Structure

UI/
│
├── main.py                    # Streamlit entry point (UI + interaction logic)
│
├── backend/
│   └── pinecone_backend.py   # Handles Pinecone connection and vector retrieval (B5 search)
│
├── services/
│   └── search.py             # Core search pipeline (query → retrieval → filtering → ranking)
│
├── render/
│   └── render.py             # UI components for displaying results and metrics
│
├── theme/
│   └── theme.py              # Light/Dark theme styling and CSS injection
│
├── utilities/
│   ├── text_utils.py         # Tokenisation and query preprocessing
│   └── results_normalise.py  # Normalises retrieved results into UI-friendly format
│
├── data/
│   └── projection_config.pkl # Projection matrix for B5 hybrid retrieval
│
├── .streamlit/
│   └── secrets.toml          # (Local only) Stores API keys (e.g., Pinecone) — not committed to Git
│
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation

## Folder structure

- [main.py](main.py): Streamlit page + controls
- [services/search.py](services/search.py): orchestrates retrieval + filtering + sorting
- [backend/pinecone_backend.py](backend/pinecone_backend.py): hybrid query encoder + Pinecone query
- [utilities/](utilities/): tokenization + snippet building + result normalization
- [render/render.py](render/render.py): result cards + advanced metrics table
- [theme/theme.py](theme/theme.py): CSS theme injection
