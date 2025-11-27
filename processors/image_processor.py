"""Image processing and analysis utilities."""
import os
import base64
from typing import Optional, Dict, Any, List
from PIL import Image
import cv2
import numpy as np
try:
    import pytesseract
except ImportError:
    pytesseract = None
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ImageProcessor:
    """Processes images for analysis and OCR."""
    
    def __init__(self):
        self.temp_dir = "/tmp/image_processing"
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def load_image(self, image_path: str) -> Optional[Image.Image]:
        """
        Load an image file.
        
        Args:
            image_path: Path to image file
            
        Returns:
            PIL Image object or None if failed
        """
        try:
            img = Image.open(image_path)
            logger.info(f"Loaded image: {image_path}, Size: {img.size}, Mode: {img.mode}")
            return img
        except Exception as e:
            logger.error(f"Error loading image {image_path}: {e}")
            return None
    
    def extract_text_ocr(self, image_path: str) -> str:
        """
        Extract text from image using OCR.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Extracted text
        """
        if pytesseract is None:
            logger.warning("pytesseract not available, skipping OCR")
            return ""
        
        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            logger.info(f"Extracted {len(text)} characters via OCR")
            return text
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""
    
    def get_image_info(self, image_path: str) -> Dict[str, Any]:
        """
        Get detailed information about an image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with image metadata
        """
        try:
            img = Image.open(image_path)
            
            info = {
                "path": image_path,
                "filename": os.path.basename(image_path),
                "size": img.size,
                "width": img.width,
                "height": img.height,
                "mode": img.mode,
                "format": img.format,
                "file_size_bytes": os.path.getsize(image_path)
            }
            
            return info
        except Exception as e:
            logger.error(f"Error getting image info: {e}")
            return {}
    
    def resize_image(
        self, 
        image_path: str, 
        max_size: tuple = (1024, 1024),
        output_path: Optional[str] = None
    ) -> str:
        """
        Resize image to fit within max dimensions.
        
        Args:
            image_path: Path to input image
            max_size: Maximum (width, height)
            output_path: Path for output (or auto-generate)
            
        Returns:
            Path to resized image
        """
        try:
            img = Image.open(image_path)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            if output_path is None:
                name, ext = os.path.splitext(os.path.basename(image_path))
                output_path = os.path.join(self.temp_dir, f"{name}_resized{ext}")
            
            img.save(output_path)
            logger.info(f"Resized image saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error resizing image: {e}")
            return image_path
    
    def encode_image_base64(self, image_path: str) -> str:
        """
        Encode image to base64 string.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded string with data URI
        """
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            base64_str = base64.b64encode(image_data).decode('utf-8')
            
            # Determine MIME type from extension
            ext = image_path.lower().split('.')[-1]
            mime_types = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'bmp': 'image/bmp',
                'webp': 'image/webp'
            }
            mime_type = mime_types.get(ext, 'image/jpeg')
            
            return f"data:{mime_type};base64,{base64_str}"
            
        except Exception as e:
            logger.error(f"Error encoding image to base64: {e}")
            return ""
    
    def convert_to_grayscale(self, image_path: str, output_path: Optional[str] = None) -> str:
        """Convert image to grayscale."""
        try:
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            if output_path is None:
                name, ext = os.path.splitext(os.path.basename(image_path))
                output_path = os.path.join(self.temp_dir, f"{name}_gray{ext}")
            
            cv2.imwrite(output_path, gray)
            return output_path
        except Exception as e:
            logger.error(f"Error converting to grayscale: {e}")
            return image_path
    
    def detect_text_regions(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Detect regions containing text in an image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            List of detected text regions with bounding boxes
        """
        if pytesseract is None:
            logger.warning("pytesseract not available")
            return []
        
        try:
            img = Image.open(image_path)
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            
            regions = []
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 0:  # Valid detection
                    regions.append({
                        'text': data['text'][i],
                        'confidence': data['conf'][i],
                        'bbox': {
                            'x': data['left'][i],
                            'y': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i]
                        }
                    })
            
            return regions
        except Exception as e:
            logger.error(f"Error detecting text regions: {e}")
            return []
    
    def enhance_for_ocr(self, image_path: str) -> str:
        """
        Enhance image for better OCR results.
        
        Args:
            image_path: Path to input image
            
        Returns:
            Path to enhanced image
        """
        try:
            img = cv2.imread(image_path)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply thresholding
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Denoise
            denoised = cv2.fastNlMeansDenoising(thresh)
            
            # Save enhanced image
            name, ext = os.path.splitext(os.path.basename(image_path))
            output_path = os.path.join(self.temp_dir, f"{name}_enhanced{ext}")
            cv2.imwrite(output_path, denoised)
            
            logger.info(f"Enhanced image for OCR: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error enhancing image: {e}")
            return image_path