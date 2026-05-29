import asyncio
import logging
from .vector_client import client, EMBEDDING_MODEL

logger = logging.getLogger(__name__)


async def with_retry(func, retries=3, delay=1.0):
    """Retry handler with exponential backoff for embedding generation."""
    attempt = 0
    while attempt < retries:
        try:
            return await func()
        except Exception as err:
            logger.error(f"Retry attempt {attempt + 1} failed: {str(err)}")
            attempt += 1
            if attempt >= retries:
                raise
            await asyncio.sleep(delay * attempt)


async def generate_embedding(text: str):
    """Generate embedding for text using OpenAI API with retry logic."""
    if not text or not text.strip():
        logger.warning("Empty text provided for generating embeddings")
        return []

    try:
        async def create_embedding():
            response = await client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text,
                dimensions=1536
            )
            embedding = response.data[0].embedding
            if not embedding:
                logger.warning("No embedding returned for the text")
                return []
            return embedding
        
        return await with_retry(create_embedding, retries=3, delay=1.0)
    except Exception as err:
        logger.error(f"Failed to generate embedding: {str(err)}")
        return []