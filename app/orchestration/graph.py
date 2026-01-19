from langgraph.graph import StateGraph, END
from app.orchestration.state import AgentState
from app.orchestration.nodes import retrieve, grade_documents, generate

class GraphManager:
    def __init__(self):
        self.workflow = StateGraph(AgentState)
        
        # Define Nodes
        self.workflow.add_node("retrieve", retrieve)
        self.workflow.add_node("grade_documents", grade_documents)
        self.workflow.add_node("generate", generate)
        
        # Define Edges
        self.workflow.set_entry_point("retrieve")
        self.workflow.add_edge("retrieve", "grade_documents")
        self.workflow.add_edge("grade_documents", "generate")
        self.workflow.add_edge("generate", END)
        
        # Compile
        self.app = self.workflow.compile()
        
    def invoke(self, question: str, chat_history: str = "") -> dict:
        inputs = {"question": question, "chat_history": chat_history}
        # Invoke the graph
        result = self.app.invoke(inputs)
        return {
            "answer": result.get("generation"),
            "confidence": result.get("confidence"),
            "reasoning": result.get("reasoning"),
            "documents": result.get("documents", [])
        }
