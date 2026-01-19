#!/usr/bin/env python
"""
Migration Script: Local to Cloud Embeddings

This script handles the complete migration from Nomic (Ollama) embeddings
to Gemini text-embedding-004 embeddings.

IMPORTANT: This script will:
1. Purge the existing ChromaDB collection
2. Re-ingest all Wikipedia pages with Gemini embeddings
3. Implement smart batching to prevent rate limit issues

Usage:
    python scripts/migrate_embeddings.py           # Full migration
    python scripts/migrate_embeddings.py --dry-run # Test without changes
"""

import sys
import os
import json
import asyncio
import argparse
import time

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.core.logger import logger


def purge_collection():
    """Purge the existing ChromaDB collection to remove incompatible embeddings."""
    import chromadb
    
    client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
    
    try:
        # Get collection info before purge
        collection = client.get_collection(name="space_pedia")
        count_before = collection.count()
        print(f"📊 Current collection has {count_before} chunks")
        
        # Delete the collection
        client.delete_collection(name="space_pedia")
        print("🗑️  Purged existing 'space_pedia' collection")
        
        return count_before
    except Exception as e:
        print(f"⚠️  Collection not found or already empty: {e}")
        return 0


def recreate_collection():
    """Recreate the collection with proper settings."""
    import chromadb
    
    client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
    collection = client.get_or_create_collection(
        name="space_pedia",
        metadata={"hnsw:space": "cosine"}
    )
    print("✅ Recreated 'space_pedia' collection")
    return collection


async def run_migration(dry_run: bool = False):
    """
    Execute the full migration pipeline.
    
    Args:
        dry_run: If True, simulate without making changes
    """
    print("=" * 60)
    print("🚀 SpacePedia Embedding Migration: Local → Cloud")
    print("=" * 60)
    print(f"   Embedding Provider: {settings.EMBEDDING_PROVIDER}")
    print(f"   Embedding Model: {settings.GEMINI_EMBEDDING_MODEL}")
    print(f"   ChromaDB Path: {settings.CHROMA_DB_PATH}")
    print(f"   Dry Run: {dry_run}")
    print("=" * 60)
    
    if dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made\n")
    
    # Step 1: Verify API key
    if not settings.GEMINI_API_KEY:
        print("❌ ERROR: GEMINI_API_KEY is not set in .env file")
        print("   Please add: GEMINI_API_KEY=your_key_here")
        return False
    
    print("✅ GEMINI_API_KEY is configured")
    
    # Step 2: Load candidates
    candidates_file = "app/ingestion/candidates.json"
    try:
        with open(candidates_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ ERROR: {candidates_file} not found")
        return False
    
    total_pages = sum(len(items) for items in data.values())
    print(f"✅ Loaded {total_pages} Wikipedia pages from candidates.json")
    
    # Step 3: Test embedder
    print("\n📡 Testing Gemini Embedder connection...")
    if not dry_run:
        try:
            from app.rag.embedder import get_embedder
            embedder = get_embedder()
            test_embedding = embedder.embed_query("test connection")
            print(f"✅ Embedder test successful (vector dimension: {len(test_embedding)})")
        except Exception as e:
            print(f"❌ Embedder test failed: {e}")
            return False
    else:
        print("   [Skipped in dry run]")
    
    # Step 4: Purge old collection
    print("\n🗑️  Purging old embeddings...")
    if not dry_run:
        old_count = purge_collection()
        recreate_collection()
    else:
        print("   [Skipped in dry run]")
    
    # Step 5: Re-ingest with new embeddings
    print("\n📥 Starting re-ingestion with Gemini embeddings...")
    if not dry_run:
        from app.ingestion.batch_processor import BatchIngestion
        
        # Use longer delay for rate limiting
        batch_processor = BatchIngestion(rate_limit_delay=2.0)
        await batch_processor.process_candidates(candidates_file)
    else:
        print(f"   Would ingest {total_pages} pages")
        print("   [Skipped in dry run]")
    
    # Step 6: Verify migration
    print("\n🔍 Verifying migration...")
    if not dry_run:
        import chromadb
        client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
        collection = client.get_collection(name="space_pedia")
        new_count = collection.count()
        
        print(f"✅ Migration complete!")
        print(f"   New collection has {new_count} chunks")
    else:
        print("   [Skipped in dry run]")
    
    print("\n" + "=" * 60)
    print("✅ Migration completed successfully!")
    print("=" * 60)
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Migrate SpacePedia from local to cloud embeddings"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate migration without making changes"
    )
    
    args = parser.parse_args()
    
    success = asyncio.run(run_migration(dry_run=args.dry_run))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
