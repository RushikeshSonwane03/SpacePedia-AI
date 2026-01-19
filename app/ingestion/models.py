from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, HttpUrl
import uuid

class DocumentType(str, Enum):
    WEB_PAGE = "web_page"
    PDF = "pdf"
    ARXIV_PAPER = "arxiv_paper"
    IMAGE = "image"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    CRAWLED = "crawled"
    PARSED = "parsed"
    NORMALIZED = "normalized"
    VECTORIZED = "vectorized"
    FAILED = "failed"

class ContentChunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    start_char_idx: int
    end_char_idx: int
    metadata: Dict[str, Any] = Field(default_factory=dict)

class IngestedDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str
    title: Optional[str] = None
    doc_type: DocumentType
    content: Optional[str] = None  # Full raw text
    chunks: List[ContentChunk] = Field(default_factory=list)
    
    # Metadata
    source_domain: str = "wikipedia.org"
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    language: str = "en"
    author: Optional[str] = None
    publication_date: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict) # E.g. {"category": "Space_agencies"}
    
    # Processing State
    status: ProcessingStatus = ProcessingStatus.PENDING
    error_message: Optional[str] = None
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }
