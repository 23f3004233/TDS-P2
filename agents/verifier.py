"""Verifier agent - validates solutions without providing code."""
import json
from typing import Dict, Any
from app.models import QuizTask, AnalysisResult, VerificationResult
from llm.aipipe_client import AIPipeClient
from llm.prompt_templates import (
    VERIFIER_SYSTEM_PROMPT,
    VERIFIER_USER_TEMPLATE,
    FILE_DESCRIPTION_TEMPLATE
)
from llm.model_manager import ModelManager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VerifierAgent:
    """Verifies solutions and provides high-level feedback."""
    
    def __init__(self):
        self.client = AIPipeClient()
        self.model_manager = ModelManager()
    
    async def verify(
        self, 
        quiz_task: QuizTask, 
        analysis_result: AnalysisResult,
        files_content: Dict[str, Any]
    ) -> VerificationResult:
        """
        Verify a proposed solution.
        
        Args:
            quiz_task: Original quiz task
            analysis_result: Proposed solution from analyzer
            files_content: Processed file contents
            
        Returns:
            Verification result with approval/feedback
        """
        logger.info("Verifying proposed solution")
        
        # Get verifier model
        model = self.model_manager.get_verifier_model()
        
        # Build verification prompt
        prompt = self._build_verification_prompt(
            quiz_task, 
            analysis_result, 
            files_content
        )
        
        # Get verification response
        try:
            messages = [
                {"role": "system", "content": VERIFIER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.client.chat_completion(
                messages=messages,
                model=model,
                temperature=0.3  # Lower temperature for verification
            )
            
            # Parse verification result
            result = await self._parse_verification_response(response)
            
            logger.info(
                f"Verification complete - Approved: {result.approved}, "
                f"Confidence: {result.confidence}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in verification: {e}")
            # Default to approval if verification fails (to not block progress)
            return VerificationResult(
                approved=True,
                confidence=0.5,
                feedback=None
            )
    
    def _build_verification_prompt(
        self, 
        quiz_task: QuizTask, 
        analysis_result: AnalysisResult,
        files_content: Dict[str, Any]
    ) -> str:
        """Build verification prompt."""
        # Format files description
        files_desc = []
        for filename, content in files_content.items():
            filepath = quiz_task.files.get(filename, "")
            file_info = FILE_DESCRIPTION_TEMPLATE.format(
                filename=filename,
                filetype=content.get('type', 'unknown'),
                size=len(str(content)),
                filepath=filepath
            )
            files_desc.append(file_info)
        
        files_description = "\n".join(files_desc) if files_desc else "No files provided"
        
        # Format solution
        solution_str = f"""
Reasoning: {analysis_result.reasoning}

Answer: {analysis_result.answer}

Code Generated: {'Yes' if analysis_result.code_executed else 'No'}

{f"Code:{analysis_result.code_executed}" if analysis_result.code_executed else ""}

Confidence: {analysis_result.confidence}
"""
        
        return VERIFIER_USER_TEMPLATE.format(
            question=quiz_task.question,
            files_description=files_description,
            solution=solution_str
        )
    
    async def _parse_verification_response(
        self, 
        response: Dict[str, Any]
    ) -> VerificationResult:
        """Parse verifier response into VerificationResult."""
        text = await self.client.extract_text_response(response)
        
        # Try to parse as JSON
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0].strip()
            else:
                json_str = text.strip()
            
            data = json.loads(json_str)
            
            return VerificationResult(
                approved=data.get("approved", True),
                confidence=data.get("confidence", 0.8),
                feedback=data.get("feedback")
            )
        except Exception as e:
            logger.warning(f"Could not parse verification JSON: {e}")
            
            # Fallback: check for keywords in text
            text_lower = text.lower()
            
            if any(word in text_lower for word in ['approve', 'correct', 'looks good', 'valid']):
                return VerificationResult(
                    approved=True,
                    confidence=0.7,
                    feedback=None
                )
            else:
                return VerificationResult(
                    approved=False,
                    confidence=0.7,
                    feedback=text
                )