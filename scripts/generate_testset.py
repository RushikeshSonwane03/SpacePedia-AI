import os
import sys
import pandas as pd
from langchain_core.documents import Document as LangchainDocument
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from ragas.testset.generator import TestsetGenerator
from ragas.testset.evolutions import simple, reasoning, multi_context

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.rag.vector_store import VectorStore
from app.core.config import settings

def main():
    print("🚀 Starting Testset Generation...")
    
    # 1. Validation
    if not settings.GEMINI_API_KEY:
        print("❌ Error: GEMINI_API_KEY is missing in settings. Evaluation requires a strong LLM.")
        return

    # 2. Fetch Data
    store = VectorStore()
    chunks = store.get_all_text_chunks(limit=20) # Start small to save cost/time
    if not chunks:
        print("❌ Error: No chunks found in Vector Store. Ingest data first.")
        return
    
    print(f"✅ Fetched {len(chunks)} chunks from Knowledge Base.")
    
    # Convert to Langchain Documents
    # We assign fake filenames because RAGAS uses 'filename' metadata for distribution
    documents = [
        LangchainDocument(
            page_content=chunk, 
            metadata={"filename": f"doc_{i}.txt"}
        ) for i, chunk in enumerate(chunks)
    ]

    # 3. Configure Generator (Gemini)
    # RAGAS Generator needs generator_llm and critic_llm
    generator_llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.5
    )
    critic_llm = ChatGoogleGenerativeAI( # Used for filtering bad questions
        model="gemini-1.5-flash",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.0
    )
    # Embeddings for similarity check
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=settings.GEMINI_API_KEY
    )

    generator = TestsetGenerator.from_langchain(
        generator_llm,
        critic_llm,
        embeddings
    )

    # 4. Generate
    print("⏳ Generating synthetic questions (this may take a minute)...")
    # Distributions: 50% Simple, 25% Reasoning, 25% Multi-Context
    testset = generator.generate_with_langchain_docs(
        documents,
        test_size=10, 
        distributions={simple: 0.5, reasoning: 0.25, multi_context: 0.25}
    )

    # 5. Save
    df = testset.to_pandas()
    os.makedirs("tests/data", exist_ok=True)
    output_path = "tests/data/testset.json"
    df.to_json(output_path, orient="records", indent=2)
    
    print(f"✅ Testset generated with {len(df)} questions.")
    print(f"💾 Saved to: {output_path}")
    print("\nSample Question:")
    print(df.iloc[0]['question'])

if __name__ == "__main__":
    main()
