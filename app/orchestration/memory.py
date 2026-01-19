from typing import List, Dict, Any
from app.db.models import Message

def format_history(messages: List[Message]) -> str:
    """
    Formats a list of SQLAlchemy Message objects into a string for the LLM prompt.
    Limited to last N messages to fit context window.
    """
    formatted = []
    # Take last 5 messages for context
    recent_messages = messages[-5:] 
    
    for msg in recent_messages:
        role = "User" if msg.role == "user" else "Assistant"
        formatted.append(f"{role}: {msg.content}")
        
    return "\n".join(formatted)
