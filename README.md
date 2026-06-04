# Pinecone Search

Hybrid product search demo that combines **Pinecone** vector search, **Meilisearch** fuzzy/keyword search, and **Reciprocal Rank Fusion (RRF)** in a Flask web app. Short queries can be spell-corrected using a catalog vocabulary before search.

## Prerequisites

- **Python 3.10+** (3.11 recommended)
- **Docker** (for Meilisearch), or a Meilisearch instance at `http://localhost:7700`
- **OpenAI API key** (embeddings via `text-embedding-3-large`)
- **Pinecone API key**(use same api key as mentioned in the script) and an index named `searchv3` (see [Indexing](#indexing-optional))
- **`products.csv`** in the project root (included in this repo)

## Quick start

### 1. Clone and enter the project

```bash
cd pinecone-search
```

### 2. Create a virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install rapidfuzz       # used by query correction (not listed in requirements.txt)
```

### 3. Set API keys

Export your keys (recommended instead of relying on defaults in code):

```bash
export OPENAI_API_KEY="your-openai-key"
```



### 4. Start Meilisearch

```bash
docker run -it --rm \
  -p 7700:7700 \
  -e MEILI_ENV='development' \
  -v $(pwd)/meili_data:/meili_data \
  getmeili/meilisearch:latest

```

Verify it is running: [http://localhost:7700/health](http://localhost:7700/health)

### 5. Build query-correction vocabulary

From the project root:

```bash
cd query_correction
python build_vocab.py
cp catalog_vocab.pkl ..
cd ..
```

The app expects `catalog_vocab.pkl` in the project root.

### 6. Index data (first-time setup)

**Meilisearch** — load products from `products.csv`:

```bash
python fuzzy/meilisearch_index.py
```

**Pinecone** — generate embeddings and upsert vectors 

Skip  Pinecone indexing and use the default api key.

### 7. Run the web app

From the project root (with the virtual environment activated):

```bash
python app_with_rrf.py
```

Open [http://localhost:5001](http://localhost:5001) in your browser. Use the search UI to try different fusion methods (RRF, weighted, etc.).

## What runs when you search

1. **Pinecone** returns semantic matches (`vector_search/query.py`, index `searchv2`).
2. **Meilisearch** returns keyword/fuzzy matches (`fuzzy/meilisearch_search.py`, index `products`).
3. Results are merged with RRF or other fusion logic in `rrf_utils.py` and returned as JSON to the UI.

## Project layout

| Path | Purpose |
|------|---------|
| `app_with_rrf.py` | Flask app entry point |
| `products.csv` | Product catalog (titles, sellers, images) |
| `templates/index_rrf.html` | Search UI |
| `vector_search/` | Pinecone client, embeddings, indexing, vector query |
| `fuzzy/` | Meilisearch indexing and search |
| `query_correction/` | Vocabulary build and spell correction |
| `rrf_utils.py` | Rank fusion helpers |

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| `FileNotFoundError: catalog_vocab.pkl` | Run [step 5](#5-build-query-correction-vocabulary) |
| Meilisearch connection errors | Meilisearch running on port `7700`; re-run `fuzzy/meilisearch_index.py` |
| Pinecone / OpenAI errors | `OPENAI_API_KEY` and `PINECONE_API_KEY` set; index `searchv3` exists |
| Empty or poor results | Re-index Meilisearch and/or Pinecone; confirm `products.csv` is present |
| Import errors for `rapidfuzz` | `pip install rapidfuzz` |
