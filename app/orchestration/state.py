from typing import TypedDict, List
from app.ingestion.models import IngestedDocument

class AgentState(TypedDict):
    question: str
    chat_history: List[dict] # formatted history or list of messages
    documents: List[dict] 
    generation: str
    confidence: str
    reasoning: str
