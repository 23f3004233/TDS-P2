"""AIPipe API client for LLM interactions."""
import base64
import httpx
from typing import List, Dict, Any, Optional, Union
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AIPipeClient:
    """Client for interacting with AIPipe API."""
    
    def __init__(self):
        self.token = settings.aipipe_token
        self.base_url = settings.aipipe_base_url
        self.openai_url = settings.aipipe_openai_url
        self.timeout = settings.request_timeout
        
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Make a chat completion request.
        
        Args:
            messages: List of message dicts with role and content
            model: Model identifier (e.g., 'openai/gpt-4o')
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            timeout: Request timeout (default: from config)
            
        Returns:
            API response dict
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            async with httpx.AsyncClient(timeout=timeout or self.timeout) as client:
                logger.info(f"Requesting completion from model: {model}")
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                # Extract and log usage
                if "usage" in result:
                    usage = result["usage"]
                    logger.info(
                        f"Model: {model} - Tokens: {usage.get('total_tokens', 'N/A')}"
                    )
                
                return result
                
        except httpx.TimeoutException:
            logger.error(f"Timeout requesting {model}")
            raise
        except httpx.HTTPError as e:
            logger.error(f"HTTP error from {model}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error with {model}: {e}")
            raise
    
    def encode_image_base64(self, image_path: str) -> str:
        """
        Encode image to base64 string.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded string
        """
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    async def vision_completion(
        self,
        prompt: str,
        image_paths: List[str],
        model: str = "openai/gpt-4o",
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Make a vision completion request with images.
        
        Args:
            prompt: Text prompt
            image_paths: List of image file paths
            model: Vision model identifier
            timeout: Request timeout
            
        Returns:
            API response dict
        """
        # Build message content with images
        content = [{"type": "text", "text": prompt}]
        
        for img_path in image_paths:
            # Determine image type from extension
            ext = img_path.lower().split('.')[-1]
            media_type = f"image/{ext}" if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp'] else "image/jpeg"
            
            base64_image = self.encode_image_base64(img_path)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{media_type};base64,{base64_image}"
                }
            })
        
        messages = [{"role": "user", "content": content}]
        
        return await self.chat_completion(
            messages=messages,
            model=model,
            timeout=timeout or 60  # Vision requests may take longer
        )
    
    async def extract_text_response(self, response: Dict[str, Any]) -> str:
        """
        Extract text content from API response.
        
        Args:
            response: API response dict
            
        Returns:
            Extracted text content
        """
        try:
            if "choices" in response and len(response["choices"]) > 0:
                choice = response["choices"][0]
                if "message" in choice:
                    message = choice["message"]
                    if "content" in message:
                        return message["content"]
            
            logger.error(f"Unexpected response format: {response}")
            return ""
        except Exception as e:
            logger.error(f"Error extracting text from response: {e}")
            return ""
    
    async def count_tokens_estimate(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation).
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Rough estimate: ~4 characters per token
        return len(text) // 4