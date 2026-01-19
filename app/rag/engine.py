from typing import Dict, Any, List
from app.rag.retriever import Retriever
from app.rag.llm import LLMClient
from app.rag.validator import OutputValidator
from app.core.logger import logger

class RAGEngine:
    def __init__(self):
        self.retriever = Retriever()
        self.llm = LLMClient()
        self.validator = OutputValidator()

    def query(self, query_text: str) -> Dict[str, Any]:
        """
        Orchestrates the RAG flow: Retrieve -> Augment -> Generate -> Validate
        """
        logger.info(f"Processing query: {query_text}")
        
        # 1. Retrieve Context
        context_docs = self.retriever.retrieve(query_text, k=3)
        
        # 2. Construct Prompt (JSON enforcement)
        context_str = "\n\n".join([doc['text'] for doc in context_docs])
        
        system_prompt = (
            "You are SpacePedia AI, an expert on space exploration.\n"
            "Use the provided context to answer the user's question.\n"
            "You MUST return your response in valid JSON format with the following keys:\n"
            "- 'answer': The direct answer to the question.\n"
            "- 'confidence': 'High', 'Medium', or 'Low'.\n"
            "- 'reasoning': A brief explanation of your confidence.\n\n"
            "Do not include any markdown formatting (like ```json) in the response, just the raw JSON object.\n\n"
            f"CONTEXT:\n{context_str}\n\n"
            f"USER QUESTION: {query_text}"
        )
        
        # 3. Generate Answer
        raw_response = self.llm.generate(system_prompt)
        
        # 4. Validate output
        validated_response = self.validator.validate(raw_response)
        
        return {
            "query": query_text,
            "answer": validated_response.answer,
            "confidence": validated_response.confidence,
            "reasoning": validated_response.reasoning,
            "sources": [doc['metadata'] for doc in context_docs]
        }
