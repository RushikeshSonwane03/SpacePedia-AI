import re
import unicodedata
from app.ingestion.models import IngestedDocument, ProcessingStatus
from app.core.logger import logger

class TextNormalizer:
    def normalize(self, doc: IngestedDocument) -> IngestedDocument:
        """
        Normalizes the text content of the document.
        """
        logger.info(f"Normalizing document: {doc.url}")
        
        try:
            if not doc.content:
                logger.warning(f"No content to normalize for {doc.url}")
                return doc

            text = doc.content
            
            # 1. Unicode normalization
            text = unicodedata.normalize('NFKC', text)
            
            # 2. Whitespace normalization
            # Replace multiple newlines with single newline, but respect paragraph breaks?
            # Strategy: Replace 3+ newlines with 2 (paragraph break)
            # Replace runs of spaces with single space
            
            lines = text.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line:
                    # Replace multiple spaces within line
                    line = re.sub(r'\s+', ' ', line)
                    cleaned_lines.append(line)
            
            # Join with newlines
            text = '\n'.join(cleaned_lines)
            
            # 3. Basic cleaning (noise removal) can go here
            
            doc.content = text
            doc.status = ProcessingStatus.NORMALIZED
            return doc

        except Exception as e:
            logger.exception(f"Error normalizing document {doc.url}")
            doc.status = ProcessingStatus.FAILED
            doc.error_message = str(e)
            return doc
