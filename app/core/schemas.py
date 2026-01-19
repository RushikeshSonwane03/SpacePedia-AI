from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union

class RAGResponse(BaseModel):
    answer: str = Field(..., description="The direct answer to the user's question")
    confidence: str = Field(..., description="Confidence level: High, Medium, or Low")
    reasoning: Optional[str] = Field(None, description="Brief explanation of why this answer was chosen")

    @field_validator('answer', mode='before')
    @classmethod
    def convert_answer(cls, v):
        """Convert list/dict answers to formatted strings."""
        if isinstance(v, list):
            # Format list as numbered items
            if all(isinstance(item, str) for item in v):
                return "\n".join([f"{i+1}. {item}" for i, item in enumerate(v)])
            else:
                # Nested structure - format as bullet points
                return "\n".join([f"- {str(item)}" for item in v])
        elif isinstance(v, dict):
            # Format dict as key-value pairs
            return "\n".join([f"**{k}**: {v}" for k, v in v.items()])
        elif v is None:
            return "No answer available."
        return str(v)

    @field_validator('confidence', mode='before')
    @classmethod
    def convert_confidence(cls, v):
        """Convert numeric confidence values to string labels."""
        if isinstance(v, (int, float)):
            # Convert numeric to categorical
            if v >= 0.8:
                return "High"
            elif v >= 0.5:
                return "Medium"
            else:
                return "Low"
        # Handle string variations
        if isinstance(v, str):
            v_lower = v.lower().strip()
            if v_lower in ['high', 'medium', 'low']:
                return v.capitalize()
            # Try to parse as number
            try:
                num = float(v)
                if num >= 0.8:
                    return "High"
                elif num >= 0.5:
                    return "Medium"
                else:
                    return "Low"
            except ValueError:
                pass
        return str(v) if v else "Medium"

    @field_validator('reasoning', mode='before')
    @classmethod
    def convert_reasoning(cls, v):
        """Ensure reasoning is always a string."""
        if v is None:
            return None
        return str(v)
