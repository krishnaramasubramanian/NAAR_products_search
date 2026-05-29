"""Configuration management for Pinecone vector search."""
import os
from dataclasses import dataclass, field

@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation."""
    model: str = "text-embedding-3-small"
    dimension: int = 1536
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    max_retries: int = 3
    retry_delay: float = 1.0

@dataclass
class PineconeConfig:
    """Configuration for Pinecone vector database."""
    api_key: str = field(default_factory=lambda: os.getenv("PINECONE_API_KEY", ""))
    standard_index: str = "search"
    hybrid_index: str = "text-search-hybrid"
    dimension: int = 1536
    metric: str = "cosine"
    region: str = "us-east-1"
    cloud: str = "aws"

@dataclass
class VectorSearchConfig:
    """Configuration for vector search queries."""
    index_name: str = "text-search-hybrid"
    top_k: int = 10
    min_score: float = 0.6  # Minimum similarity score threshold
    num_candidates: int = 100  # Number of candidates to examine
    batch_size: int = 100  # Batch size for indexing operations

@dataclass
class DataConfig:
    """Configuration for data processing."""
    csv_path: str = "products.csv"
    batch_upsert_size: int = 10
    required_fields: list = field(default_factory=lambda: [
        "_id", "title", "description", "sellerName",
        "category[0]", "subcategory[0]", "createdAt"
    ])

# Global configuration instances
embedding_config = EmbeddingConfig()
pinecone_config = PineconeConfig()
search_config = VectorSearchConfig()
data_config = DataConfig()

__all__ = [
    "embedding_config",
    "pinecone_config",
    "search_config",
    "data_config",
    "EmbeddingConfig",
    "PineconeConfig",
    "VectorSearchConfig",
    "DataConfig"
]
