# TREC-COVID Scholar Search (Streamlit + Pinecone)

A lightweight Streamlit app for searching an **already-indexed TREC-COVID corpus** stored in **Pinecone**.

The UI is intentionally simple: type a query, pick how many results to show + a year range, then compare multiple retrieval strategies side-by-side.

## What the UI shows

- **Search box + Search button**
- **Sidebar filters**
  - Results count (`top_k`)
  - Year range (filters on metadata when available)
  - Light/Dark theme toggle
- **Result tabs** (one per retrieval method)
  - **Dense** (dense-only embedding search)
  - **Sparse** (SPLADE sparse-only search)
  - **RRF** (Reciprocal Rank Fusion of dense + sparse)
  - **RRF + MMR** (RRF fusion, then MMR re-ranking for diversity)

Each result is rendered as a card with a clickable title link and a “Show more” expander containing key metadata fields.

## Requirements

- Python **3.10+** (this code uses `X | Y` type unions)
- A Pinecone index populated with your corpus
- Internet access on first run (downloads Hugging Face models)

The dependencies are listed in [requirements.txt](requirements.txt).

## Quickstart (local)

1) Create a virtual environment and install deps

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r "UI - Copy/requirements.txt"
```

If you prefer installing from inside this folder:

```powershell
cd "UI - Copy"
pip install -r requirements.txt
```

**macOS/Linux (bash/zsh):**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r "UI - Copy/requirements.txt"
```

If you prefer installing from inside this folder:

```bash
cd "UI - Copy"
pip install -r requirements.txt
```

2) Configure secrets

Set your Pinecone key in `.streamlit/secrets.toml`.

- If you run the app from inside `UI - Copy/`, use [./.streamlit/secrets.toml](.streamlit/secrets.toml).
- If you run `streamlit run` from the repo root, put the file at `<repo_root>/.streamlit/secrets.toml` (or use your global Streamlit secrets file).

```toml
PINECONE_API_KEY = "YOUR_KEY_HERE"
```

Security note: keep API keys out of git history. This repo ignores `.streamlit/secrets.toml` via [.gitignore](.gitignore), but if you ever committed a key, rotate it in Pinecone.

3) Run Streamlit

From inside this folder (recommended):

```bash
cd "UI - Copy"
streamlit run main.py
```

Or from the repo root:

```bash
streamlit run "UI - Copy/main.py"
```

## Configuration

### Pinecone

The UI reads the Pinecone API key from `st.secrets["PINECONE_API_KEY"]` in [main.py](main.py).

The index name is currently hard-coded in [main.py](main.py) as:

```python
PINECONE_INDEX = "trec-covid"
```

If your index name or namespace differs, update the constants/arguments in [main.py](main.py).

### Index schema expectations

This app queries Pinecone using:

- A **dense** query embedding from `BAAI/bge-base-en-v1.5`
- A **sparse** query vector from `naver/splade-cocondenser-ensembledistil`

To fully use the Sparse / RRF / RRF+MMR tabs, your Pinecone vectors should include a sparse component (and relevant metadata). At minimum, results render best when metadata contains fields like `title`, `abstract`, `publish_time` (or `year`/`publish_year`), and `url`.

## Retrieval methods (how tabs differ)

- **Dense**: queries Pinecone using only the dense embedding.
- **Sparse**: queries Pinecone using only SPLADE sparse weights.
- **RRF**: runs Dense and Sparse separately, then fuses ranks via weighted Reciprocal Rank Fusion (see [backend/pinecone_backend.py](backend/pinecone_backend.py)).
- **RRF + MMR**: fuses with RRF, fetches candidate dense vectors, then re-ranks with Maximal Marginal Relevance (MMR) to promote diversity.

## Project structure

```text
UI - Copy/
	main.py
	README.md
	requirements.txt
	.streamlit/
		secrets.toml
	backend/
		pinecone_backend.py
	data/
		projection_config.pkl
	render/
		render.py
	services/
		search.py
	theme/
		theme.py
	utilities/
		results_normalise.py
		text_utils.py
```

- [main.py](main.py): Streamlit page layout, sidebar filters, and tabs
- [services/search.py](services/search.py): runs all retrieval modes and applies metadata filters
- [backend/pinecone_backend.py](backend/pinecone_backend.py): dense/sparse encoders + Pinecone querying + RRF/MMR logic
- [render/render.py](render/render.py): result cards (and an optional advanced metrics table, currently not enabled in the UI)
- [theme/theme.py](theme/theme.py): light/dark theme injection via CSS

## Troubleshooting

- **“Missing Pinecone API key”**: set `PINECONE_API_KEY` in [.streamlit/secrets.toml](.streamlit/secrets.toml).
- **Index not found / auth errors**: verify the Pinecone environment, key permissions, and that `PINECONE_INDEX` in [main.py](main.py) matches your index.
- **First run is slow**: the encoder models download the first time and are cached afterwards.
- **Torch install issues**: install a compatible `torch` build for your OS/Python version before installing the rest of the requirements.

## Notes

- The codebase contains an experimental **projection-fusion (B5)** encoder (see `projection_config.pkl` and related functions in [backend/pinecone_backend.py](backend/pinecone_backend.py)). The current UI flow compares Dense/Sparse/RRF/MMR modes; the B5 encoder is not wired into the tabs by default.
