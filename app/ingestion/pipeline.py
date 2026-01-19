from app.ingestion.crawler import SpaceCrawler
from app.ingestion.parser import DocumentParser
from app.ingestion.normalizer import TextNormalizer
from app.rag.chunker import HybridChunker
from app.rag.vector_store import VectorStore
from app.ingestion.models import IngestedDocument, ProcessingStatus
from app.core.logger import logger
from typing import Dict

class IngestionPipeline:
    def __init__(self):
        self.crawler = SpaceCrawler()
        self.parser = DocumentParser()
        self.normalizer = TextNormalizer()
        self.chunker = HybridChunker()
        self.vector_store = VectorStore() # This initializes the DB connection

    async def run(self, url: str, metadata: Dict = None) -> IngestedDocument:
        logger.info(f"Running ingestion pipeline for {url}")
        
        # 1. Crawl
        doc = await self.crawler.crawl_url(url)
        if doc.status == ProcessingStatus.FAILED:
            logger.error(f"Crawling failed: {doc.error_message}")
            return doc
        
        # Inject Metadata early
        if metadata:
            doc.metadata.update(metadata)
            doc.title = metadata.get("title", doc.title) # Prefer candidate title
            
        # 2. Parse
        doc = self.parser.parse(doc)
        if doc.status == ProcessingStatus.FAILED:
            logger.error(f"Parsing failed: {doc.error_message}")
            return doc
            
        # 3. Normalize
        doc = self.normalizer.normalize(doc)
        if doc.status == ProcessingStatus.FAILED:
            logger.error(f"Normalization failed: {doc.error_message}")
            return doc

        # 4. Chunk
        chunks = self.chunker.chunk(doc)
        if not chunks:
             logger.warning(f"No chunks created for {doc.url}")
             return doc
             
        # 5. Store (Vectorize & Persist)
        try:
            self.vector_store.add_chunks(chunks)
            doc.status = ProcessingStatus.VECTORIZED
        except Exception as e:
            logger.error(f"Vectorization failed: {e}")
            doc.status = ProcessingStatus.FAILED
            doc.error_message = str(e)
            return doc
            
        logger.info(f"Ingestion pipeline completed for {url}. Stored {len(chunks)} chunks.")
        return doc
