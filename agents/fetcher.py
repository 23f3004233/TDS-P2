"""Content fetcher agent using Playwright for JavaScript rendering."""
import os
import re
import asyncio
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import httpx
from bs4 import BeautifulSoup
from app.config import settings
from app.models import QuizTask
from app.utils.logger import get_logger

logger = get_logger(__name__)


class FetcherAgent:
    """Fetches and processes quiz content including JS-rendered pages."""
    
    def __init__(self):
        self.work_dir = settings.work_dir
        self.timeout = settings.browser_timeout * 1000  # Convert to milliseconds
        
    async def fetch_quiz_page(self, url: str) -> QuizTask:
        """
        Fetch quiz page with JavaScript rendering.
        
        Args:
            url: Quiz page URL
            
        Returns:
            QuizTask with extracted content
        """
        logger.info(f"Fetching quiz page: {url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            try:
                # Navigate to page
                await page.goto(url, wait_until="networkidle", timeout=self.timeout)
                
                # Wait for content to render
                await page.wait_for_timeout(2000)  # Additional 2s for JS execution
                
                # Get rendered HTML
                html_content = await page.content()
                
                # Extract text content
                text_content = await page.evaluate("() => document.body.innerText")
                
                await browser.close()
                
                # Parse the content
                quiz_task = self._parse_quiz_content(url, html_content, text_content)
                
                # Download any referenced files
                await self._download_files(quiz_task)
                
                return quiz_task
                
            except PlaywrightTimeout:
                logger.error(f"Timeout loading page: {url}")
                await browser.close()
                raise
            except Exception as e:
                logger.error(f"Error fetching quiz page: {e}")
                await browser.close()
                raise
    
    def _parse_quiz_content(self, url: str, html: str, text: str) -> QuizTask:
        """Parse quiz HTML to extract question and file URLs."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract question text
        question = self._extract_question(text, soup)
        
        # Extract file URLs
        file_urls = self._extract_file_urls(soup, url)
        
        # Extract submit URL
        submit_url = self._extract_submit_url(text, soup)
        
        quiz_task = QuizTask(
            url=url,
            question=question,
            files={},
            submit_url=submit_url,
            raw_html=html
        )
        
        # Store file URLs for download
        quiz_task._file_urls = file_urls
        
        logger.info(f"Parsed quiz - Question length: {len(question)}, Files: {len(file_urls)}")
        return quiz_task
    
    def _extract_question(self, text: str, soup: BeautifulSoup) -> str:
        """Extract the question from page content."""
        # Try to find question in structured format
        question_elem = soup.find(id="result")
        if question_elem:
            return question_elem.get_text(strip=True)
        
        # Otherwise, use the full text content
        return text.strip()
    
    def _extract_file_urls(self, soup: BeautifulSoup, base_url: str) -> Dict[str, str]:
        """Extract file download URLs from page."""
        file_urls = {}
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Make absolute URL
            if href.startswith('http'):
                full_url = href
            else:
                full_url = self._make_absolute_url(base_url, href)
            
            # Check if it's a file
            if self._is_file_url(full_url):
                filename = self._extract_filename(full_url, link.get_text())
                file_urls[filename] = full_url
        
        return file_urls
    
    def _extract_submit_url(self, text: str, soup: BeautifulSoup) -> Optional[str]:
        """Extract the submit URL from page content."""
        # Look for "Post your answer to" pattern
        patterns = [
            r'Post your answer to\s+(https?://[^\s]+)',
            r'submit.*?to\s+(https?://[^\s]+)',
            r'Submit URL:\s*(https?://[^\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Look in structured elements
        for elem in soup.find_all(['code', 'pre']):
            match = re.search(r'https?://[^\s"\']+/submit', elem.get_text())
            if match:
                return match.group(0)
        
        logger.warning("Could not find submit URL in page")
        return None
    
    def _is_file_url(self, url: str) -> bool:
        """Check if URL points to a downloadable file."""
        file_extensions = [
            '.pdf', '.csv', '.xlsx', '.xls', '.json', '.txt',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
            '.mp3', '.wav', '.ogg', '.m4a',
            '.mp4', '.avi', '.mov', '.mkv',
            '.zip', '.tar', '.gz', '.py', '.ipynb'
        ]
        
        url_lower = url.lower()
        return any(url_lower.endswith(ext) for ext in file_extensions)
    
    def _extract_filename(self, url: str, link_text: str) -> str:
        """Extract filename from URL or link text."""
        # Try to get from URL path
        path = url.split('?')[0]  # Remove query parameters
        filename = os.path.basename(path)
        
        if filename and '.' in filename:
            return filename
        
        # Use link text if available
        if link_text and link_text.strip():
            return link_text.strip().replace(' ', '_')
        
        # Generate filename from URL
        return f"file_{abs(hash(url))}"
    
    def _make_absolute_url(self, base_url: str, relative_url: str) -> str:
        """Convert relative URL to absolute."""
        from urllib.parse import urljoin
        return urljoin(base_url, relative_url)
    
    async def _download_files(self, quiz_task: QuizTask):
        """Download all files referenced in the quiz."""
        if not hasattr(quiz_task, '_file_urls'):
            return
        
        file_urls = quiz_task._file_urls
        
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            for filename, url in file_urls.items():
                try:
                    logger.info(f"Downloading file: {filename} from {url}")
                    
                    response = await client.get(url)
                    response.raise_for_status()
                    
                    # Save file
                    filepath = os.path.join(self.work_dir, filename)
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    quiz_task.files[filename] = filepath
                    logger.info(f"Saved file: {filepath}")
                    
                except Exception as e:
                    logger.error(f"Error downloading {filename}: {e}")
        
        # Clean up temporary attribute
        delattr(quiz_task, '_file_urls')
    
    async def download_file(self, url: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Download a single file from URL.
        
        Args:
            url: File URL
            filename: Optional custom filename
            
        Returns:
            Path to downloaded file
        """
        if filename is None:
            filename = os.path.basename(url.split('?')[0])
        
        filepath = os.path.join(self.work_dir, filename)
        
        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Downloaded file: {filepath}")
                return filepath
                
        except Exception as e:
            logger.error(f"Error downloading file from {url}: {e}")
            return None