"""PDF processing utilities."""
import os
from typing import Dict, List, Optional, Any
import pdfplumber
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PDFProcessor:
    """Processes PDF files for text extraction and analysis."""
    
    def __init__(self):
        self.temp_dir = "/tmp/pdf_processing"
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def extract_text(self, pdf_path: str) -> Dict[int, str]:
        """
        Extract text from all pages of a PDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary mapping page number to text content
        """
        try:
            page_texts = {}
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    page_texts[page_num] = text
                    logger.info(
                        f"Extracted {len(text)} characters from page {page_num}"
                    )
            
            return page_texts
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            # Fallback to PyPDF2
            return self._extract_text_pypdf2(pdf_path)
    
    def _extract_text_pypdf2(self, pdf_path: str) -> Dict[int, str]:
        """Fallback text extraction using PyPDF2."""
        try:
            page_texts = {}
            reader = PdfReader(pdf_path)
            
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                page_texts[page_num] = text
            
            return page_texts
        except Exception as e:
            logger.error(f"PyPDF2 extraction also failed: {e}")
            return {}
    
    def extract_tables(self, pdf_path: str, page_num: Optional[int] = None) -> List[List[List[Any]]]:
        """
        Extract tables from PDF pages.
        
        Args:
            pdf_path: Path to PDF file
            page_num: Specific page number (1-indexed), or None for all pages
            
        Returns:
            List of tables, where each table is a list of rows
        """
        try:
            all_tables = []
            
            with pdfplumber.open(pdf_path) as pdf:
                pages = [pdf.pages[page_num - 1]] if page_num else pdf.pages
                
                for page in pages:
                    tables = page.extract_tables()
                    if tables:
                        all_tables.extend(tables)
                        logger.info(f"Extracted {len(tables)} tables from page")
            
            return all_tables
            
        except Exception as e:
            logger.error(f"Error extracting tables from PDF: {e}")
            return []
    
    def convert_to_images(self, pdf_path: str, dpi: int = 200) -> List[str]:
        """
        Convert PDF pages to images.
        
        Args:
            pdf_path: Path to PDF file
            dpi: Resolution for conversion
            
        Returns:
            List of image file paths
        """
        try:
            images = convert_from_path(pdf_path, dpi=dpi)
            image_paths = []
            
            for i, image in enumerate(images, start=1):
                image_path = os.path.join(
                    self.temp_dir, 
                    f"{os.path.basename(pdf_path)}_page_{i}.png"
                )
                image.save(image_path, 'PNG')
                image_paths.append(image_path)
                logger.info(f"Converted page {i} to image: {image_path}")
            
            return image_paths
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")
            return []
    
    def get_page_count(self, pdf_path: str) -> int:
        """Get number of pages in PDF."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                return len(pdf.pages)
        except:
            try:
                reader = PdfReader(pdf_path)
                return len(reader.pages)
            except Exception as e:
                logger.error(f"Error getting page count: {e}")
                return 0
    
    def extract_page(self, pdf_path: str, page_num: int) -> Dict[str, Any]:
        """
        Extract comprehensive information from a specific page.
        
        Args:
            pdf_path: Path to PDF file
            page_num: Page number (1-indexed)
            
        Returns:
            Dictionary with text, tables, and metadata
        """
        try:
            result = {
                "page_number": page_num,
                "text": "",
                "tables": [],
                "has_images": False
            }
            
            with pdfplumber.open(pdf_path) as pdf:
                if page_num > len(pdf.pages):
                    logger.warning(f"Page {page_num} does not exist")
                    return result
                
                page = pdf.pages[page_num - 1]
                
                # Extract text
                result["text"] = page.extract_text() or ""
                
                # Extract tables
                result["tables"] = page.extract_tables() or []
                
                # Check for images
                result["has_images"] = len(page.images) > 0
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting page {page_num}: {e}")
            return {"page_number": page_num, "text": "", "tables": [], "has_images": False}
    
    def search_text(self, pdf_path: str, search_term: str) -> List[Dict[str, Any]]:
        """
        Search for text across all pages.
        
        Args:
            pdf_path: Path to PDF file
            search_term: Text to search for
            
        Returns:
            List of matches with page numbers and context
        """
        matches = []
        page_texts = self.extract_text(pdf_path)
        
        for page_num, text in page_texts.items():
            if search_term.lower() in text.lower():
                # Find context around the match
                idx = text.lower().find(search_term.lower())
                start = max(0, idx - 100)
                end = min(len(text), idx + len(search_term) + 100)
                context = text[start:end]
                
                matches.append({
                    "page": page_num,
                    "context": context,
                    "position": idx
                })
        
        return matches