from typing import List, Dict, Any
from app.rag.vector_store import VectorStore
from app.core.logger import logger

class Retriever:
    def __init__(self):
        self.vector_store = VectorStore() # Re-uses existing vector store logic

    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves top-k relevant chunks for the given query.
        """
        logger.info(f"Retrieving top {k} context for query: '{query}'")
        try:
            results = self.vector_store.search(query, k=k)
            # Log sources for debugging
            for r in results:
                logger.debug(f"Found source: {r['metadata'].get('title')} (dist: {r.get('distance')})")
            return results
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return []
