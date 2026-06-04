import asyncio
import logging
from dataclasses import dataclass
from typing import List, Optional
from .vector_client import pc
from .embeddings import generate_embedding

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


# -------------------
# Config
# -------------------

@dataclass
class VectorSearchConfig:
    index_name: str = "searchv3"
    top_k: int = 10
    candidate_k: int = 50
    min_score: float = 0.5


CONFIG = VectorSearchConfig()
index = pc.Index(CONFIG.index_name)


# -------------------
# Result Object
# -------------------

@dataclass
class SearchResult:
    score: float
    title: str
    seller: str
    product_id: str
    metadata: dict


# -------------------
# Search
# -------------------

async def search(
    query: str,
    top_k: Optional[int] = None,
    min_score: Optional[float] = None
) -> List[SearchResult]:

    if top_k is None:
        top_k = CONFIG.top_k

    if min_score is None:
        min_score = CONFIG.min_score

    if not query or not query.strip():
        return []

    try:
        # Dense embedding
        query_lower = query.lower().strip()
        dense_vector = await generate_embedding(query_lower)

        if not dense_vector:
            return []

        # -------------------
        # Dense candidate retrieval
        # -------------------

        dense_results = index.query(
            vector=dense_vector,
            top_k=CONFIG.candidate_k,
            include_metadata=True
        )

        
        results = []

        # -------------------
        # Local reranking
        # -------------------
        

        for m in dense_results.matches:
            score = float(m.score)
            if score < min_score:
                continue

            results.append(
                SearchResult(
                    score=score,
                    title=m.metadata.get("title",""),
                    seller=m.metadata.get("seller",""),
                    product_id=m.id,
                    metadata=m.metadata
                )
            )

        # Sort by reranked score            
        results.sort(
            key=lambda x: x.score,
            reverse=True
        )

        return results

    except Exception as err:
        logger.error(err, exc_info=True)
        return []


# -------------------
# Demo
# -------------------

async def main():

    results = await search(
        "Herbal Cup Sambrani : 12 Pcs ",
        top_k=10,
        min_score=0.2
    )
    if not results:
        print("No results found")
        return
    for r in results:
        print(f"{r.title} | {r.seller}")
    


if __name__ == "__main__":
    asyncio.run(main())