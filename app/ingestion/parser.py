import fitz  # PyMuPDF
from bs4 import BeautifulSoup
from typing import Optional
from app.ingestion.models import IngestedDocument, DocumentType, ProcessingStatus
from app.core.logger import logger
import requests
import io

class DocumentParser:
    def parse(self, doc: IngestedDocument) -> IngestedDocument:
        """
        Parses the raw content of the document and extracts text.
        Updates doc.content with the extracted text.
        """
        logger.info(f"Parsing document: {doc.url} ({doc.doc_type})")
        
        try:
            if doc.doc_type == DocumentType.WEB_PAGE:
                doc.content = self._parse_html(doc.content)
            elif doc.doc_type == DocumentType.PDF:
                # If content is None (direct link), we might need to fetch it first
                # In a real pipeline, Crawler might have fetched bytes.
                # Here we assume we might need to download if content is missing.
                if not doc.content: 
                     doc.content = self._fetch_and_parse_pdf(doc.url)
                else:
                    # If content was passed as bytes/string, handle accordingly
                    pass 
            
            doc.status = ProcessingStatus.PARSED
            return doc
            
        except Exception as e:
            logger.exception(f"Error parsing document {doc.url}")
            doc.status = ProcessingStatus.FAILED
            doc.error_message = str(e)
            return doc

    def _parse_html(self, html_content: str) -> str:
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove scripts and styles
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        text = soup.get_text(separator='\n')
        return text

    def _fetch_and_parse_pdf(self, url: str) -> str:
        logger.info(f"Downloading PDF from {url}")
        response = requests.get(url)
        response.raise_for_status()
        
        with fitz.open(stream=response.content, filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()
        
        return text
