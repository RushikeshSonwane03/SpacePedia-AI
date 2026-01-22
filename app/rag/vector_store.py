import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.ingestion.models import ContentChunk
from app.rag.embedder import get_embedder
from app.core.logger import logger
import uuid

class VectorStore:
    def __init__(self, collection_name: str = "space_pedia"):
        import os
        if not os.path.exists(settings.CHROMA_DB_PATH):
             logger.warning(f"ChromaDB path {settings.CHROMA_DB_PATH} not found. Creating it (empty).")
             # We create it so it doesn't crash, but it will be empty unless user uploaded it.
             os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
             
        self.client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
        self.embedder = get_embedder()  # Factory: Gemini or Ollama based on config
        try:
             self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"} # Cosine similarity
            )
        except Exception as e:
             logger.error(f"Failed to load collection: {e}. Attempting to reset/continue.")
             # Fallback logic could go here
             raise e

    def add_chunks(self, chunks: List[ContentChunk]):
        if not chunks:
            return

        ids = [c.chunk_id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = []
        for c in chunks:
            # Node 4: Metadata Normalization (Safety Net)
            clean_meta = {}
            for k, v in c.metadata.items():
                if isinstance(v, (list, dict)):
                    clean_meta[k] = str(v) # Flatten complex types
                else:
                    clean_meta[k] = v
            metadatas.append(clean_meta)
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        embeddings = self.embedder.embed_documents(documents)
        
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings
        )
        logger.info(f"Added {len(chunks)} chunks to ChromaDB.")

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        query_embedding = self.embedder.embed_query(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
        )
        
        # Parse results into cleaner format
        parsed_results = []
        if results['ids']:
            for i in range(len(results['ids'][0])):
                parsed_results.append({
                    "id": results['ids'][0][i],
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if results['distances'] else None
                })
        
        return parsed_results

    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all unique documents in the store (based on metadata).
        This is a 'lite' query that fetches only metadata.
        """
        # Fetch all metadata (limit to 1000 chunks for now)
        try:
            results = self.collection.get(include=["metadatas"])
            metadatas = results.get("metadatas", [])
            
            unique_docs = {}
            for meta in metadatas:
                title = meta.get("title", "Unknown")
                source = meta.get("source", "Unknown")
                category = meta.get("category", "General")
                key = f"{title}-{source}"
                if key not in unique_docs:
                    unique_docs[key] = {
                        "title": title,
                        "source": source,
                        "category": category,
                        "type": "Article"
                    }
            return list(unique_docs.values())
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return []

    def get_all_text_chunks(self, limit: int = 50) -> List[str]:
        """
        Retrieves a random sample of text chunks for evaluation dataset generation.
        """
        try:
            # Fetch a batch. Chroma doesn't support random native, but we can fetch and slice.
            # limit=None fetches all? CAREFUL.
            # safe fetch 200, then slice.
            results = self.collection.get(limit=limit, include=["documents"])
            return results.get("documents", [])
        except Exception as e:
            logger.error(f"Error fetching text chunks: {e}")
            return []
