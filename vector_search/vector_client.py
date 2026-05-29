import os
import logging
from openai import AsyncOpenAI
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
logger = logging.getLogger(__name__)
load_dotenv()
# OpenAI Client Configuration
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536

# Pinecone Configuration
pc = Pinecone(
    api_key= os.getenv("PINECONE_API_KEY")
)

INDEX_NAME = "searchv2"
HYBRID_INDEX_NAME = "text-search-hybrid"
DIMENSION = 1536

# Initialize standard index
if INDEX_NAME not in pc.list_indexes().names():
    logger.info(f"Creating index: {INDEX_NAME}")
    pc.create_index(
        name=INDEX_NAME,
        dimension=DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )
else:
    logger.info(f"Index '{INDEX_NAME}' already exists")

index = pc.Index(INDEX_NAME)