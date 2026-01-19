
import asyncio
from typing import List, Dict
import time
from app.ingestion.pipeline import IngestionPipeline
from app.ingestion.models import IngestedDocument, ProcessingStatus
from app.core.logger import logger

class BatchIngestion:
    """
    Handles batched ingestion of URLs with rate limiting and metadata support.
    """
    def __init__(self, rate_limit_delay: float = 1.0):
        self.pipeline = IngestionPipeline()
        self.rate_limit_delay = rate_limit_delay

    async def process_candidates(self, candidates_file: str = "candidates.json"):
        import json
        
        try:
            with open(candidates_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.error(f"Candidates file {candidates_file} not found.")
            return

        total_tasks = sum(len(items) for items in data.values())
        print(f"📦 Starting Batch Ingestion of {total_tasks} documents...")
        
        current_idx = 0
        success_count = 0
        
        for category, pages in data.items():
            print(f"\n📂 Processing Category: {category} ({len(pages)} items)")
            
            for page in pages:
                if not page.get("selected", True):
                    continue
                    
                current_idx += 1
                url = page["url"]
                title = page["title"]
                tags = page.get("tags", [category]) # Use tags if available, else cat
                
                # Metadata packet (Node 4: Normalize to scalar)
                flat_tags = ",".join(tags) if isinstance(tags, list) else str(tags)
                
                metadata = {
                    "category": category,
                    "tags": flat_tags, # Flattened: "tag1,tag2"
                    "title": title,
                    "source": url # FIX: Used to be "wikipedia", now passing full URL
                }
                
                print(f"  [{current_idx}/{total_tasks}] Ingesting: {title}...", end="", flush=True)
                
                try:
                    # Run Pipeline
                    doc = await self.pipeline.run(url, metadata=metadata)
                    
                    if doc.status == ProcessingStatus.VECTORIZED:
                        print(f" ✅ (Chunks: {len(doc.chunks)})")
                        success_count += 1
                    else:
                        print(f" ❌ ({doc.error_message})")
                        
                except Exception as e:
                    print(f" ❌ Exception: {e}")
                
                # Rate Limit
                time.sleep(self.rate_limit_delay)

        print("-" * 50)
        print(f"🏁 Ingestion Complete. Success: {success_count}/{total_tasks}")
