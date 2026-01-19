from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.ingestion.models import IngestedDocument, ContentChunk
import uuid

class HybridChunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # We handle "semantic" implicitly by respecting paragraph boundaries via separators
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )

    def chunk(self, doc: IngestedDocument) -> List[ContentChunk]:
        """
        Splits the document content into chunks.
        """
        if not doc.content:
            return []

        texts = self.splitter.split_text(doc.content)
        chunks = []
        
        current_idx = 0
        for text in texts:
            # Note: Exact char index tracking with RecursiveSplitter is tricky because it drops separators.
            # For strict tracking, we'd need a more manual approach or use specific libraries.
            # For RAG, the content itself is most important. 
            # We will approximate start/end for now if exact reconstruction isn't critical.
            
            # Simple approximation for this phase:
            start = doc.content.find(text, current_idx)
            if start == -1:
                start = current_idx # Fallback if not found (should rarely happen with unique text)
            
            end = start + len(text)
            current_idx = start # Move pointer forward (overlap makes this tricky, but fine for approximation)
            
            chunk = ContentChunk(
                chunk_id=str(uuid.uuid4()),
                text=text,
                start_char_idx=start,
                end_char_idx=end,
                metadata={
                    "source": doc.url,
                    "title": doc.title,
                    "doc_id": doc.id,
                    **doc.metadata # Merge existing metadata (Category, Tags, etc.)
                }
            )
            chunks.append(chunk)

        doc.chunks = chunks
        return chunks
