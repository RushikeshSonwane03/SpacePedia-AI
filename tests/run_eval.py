import os
import sys
import pandas as pd
import json
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.orchestration.graph import GraphManager
from app.core.config import settings

def main():
    print("🚀 Starting RAGAS Evaluation...")

    # 1. Load Testset
    testset_path = "tests/data/testset.json"
    if not os.path.exists(testset_path):
        print(f"❌ Error: Testset not found at {testset_path}.")
        print("Run 'python scripts/generate_testset.py' first.")
        return

    print("Loading testset...")
    with open(testset_path, 'r') as f:
        data = json.load(f)

    # 2. Run Inference (Get Answers from OUR System)
    print(f"🧠 Running Inference on {len(data)} questions...")
    
    graph = GraphManager()
    
    questions = []
    answers = [] # Our RAG answers
    contexts = [] # Our retrieved chunks
    ground_truths = [] # From testset
    
    for item in data:
        q = item['question']
        gt = item['ground_truth']
        
        # Invoke System
        response = graph.invoke(q)
        ans = response['answer']
        # Extract text from retrieved docs
        retrieved_texts = [d['text'] for d in response['documents']]
        
        questions.append(q)
        answers.append(ans)
        contexts.append(retrieved_texts)
        ground_truths.append([gt]) # Ragas expects list of strings for GT
        
        print(f"Processed: {q[:50]}...")

    # 3. Prepare Dataset for RAGAS
    eval_dict = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    }
    dataset = Dataset.from_dict(eval_dict)

    # 4. Configure Judge (Gemini)
    gemini_llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=settings.GEMINI_API_KEY
    )
    gemini_embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=settings.GEMINI_API_KEY
    )

    # 5. Evaluate
    print("⚖️ Judging results with RAGAS metrics...")
    results = evaluate(
        dataset=dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall
        ],
        llm=gemini_llm,
        embeddings=gemini_embeddings
    )

    # 6. Report
    print("\n📊 Evaluation Results:")
    print(results)
    
    # Save CSV
    df_res = results.to_pandas()
    df_res.to_csv("evaluation_results.csv", index=False)
    print("💾 Saved detailed results to 'evaluation_results.csv'")

if __name__ == "__main__":
    main()
