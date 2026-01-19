"""
Embedder Factory Module

Provides the get_embedder() factory function for obtaining
the appropriate embedder based on configuration.

Cloud-only architecture: Uses Gemini text-embedding-004.
"""

from typing import List
from app.core.config import settings
from app.core.logger import logger


def get_embedder():
    """
    Factory function to get the Gemini embedder.
    
    Returns:
        GeminiEmbedder for cloud embedding via Google Gemini API
    """
    from app.rag.embedder_gemini import GeminiEmbedder
    logger.info("Using Gemini Embedder (Cloud)")
    return GeminiEmbedder()
