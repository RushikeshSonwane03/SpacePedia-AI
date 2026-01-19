#!/usr/bin/env python
"""
SpacePedia Dynamic Data Ingestion Tool

A flexible script for updating/adding content to the knowledge base.
Supports multiple modes: single URL, batch file, or interactive.

Usage:
    python scripts/ingest_data.py                     # Interactive mode
    python scripts/ingest_data.py --url <url>         # Single URL
    python scripts/ingest_data.py --file <json_file>  # Batch from file
    python scripts/ingest_data.py --refresh           # Re-ingest all candidates
"""

import sys
import os
import json
import asyncio
import argparse
from datetime import datetime

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.core.logger import logger
from app.ingestion.pipeline import IngestionPipeline
from app.ingestion.batch_processor import BatchIngestion

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


class DataIngestionTool:
    """Dynamic data ingestion with multiple modes."""
    
    def __init__(self):
        self.pipeline = IngestionPipeline()
        self.stats = {"success": 0, "failed": 0, "total": 0}
    
    async def ingest_single_url(self, url: str, metadata: dict = None):
        """Ingest a single URL into the knowledge base."""
        print(f"\n{YELLOW}📥 Ingesting: {url}{RESET}")
        
        try:
            doc = await self.pipeline.run(url, metadata=metadata)
            
            if doc.status.value == "vectorized":
                print(f"{GREEN}✅ Success: {doc.title} ({len(doc.chunks)} chunks){RESET}")
                self.stats["success"] += 1
                return True
            else:
                print(f"{RED}❌ Failed: {doc.status} - {doc.error_message}{RESET}")
                self.stats["failed"] += 1
                return False
        except Exception as e:
            print(f"{RED}❌ Error: {e}{RESET}")
            self.stats["failed"] += 1
            return False
    
    async def ingest_from_file(self, file_path: str):
        """Ingest URLs from a JSON file."""
        print(f"\n{BOLD}📂 Loading URLs from: {file_path}{RESET}")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"{RED}❌ File not found: {file_path}{RESET}")
            return
        
        # Support multiple formats
        urls = []
        
        if isinstance(data, list):
            # Simple list of URLs or objects
            for item in data:
                if isinstance(item, str):
                    urls.append({"url": item})
                elif isinstance(item, dict):
                    urls.append(item)
        elif isinstance(data, dict):
            # Category-based format (like candidates.json)
            for category, pages in data.items():
                for page in pages:
                    page["category"] = category
                    urls.append(page)
        
        self.stats["total"] = len(urls)
        print(f"{CYAN}Found {len(urls)} URLs to process{RESET}")
        
        for i, item in enumerate(urls, 1):
            url = item.get("url")
            if not url:
                continue
            
            print(f"\n[{i}/{len(urls)}] ", end="")
            
            metadata = {
                "title": item.get("title", ""),
                "category": item.get("category", "General"),
                "source": url
            }
            
            await self.ingest_single_url(url, metadata)
            
            # Rate limit protection
            await asyncio.sleep(2.0)
        
        self.print_summary()
    
    async def refresh_all(self):
        """Re-ingest all candidates from candidates.json."""
        candidates_file = "app/ingestion/candidates.json"
        print(f"\n{BOLD}🔄 Refreshing entire knowledge base...{RESET}")
        
        batch = BatchIngestion(rate_limit_delay=2.0)
        await batch.process_candidates(candidates_file)
    
    def print_summary(self):
        """Print ingestion summary."""
        print(f"\n{BOLD}{'='*50}{RESET}")
        print(f"{BOLD}📊 Ingestion Summary{RESET}")
        print(f"{'='*50}")
        print(f"  Total: {self.stats['total']}")
        print(f"  {GREEN}Success: {self.stats['success']}{RESET}")
        print(f"  {RED}Failed: {self.stats['failed']}{RESET}")
        print(f"{'='*50}\n")
    
    def run_interactive(self):
        """Interactive mode with menu."""
        while True:
            print(f"\n{BOLD}{'='*50}{RESET}")
            print(f"{CYAN}🚀 SpacePedia Data Ingestion Tool{RESET}")
            print(f"{'='*50}")
            print(f"\n  {CYAN}[1]{RESET} Ingest single URL")
            print(f"  {CYAN}[2]{RESET} Ingest from JSON file")
            print(f"  {CYAN}[3]{RESET} Refresh all (re-ingest candidates.json)")
            print(f"  {CYAN}[4]{RESET} Check database stats")
            print(f"  {CYAN}[Q]{RESET} Quit")
            print(f"\n{'='*50}")
            
            choice = input(f"\n{CYAN}Enter choice: {RESET}").strip().upper()
            
            if choice == 'Q':
                print(f"\n{YELLOW}Goodbye!{RESET}")
                break
            
            elif choice == '1':
                url = input(f"{CYAN}Enter URL: {RESET}").strip()
                if url:
                    category = input(f"{CYAN}Category (optional): {RESET}").strip() or "General"
                    metadata = {"category": category, "source": url}
                    asyncio.run(self.ingest_single_url(url, metadata))
            
            elif choice == '2':
                file_path = input(f"{CYAN}Enter JSON file path: {RESET}").strip()
                if file_path:
                    asyncio.run(self.ingest_from_file(file_path))
            
            elif choice == '3':
                confirm = input(f"{YELLOW}⚠️ This will re-ingest all data. Continue? (y/n): {RESET}")
                if confirm.lower() == 'y':
                    asyncio.run(self.refresh_all())
            
            elif choice == '4':
                self.show_db_stats()
            
            else:
                print(f"{RED}Invalid choice.{RESET}")
    
    def show_db_stats(self):
        """Show current database statistics."""
        import chromadb
        
        print(f"\n{BOLD}📊 Database Statistics{RESET}")
        print(f"{'='*50}")
        
        try:
            client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
            collection = client.get_collection(name="space_pedia")
            count = collection.count()
            
            # Get unique sources
            res = collection.get(include=["metadatas"], limit=10000)
            sources = set()
            categories = set()
            
            for m in res.get("metadatas", []):
                sources.add(m.get("title", "Unknown"))
                categories.add(m.get("category", "Unknown"))
            
            print(f"  Total Chunks: {count}")
            print(f"  Unique Documents: {len(sources)}")
            print(f"  Categories: {len(categories)}")
            print(f"\n  Categories Found:")
            for cat in sorted(categories):
                print(f"    - {cat}")
            
        except Exception as e:
            print(f"{RED}Error: {e}{RESET}")
        
        print(f"{'='*50}\n")


def main():
    parser = argparse.ArgumentParser(description="SpacePedia Data Ingestion Tool")
    parser.add_argument("--url", type=str, help="Ingest a single URL")
    parser.add_argument("--file", type=str, help="Ingest from JSON file")
    parser.add_argument("--refresh", action="store_true", help="Re-ingest all candidates")
    parser.add_argument("--category", type=str, default="General", help="Category for single URL")
    
    args = parser.parse_args()
    tool = DataIngestionTool()
    
    if args.url:
        metadata = {"category": args.category, "source": args.url}
        asyncio.run(tool.ingest_single_url(args.url, metadata))
    elif args.file:
        asyncio.run(tool.ingest_from_file(args.file))
    elif args.refresh:
        asyncio.run(tool.refresh_all())
    else:
        tool.run_interactive()


if __name__ == "__main__":
    main()
