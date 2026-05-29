import meilisearch
import pandas as pd
import logging
import re
from pathlib import Path
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent.parent
# Meilisearch client
client = meilisearch.Client('http://localhost:7700')

INDEX_NAME = 'products'
CSV_PATH = ROOT / "products.csv"

def normalize(text):
    if pd.isna(text):
        return ""

    text = str(text).lower()


    text = re.sub(r'[^a-z0-9\s]', '', text)


    text = re.sub(r'\s+', ' ', text).strip()

    return text

try:
    client.delete_index(INDEX_NAME)
    logger.info(f"Deleted existing index: {INDEX_NAME}")
except:
    logger.info("No existing index to delete")

# Create fresh index
client.create_index(INDEX_NAME, {'primaryKey': '_id'})
index = client.index(INDEX_NAME)

# Load CSV
logger.info("Loading products from CSV...")
df = pd.read_csv(CSV_PATH)
logger.info(f"Loaded {len(df)} products")

# Fill NaN and force lowercase
#df['title'] = df['title'].fillna('').astype(str).str.lower()
#df['sellerName'] = df['sellerName'].fillna('').astype(str).str.lower()

# Prepare documents
documents = []
for _, row in df.iterrows():

    original_seller = str(row.get('sellerName', '') or '')
    original_title = str(row.get('title', '') or '')
    documents.append({
        '_id': str(row['_id']),
        'title': original_title,
        'normalized_title' : normalize(original_title),
        'seller_name' : original_seller,
        'normalized_sellerName': normalize(original_seller),
        'desc':normalize(row.get('description','') or '')
    })

logger.info(f"Creating/updating Meilisearch index: {INDEX_NAME}")

# Configure searchable attributes
logger.info("Configuring searchable attributes...")
index.update_searchable_attributes(['title','normalized_title', 'sellerName','normalized_sellerName','desc'])

# Configure sortable attributes
logger.info("Configuring sortable attributes...")
index.update_sortable_attributes(['title','normalized_title'])

# Configure typo tolerance
logger.info("Configuring typo tolerance...")
index.update_typo_tolerance({
    'enabled': True,
    'minWordSizeForTypos': {
        'oneTypo': 4,
        'twoTypos': 8
    },
    'disableOnWords': [],
    'disableOnAttributes': []
})

# Treat punctuation like separators
index.update_settings({
    'separatorTokens': [".", "/", "#", ":", "-", "_"]
})

# Add documents
logger.info(f"Indexing {len(documents)} documents...")
task = index.add_documents(documents)

logger.info(f"Indexing task submitted: {task.task_uid}")
logger.info("Indexing complete!")
logger.info("All titles and seller names indexed in lowercase.")
logger.info("You can now search at http://localhost:7700")