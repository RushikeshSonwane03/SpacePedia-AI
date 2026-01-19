import traceback
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.rag.engine import RAGEngine
from app.core.logger import logger
from app.api.dependencies import limiter

router = APIRouter()
rag_engine = RAGEngine()

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    query: str
    answer: str
    confidence: str
    reasoning: Optional[str] = None
    sources: List[Dict[str, Any]]

@router.post("/query", response_model=QueryResponse)
@limiter.limit("5/minute")
async def query_endpoint(request: Request, body: QueryRequest):
    if not body.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        result = rag_engine.query(body.query)
        return result
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
