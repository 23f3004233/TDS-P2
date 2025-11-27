"""Orchestrator agent - coordinates the entire quiz-solving process."""
import asyncio
import httpx
from typing import Optional, List, Dict, Any
from app.models import (
    QuizRequest, 
    QuizTask, 
    AnswerSubmission, 
    AnswerResponse,
    AnalysisResult,
    VerificationResult
)
from app.config import settings
from app.utils.timer import QuizTimer
from app.utils.logger import get_logger
from agents.fetcher import FetcherAgent
from agents.analyzer import AnalyzerAgent
from agents.verifier import VerifierAgent

logger = get_logger(__name__)


class OrchestratorAgent:
    """Orchestrates the complete quiz-solving workflow."""
    
    def __init__(self):
        self.fetcher = FetcherAgent()
        self.analyzer = AnalyzerAgent()
        self.verifier = VerifierAgent()
        self.max_retries = settings.max_retries
        self.enable_verification = settings.enable_verification
    
    async def process_quiz(self, request: QuizRequest):
        """
        Process complete quiz chain.
        
        Args:
            request: Initial quiz request
        """
        logger.info(f"=== Starting quiz processing for {request.email} ===")
        logger.info(f"Initial URL: {request.url}")
        
        # Start timer
        timer = QuizTimer()
        
        # Track quiz chain
        current_url = request.url
        quiz_number = 1
        
        while current_url and timer.should_continue():
            logger.info(f"\n{'='*60}")
            logger.info(f"Quiz #{quiz_number}: {current_url}")
            logger.info(f"{'='*60}\n")
            
            timer.log_status(f"Quiz #{quiz_number}")
            
            try:
                # Fetch quiz
                quiz_task = await self.fetcher.fetch_quiz_page(current_url)
                
                if not timer.should_continue():
                    logger.warning("Timer expiring, submitting best attempt")
                
                # Solve quiz with verification loop
                answer = await self._solve_quiz_with_verification(
                    quiz_task, 
                    request, 
                    timer
                )
                
                # Submit answer
                next_url = await self._submit_answer(
                    quiz_task, 
                    answer, 
                    request,
                    timer
                )
                
                # Move to next quiz
                if next_url:
                    current_url = next_url
                    quiz_number += 1
                    logger.info(f"Moving to next quiz: {next_url}")
                else:
                    logger.info("Quiz chain complete!")
                    break
                    
            except Exception as e:
                logger.error(f"Error processing quiz #{quiz_number}: {e}")
                break
        
        elapsed = timer.elapsed()
        logger.info(f"\n=== Quiz processing complete ===")
        logger.info(f"Total time: {elapsed:.2f}s")
        logger.info(f"Quizzes completed: {quiz_number}")
    
    async def _solve_quiz_with_verification(
        self, 
        quiz_task: QuizTask, 
        request: QuizRequest,
        timer: QuizTimer
    ) -> Any:
        """
        Solve quiz with analyzer-verifier loop.
        
        Args:
            quiz_task: Quiz to solve
            request: Original request
            timer: Quiz timer
            
        Returns:
            Final answer
        """
        logger.info("Starting solver loop")
        
        analysis_result = None
        attempt = 0
        max_refinement_iterations = 2
        
        # Initial analysis
        analysis_result = await self.analyzer.analyze(
            quiz_task, 
            attempt=attempt
        )
        
        logger.info(f"Initial answer: {analysis_result.answer}")
        logger.info(f"Confidence: {analysis_result.confidence}")
        
        # Verification loop (if enabled and time permits)
        if self.enable_verification and timer.has_buffer_time():
            for iteration in range(max_refinement_iterations):
                if not timer.should_continue():
                    logger.warning("No time for verification, using current answer")
                    break
                
                logger.info(f"Verification iteration {iteration + 1}")
                
                # Get verification
                verification = await self.verifier.verify(
                    quiz_task,
                    analysis_result,
                    {}  # Files already processed in analyzer
                )
                
                if verification.approved:
                    logger.info("Solution verified successfully!")
                    break
                
                if verification.feedback:
                    logger.info(f"Feedback received: {verification.feedback[:200]}...")
                    
                    # Refine solution
                    attempt += 1
                    analysis_result = await self.analyzer.analyze(
                        quiz_task,
                        attempt=attempt,
                        previous_feedback=verification.feedback
                    )
                    
                    logger.info(f"Refined answer: {analysis_result.answer}")
                else:
                    logger.info("No feedback provided, using current answer")
                    break
        
        return analysis_result.answer
    
    async def _submit_answer(
        self, 
        quiz_task: QuizTask, 
        answer: Any, 
        request: QuizRequest,
        timer: QuizTimer
    ) -> Optional[str]:
        """
        Submit answer to quiz system.
        
        Args:
            quiz_task: Quiz task
            answer: Answer to submit
            request: Original request
            timer: Quiz timer
            
        Returns:
            Next quiz URL if any
        """
        submit_url = quiz_task.submit_url
        if not submit_url:
            logger.error("No submit URL found!")
            return None
        
        logger.info(f"Submitting answer to: {submit_url}")
        logger.info(f"Answer: {answer}")
        
        # Prepare submission
        submission = AnswerSubmission(
            email=request.email,
            secret=request.secret,
            url=quiz_task.url,
            answer=answer
        )
        
        # Submit with retries
        for retry in range(self.max_retries):
            if not timer.should_continue() and retry > 0:
                logger.warning("No time for retries")
                break
            
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.post(
                        submit_url,
                        json=submission.dict()
                    )
                    
                    logger.info(f"Response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        logger.info(f"Response: {result}")
                        
                        if result.get("correct"):
                            logger.info("✓ Answer correct!")
                            return result.get("url")  # Next quiz URL
                        else:
                            reason = result.get("reason", "No reason provided")
                            logger.warning(f"✗ Answer incorrect: {reason}")
                            
                            # Check if we got a next URL anyway
                            next_url = result.get("url")
                            if next_url:
                                logger.info("Received next URL despite incorrect answer")
                                return next_url
                            
                            # Retry if we have time
                            if retry < self.max_retries - 1:
                                logger.info(f"Retrying ({retry + 1}/{self.max_retries})...")
                                # Could potentially re-analyze here with the reason
                                await asyncio.sleep(1)
                                continue
                            else:
                                logger.warning("Max retries reached")
                                return None
                    else:
                        logger.error(f"HTTP {response.status_code}: {response.text}")
                        return None
                        
            except Exception as e:
                logger.error(f"Error submitting answer: {e}")
                if retry < self.max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                return None
        
        return None