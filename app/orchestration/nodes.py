from typing import Dict, Any
from app.orchestration.state import AgentState
from app.rag.retriever import Retriever
from app.rag.llm import LLMClient
from app.rag.validator import OutputValidator
from app.core.logger import logger

retriever = Retriever()
llm = LLMClient()
validator = OutputValidator()

def retrieve(state: AgentState) -> dict:
    logger.info("---RETRIEVE---")
    question = state["question"]
    documents = retriever.retrieve(question, k=3) # Faster processing
    return {"documents": documents, "question": question}

def grade_documents(state: AgentState) -> dict:
    logger.info("---GRADE DOCUMENTS (BATCH)---")
    question = state["question"]
    documents = state["documents"]
    
    if not documents:
        return {"documents": [], "question": question}

    # Construct batch prompt
    doc_strings = []
    for i, doc in enumerate(documents):
        doc_strings.append(f"Document {i}: {doc['text'][:300]}...") # Shorter context for grading
    
    docs_context = "\n\n".join(doc_strings)
    
    prompt = (
        f"You are a grader assessing relevance of retrieved documents to the user question: '{question}'\n\n"
        f"{docs_context}\n\n"
        "Return a JSON object with a single key 'relevant_indices' containing a list of integer indices (0-based) for documents that are relevant.\n"
        "Example: {\"relevant_indices\": [0, 2]}\n"
        "If none are relevant, return {\"relevant_indices\": []}.\n"
        "Do NOT include any explanation, only the JSON."
    )
    
    try:
        response = llm.generate(prompt)
        # Clean response potential markdown
        response = response.replace("```json", "").replace("```", "").strip()
        import json
        data = json.loads(response)
        indices = data.get("relevant_indices", [])
        
        filtered_docs = [documents[i] for i in indices if 0 <= i < len(documents)]
        logger.info(f"Batch Grading: Kept {len(filtered_docs)}/{len(documents)} documents (Indices: {indices})")
        
        # Fallback: If grading filtered EVERYTHING out, but we had docs, keep them.
        # This prevents "I couldn't find info" when the grader is too strict or hallucinates emptiness.
        if not filtered_docs and documents:
            logger.warning("Grading filtered out all documents. Falling back to original retrieval set.")
            filtered_docs = documents
        
    except Exception as e:
        logger.warning(f"Batch grading failed ({e}), keeping all documents as fallback.")
        filtered_docs = documents

    return {"documents": filtered_docs, "question": question}

def generate(state: AgentState) -> dict:
    logger.info("---GENERATE---")
    question = state["question"]
    documents = state["documents"]
    
    if not documents:
        return {
            "generation": "I'm sorry, I couldn't find any relevant information in my database to answer your question.",
            "confidence": "Low",
            "reasoning": "No relevant documents found after grading."
        }

    context_str = "\n\n".join([doc['text'] for doc in documents])
    
    # Get history if available
    history_str = state.get("chat_history", "No previous history.")

    # Reuse the prompt logic from RAGEngine but structured for the graph
    system_prompt = (
        "You are SpacePedia AI, an expert on space exploration.\n"
        "Use the provided context and conversation history to answer the user's question.\n"
        "You MUST return your response in valid JSON format with the following keys:\n"
        "- 'answer': The direct answer (markdown supported: lists, code blocks, bolding).\n"
        "- 'confidence': 'High', 'Medium', or 'Low'.\n"
        "- 'reasoning': A brief explanation of your confidence.\n\n"
        "Do not include any markdown formatting (like ```json) OUTSIDE the JSON object. Just the raw JSON.\n\n"
        f"CONTEXT:\n{context_str}\n\n"
        f"HISTORY:\n{history_str}\n\n"
        f"USER QUESTION: {question}"
    )
    
    raw_response = llm.generate(system_prompt)
    validated = validator.validate(raw_response)
    
    return {
        "generation": validated.answer,
        "confidence": validated.confidence,
        "reasoning": validated.reasoning
    }
