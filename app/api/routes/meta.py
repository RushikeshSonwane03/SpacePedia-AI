from fastapi import APIRouter
from typing import List, Dict, Any
from pydantic import BaseModel
from app.rag.vector_store import VectorStore
from app.core.logger import logger

router = APIRouter()
store = VectorStore()

class DocumentMeta(BaseModel):
    title: str
    source: str
    category: str
    type: str

@router.get("/knowledge", response_model=List[DocumentMeta])
async def get_knowledge_base():
    """
    Get list of all documents in the Knowledge Base.
    """
    try:
        docs = store.list_documents()
        return docs
    except Exception as e:
        logger.error(f"Failed to fetch knowledge base: {e}")
        return []
