import json
import re
from typing import Optional
from app.core.schemas import RAGResponse
from app.core.logger import logger

class OutputValidator:

    def _fix_json_newlines(self, text: str) -> str:
        """
        Fix unescaped newlines inside JSON string values.
        LLMs often return JSON with literal newlines in strings.
        """
        # This pattern matches content inside JSON string values and escapes newlines
        def escape_newlines_in_strings(match):
            # Get the string content (without quotes)
            content = match.group(1)
            # Escape literal newlines
            content = content.replace('\n', '\\n').replace('\r', '\\r')
            return f'"{content}"'
        
        # Match JSON string values: "..." (handles escaped quotes inside)
        # This is a simplified fix - match strings and escape newlines
        result = text
        
        # First, try to identify and fix the answer field specifically
        # Pattern to match "answer": "content with newlines"
        answer_pattern = r'("answer"\s*:\s*)"([^"]*(?:\\.[^"]*)*)"'
        
        def fix_answer_field(m):
            prefix = m.group(1)
            content = m.group(2)
            # Escape literal newlines in the content
            fixed_content = content.replace('\n', '\\n').replace('\r', '\\r')
            return f'{prefix}"{fixed_content}"'
        
        result = re.sub(answer_pattern, fix_answer_field, result, flags=re.DOTALL)
        
        return result

    def _extract_json(self, text: str) -> str:
        # First try to fix common LLM JSON issues
        text = self._fix_json_newlines(text)
        
        # Remove markdown code fences
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        # Regex to find JSON Object OR List
        match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
        if match:
            return match.group(0)
        return text

    def validate(self, llm_output: str) -> RAGResponse:
        logger.info("Validating LLM output...")
        cleaned_output = self._extract_json(llm_output)
        
        try:
            data = json.loads(cleaned_output)
            
            # Dynamic Handling: If List, wrap it
            if isinstance(data, list):
                logger.info("LLM returned a List. Formatting as bullet points.")
                # Format list as bullets for better readability
                formatted_list = "\n".join([f"- {item}" for item in data])
                return RAGResponse(
                    answer=formatted_list,
                    confidence="Medium",
                    reasoning="Auto-converted from List response."
                )
            
            # If Dict with expected keys
            if isinstance(data, dict):
                # Ensure defaults
                defaults = {
                    "answer": json.dumps(data) if "answer" not in data else data["answer"],
                    "confidence": "Medium",
                    "reasoning": "Standard validation."
                }
                # Update defaults with actual data
                defaults.update({k: v for k, v in data.items() if k in defaults})
                
                logger.info(f"Validation successful. Confidence: {defaults['confidence']}")
                return RAGResponse(**defaults)
                
            # If primitive (str/int/bool)
            return RAGResponse(
                answer=str(data),
                confidence="Low",
                reasoning="Auto-converted from primitive."
            )
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode failed: {e}. Attempting secondary extraction...")
            
            # Secondary extraction: Try to extract answer manually from text
            answer_match = re.search(r'"answer"\s*:\s*"([^"]*)"', llm_output, re.DOTALL)
            if answer_match:
                extracted_answer = answer_match.group(1)
                # Unescape common escape sequences
                extracted_answer = extracted_answer.replace('\\n', '\n').replace('\\r', '\r')
                logger.info("Secondary extraction successful - extracted answer field.")
                return RAGResponse(
                    answer=extracted_answer,
                    confidence="Medium",
                    reasoning="Extracted from partial JSON."
                )
            
            # Try to find any structured list in the response
            list_match = re.findall(r'^\s*\d+\.\s+(.+)$', llm_output, re.MULTILINE)
            if list_match:
                logger.info("Found numbered list in response. Formatting.")
                formatted_list = "\n".join([f"{i+1}. {item}" for i, item in enumerate(list_match)])
                return RAGResponse(
                    answer=formatted_list,
                    confidence="Medium",
                    reasoning="Extracted numbered list from response."
                )
            
            # Final fallback
            logger.warning("Falling back to raw text output.")
            return RAGResponse(
                answer=llm_output.strip(),
                confidence="Low",
                reasoning="Raw output fallback."
            )
            
        except Exception as e:
            logger.error(f"Validation critical failure: {e}")
            # Absolute fallback
            return RAGResponse(
                answer="I encountered an error processing the response.",
                confidence="Low",
                reasoning=f"System Error: {str(e)}"
            )
