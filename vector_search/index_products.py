import asyncio
import pandas as pd
import re
from vector_client import index
from embeddings import generate_embedding
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "products.csv"

# Patterns to detect bulk/pack quantities
BULK_PATTERNS = [
    r'\b(pack|pcs|pieces|set)\s+of\s+\d+\b',
    r'\d+\s+(pack|pcs|pieces|units?|set)\b',
    r'\b(bulk|wholesale|dozen|gross)\b',
    r'\((\d+\s*x\s*\d+|qty:\s*\d+)\)',
]

def strip_bulk_indicators(text):
    """Remove bulk/pack indicators from text, return cleaned text"""
    if not text:
        return text
    
    # Remove bulk patterns while preserving the rest
    cleaned = text
    for pattern in BULK_PATTERNS:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Clean up extra whitespace and separators
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = re.sub(r'\s*\|\s*', ' | ', cleaned)  # Fix separators
    cleaned = re.sub(r'\s*-\s*$', '', cleaned)  # Remove trailing dashes
    
    return cleaned

async def upsert_product(row):
    product_id = str(row["_id"])
    title = str(row.get("title", "") or "")
    description = str(row.get("description", "") or "")
    seller = str(row.get("sellerName", "") or "")
    category = str(row.get("category[0]", "") or "")
    subcategory = str(row.get("subcategory[0]", "") or "")
    created_at = str(row.get("createdAt", "") or "")
    
    # Clean up whitespace
    t = (title or "").strip()
    d = (description or "").strip()
    s = (subcategory or "").strip()
    
    # Strip bulk indicators from title and description
    t = strip_bulk_indicators(t)
    d = strip_bulk_indicators(d)
    
    # Skip if title becomes empty after stripping
    if not t:
        print(f"Skipped {product_id} (title empty after bulk removal)")
        return
    
    # Build a natural, structured sentence
    components = []
    if t:
        components.append(t)
    if d:
        components.append(f"Product Description: {d}")
    if s:
        components.append(f"Category: {s}")
    
    # Join with a clear separator
    product_text = " | ".join(components)
    
    if not product_text:
        return
    
    embedding = await generate_embedding(product_text)
    if not embedding:
        return
    
    index.upsert(
        vectors=[{
            "id": product_id,
            "values": embedding,
            "metadata": {
                "title": title,
                "description": description,
                "seller": seller,
                "category": category,
                "subcategory": subcategory,
                "createdAt": created_at
            }
        }]
    )
    print(f"Indexed {product_id}")

async def main():
    df = pd.read_csv(CSV_PATH)
    for _, row in df.iterrows():
        await upsert_product(row)
    print("Indexing complete")

if __name__ == "__main__":
    asyncio.run(main())