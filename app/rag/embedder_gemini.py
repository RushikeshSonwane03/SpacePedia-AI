"""
Gemini Embedding Client with Smart Batching

This module implements Google Gemini text-embedding-004 embeddings
with rate limit protection via smart batching.

Migration Note:
- Replaces NomicEmbedder for cloud deployment
- Implements 20 chunks/batch to reduce API calls by 95%
- Uses time.sleep() between batches to respect RPM limits
"""

from typing import List
import time
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.core.config import settings
from app.core.logger import logger


class GeminiEmbedder:
    """
    Gemini Embeddings with Smart Batching for Rate Limit Protection.
    
    Batching Strategy:
    - Default batch size: 20 chunks (reduces 1500 calls to 75)
    - Sleep between batches: 1.0 second (respects RPM limits)
    - Model: text-embedding-004 (768 dimensions)
    """
    
    def __init__(
        self,
        batch_size: int = 20,
        sleep_between_batches: float = 1.0
    ):
        if not settings.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is required for Gemini embeddings. "
                "Please set it in your .env file."
            )
        
        self.batch_size = batch_size
        self.sleep_between_batches = sleep_between_batches
        
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=f"models/{settings.GEMINI_EMBEDDING_MODEL}",
            google_api_key=settings.GEMINI_API_KEY,
            task_type="retrieval_document"  # Optimized for RAG storage
        )
        
        logger.info(
            f"Gemini Embedder initialized: model={settings.GEMINI_EMBEDDING_MODEL}, "
            f"batch_size={batch_size}, sleep={sleep_between_batches}s"
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple documents with smart batching.
        
        This method batches chunks to reduce API calls and implements
        rate limit protection via sleep between batches.
        
        Args:
            texts: List of text chunks to embed
            
        Returns:
            List of embedding vectors (768 dimensions each)
        """
        if not texts:
            return []
        
        all_embeddings = []
        total_chunks = len(texts)
        total_batches = (total_chunks + self.batch_size - 1) // self.batch_size
        
        logger.info(
            f"Starting batched embedding: {total_chunks} chunks → "
            f"{total_batches} batches (batch_size={self.batch_size})"
        )
        
        for batch_idx in range(0, total_chunks, self.batch_size):
            batch = texts[batch_idx:batch_idx + self.batch_size]
            current_batch_num = (batch_idx // self.batch_size) + 1
            
            try:
                logger.debug(
                    f"Processing batch {current_batch_num}/{total_batches} "
                    f"({len(batch)} chunks)"
                )
                
                # API call for this batch
                batch_embeddings = self.embeddings.embed_documents(batch)
                all_embeddings.extend(batch_embeddings)
                
                # Rate limit protection: sleep between batches (except last)
                if batch_idx + self.batch_size < total_chunks:
                    time.sleep(self.sleep_between_batches)
                    
            except Exception as e:
                logger.error(
                    f"Batch {current_batch_num} failed: {e}. "
                    f"Retrying after extended sleep..."
                )
                # Extended backoff on error
                time.sleep(5.0)
                try:
                    batch_embeddings = self.embeddings.embed_documents(batch)
                    all_embeddings.extend(batch_embeddings)
                except Exception as retry_error:
                    logger.error(f"Retry failed: {retry_error}")
                    raise retry_error
        
        logger.info(
            f"Batched embedding complete: {len(all_embeddings)} embeddings generated"
        )
        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query for retrieval.
        
        Uses task_type="retrieval_query" for optimal search performance.
        
        Args:
            text: Query text to embed
            
        Returns:
            Embedding vector (768 dimensions)
        """
        try:
            # Create a query-optimized embedder
            query_embeddings = GoogleGenerativeAIEmbeddings(
                model=f"models/{settings.GEMINI_EMBEDDING_MODEL}",
                google_api_key=settings.GEMINI_API_KEY,
                task_type="retrieval_query"  # Optimized for search
            )
            return query_embeddings.embed_query(text)
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            raise e
