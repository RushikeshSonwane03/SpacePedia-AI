"""
LLM Client Module

Provides LLMClient class supporting Groq and Gemini providers.
Cloud-only architecture: Groq (primary) or Gemini (fallback).
"""

from app.core.config import settings
from app.core.logger import logger


class LLMClient:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        
        if self.provider == "groq":
            try:
                from langchain_groq import ChatGroq
            except ImportError:
                logger.error("langchain-groq not installed. Please run: pip install langchain-groq")
                raise ImportError("Missing Groq dependency")

            if not settings.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY is missing in environment variables.")

            self.llm = ChatGroq(
                api_key=settings.GROQ_API_KEY,
                model_name=settings.GROQ_MODEL,
                temperature=0.7,
                max_tokens=1024
            )
            logger.info(f"LLM Initialized: Groq ({settings.GROQ_MODEL})")
            
        elif self.provider == "gemini":
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
            except ImportError:
                logger.error("langchain-google-genai not installed. Please run: pip install langchain-google-genai")
                raise ImportError("Missing Gemini dependency")

            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is missing in environment variables.")

            self.llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.7,
                convert_system_message_to_human=True
            )
            logger.info(f"LLM Initialized: Google Gemini ({settings.GEMINI_MODEL})")
        
        else:
            raise ValueError(
                f"Unsupported LLM_PROVIDER: {self.provider}. "
                f"Supported: 'groq', 'gemini'"
            )

    def generate(self, prompt: str) -> str:
        """
        Generates a response from the LLM.
        """
        try:
            response = self.llm.invoke(prompt)
            
            # Both ChatGroq and ChatGoogleGenerativeAI return AIMessage
            if hasattr(response, 'content'):
                return response.content
            return str(response)
            
        except Exception as e:
            logger.error(f"LLM generation failed ({self.provider}): {e}")
            raise e
