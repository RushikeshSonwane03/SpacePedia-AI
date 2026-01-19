#!/usr/bin/env python
"""
Migration Verification Script

Verifies all components of the local-to-cloud migration are working correctly.
Run this after migration to ensure system consistency.
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings


def check(name: str, condition: bool, detail: str = ""):
    """Print check result."""
    status = "✅" if condition else "❌"
    msg = f"{status} {name}"
    if detail:
        msg += f" - {detail}"
    print(msg)
    return condition


def main():
    print("=" * 60)
    print("🔍 SpacePedia Migration Verification")
    print("=" * 60)
    
    all_passed = True
    
    # 1. Configuration Checks
    print("\n📋 Configuration Checks:")
    all_passed &= check("LLM Provider", settings.LLM_PROVIDER in ["groq", "gemini"], settings.LLM_PROVIDER)
    all_passed &= check("Groq Model", settings.GROQ_MODEL == "llama-3.3-70b-versatile", settings.GROQ_MODEL)
    all_passed &= check("Gemini Embedding Model", settings.GEMINI_EMBEDDING_MODEL == "text-embedding-004", settings.GEMINI_EMBEDDING_MODEL)
    all_passed &= check("GEMINI_API_KEY configured", bool(settings.GEMINI_API_KEY), "Set" if settings.GEMINI_API_KEY else "Missing")
    all_passed &= check("GROQ_API_KEY configured", bool(settings.GROQ_API_KEY), "Set" if settings.GROQ_API_KEY else "Missing - LLM will fail")
    
    # 2. Import Checks
    print("\n📦 Import Checks:")
    try:
        from langchain_groq import ChatGroq
        all_passed &= check("langchain-groq", True)
    except ImportError as e:
        all_passed &= check("langchain-groq", False, str(e))
    
    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        all_passed &= check("langchain-google-genai", True)
    except ImportError as e:
        all_passed &= check("langchain-google-genai", False, str(e))
    
    try:
        from app.rag.embedder import get_embedder
        all_passed &= check("Embedder factory (get_embedder)", True)
    except ImportError as e:
        all_passed &= check("Embedder factory", False, str(e))
    
    try:
        from app.rag.embedder_gemini import GeminiEmbedder
        all_passed &= check("GeminiEmbedder class", True)
    except ImportError as e:
        all_passed &= check("GeminiEmbedder class", False, str(e))
    
    # 3. Embedder Test
    print("\n🔗 Embedder Verification:")
    try:
        from app.rag.embedder import get_embedder
        embedder = get_embedder()
        all_passed &= check("Embedder initialization", True, type(embedder).__name__)
        
        test_emb = embedder.embed_query("test query")
        all_passed &= check("Query embedding", len(test_emb) == 768, f"Dimension: {len(test_emb)}")
        
        batch_emb = embedder.embed_documents(["text 1", "text 2"])
        all_passed &= check("Batch embedding", len(batch_emb) == 2, f"Got {len(batch_emb)} embeddings")
    except Exception as e:
        all_passed &= check("Embedder test", False, str(e))
    
    # 4. ChromaDB Check
    print("\n🗄️  ChromaDB Verification:")
    try:
        import chromadb
        client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
        collection = client.get_or_create_collection(name="space_pedia")
        count = collection.count()
        all_passed &= check("ChromaDB accessible", True, f"{count} chunks in collection")
    except Exception as e:
        all_passed &= check("ChromaDB", False, str(e))
    
    # 5. Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All verification checks passed!")
    else:
        print("⚠️  Some checks failed - review above for details")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
