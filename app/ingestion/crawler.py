import asyncio
from typing import List, Optional, Tuple
from playwright.async_api import async_playwright, Page, BrowserContext
from app.core.logger import logger
from app.ingestion.models import IngestedDocument, DocumentType, ProcessingStatus
from urllib.parse import urlparse

class SpaceCrawler:
    def __init__(self, headless: bool = True):
        self.headless = headless

    async def crawl_url(self, url: str) -> IngestedDocument:
        """
        Crawls a single URL and returns an IngestedDocument with raw content.
        Does not parse the content yet.
        """
        logger.info(f"Starting crawl for: {url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="SpacePedia-AI-Bot/1.0",
                viewport={"width": 1280, "height": 720}
            )
            page = await context.new_page()
            
            try:
                # Navigate to the page
                response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                if not response or response.status >= 400:
                    logger.error(f"Failed to load page {url}, status: {response.status if response else 'Unknown'}")
                    return self._create_failed_doc(url, f"HTTP Error: {response.status if response else 'Unknown'}")

                # Determine if it's a PDF primarily (checking headers)
                content_type = response.headers.get("content-type", "")
                if "application/pdf" in content_type:
                     # For direct PDF links, we might handle them differently or just download
                     # Playwright doesn't "render" PDFs like HTML.
                     logger.info(f"Detected direct PDF link: {url}")
                     return await self._handle_direct_pdf(page, url)

                # Basic info extraction
                title = await page.title()
                content = await page.content()
                
                # Check for Linked PDFs (heuristic)
                pdf_links = await self._extract_pdf_links(page)
                if pdf_links:
                    logger.info(f"Found {len(pdf_links)} PDF links on {url}")
                    # TODO: add logic to potentially crawl these recursively if needed
                    # For now, we just log them or add to metadata
                
                # Create document
                domain = urlparse(url).netloc
                
                doc = IngestedDocument(
                    url=url,
                    title=title,
                    doc_type=DocumentType.WEB_PAGE,
                    content=content, # Raw HTML
                    source_domain=domain,
                    status=ProcessingStatus.CRAWLED,
                    metadata={"pdf_links": pdf_links}
                )
                
                logger.info(f"Successfully crawled {url}")
                return doc

            except Exception as e:
                logger.exception(f"Error crawling {url}")
                return self._create_failed_doc(url, str(e))
            finally:
                await browser.close()

    async def _extract_pdf_links(self, page: Page) -> List[str]:
        """Extracts hrefs ending in .pdf"""
        return await page.eval_on_selector_all(
            "a[href$='.pdf']", 
            "elements => elements.map(el => el.href)"
        )

    async def _handle_direct_pdf(self, page: Page, url: str) -> IngestedDocument:
        # For direct PDF, we might assume content is empty here and let Parser fetch it via requests/httpx if needed,
        # OR we can try to download it here. For simplicity, we flag it.
        domain = urlparse(url).netloc
        return IngestedDocument(
            url=url,
            title=url.split('/')[-1],
            doc_type=DocumentType.PDF,
            content=None, # Binary content handling depends on pipeline design
            source_domain=domain,
            status=ProcessingStatus.CRAWLED,
            metadata={"is_direct_pdf": True}
        )

    def _create_failed_doc(self, url: str, error: str) -> IngestedDocument:
        domain = urlparse(url).netloc
        return IngestedDocument(
            url=url,
            doc_type=DocumentType.WEB_PAGE,
            source_domain=domain,
            status=ProcessingStatus.FAILED,
            error_message=error
        )
