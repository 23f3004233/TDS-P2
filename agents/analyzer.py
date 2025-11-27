"""Analyzer agent - primary AI solver."""
import json
from typing import Dict, Any, Optional, List
from app.models import QuizTask, AnalysisResult
from app.config import settings
from llm.aipipe_client import AIPipeClient
from llm.prompt_templates import (
    ANALYZER_SYSTEM_PROMPT,
    ANALYZER_USER_TEMPLATE,
    REFINEMENT_PROMPT,
    FILE_DESCRIPTION_TEMPLATE
)
from llm.model_manager import ModelManager, TaskType
from agents.executor import ExecutorAgent
from processors.pdf_processor import PDFProcessor
from processors.image_processor import ImageProcessor
from processors.audio_processor import AudioProcessor
from processors.video_processor import VideoProcessor
from processors.data_processor import DataProcessor
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AnalyzerAgent:
    """Primary AI agent that solves quiz questions."""
    
    def __init__(self):
        self.client = AIPipeClient()
        self.model_manager = ModelManager()
        self.executor = ExecutorAgent()
        
        # Initialize processors
        self.pdf_processor = PDFProcessor()
        self.image_processor = ImageProcessor()
        self.audio_processor = AudioProcessor()
        self.video_processor = VideoProcessor()
        self.data_processor = DataProcessor()
    
    async def analyze(
        self, 
        quiz_task: QuizTask, 
        attempt: int = 0,
        previous_feedback: Optional[str] = None
    ) -> AnalysisResult:
        """
        Analyze quiz and provide solution.
        
        Args:
            quiz_task: Quiz task to solve
            attempt: Attempt number for model selection
            previous_feedback: Feedback from verifier for refinement
            
        Returns:
            Analysis result with answer
        """
        logger.info(f"Analyzing quiz (attempt {attempt})")
        
        # Detect task type
        task_type = self.model_manager.detect_task_type(
            quiz_task.question, 
            quiz_task.files
        )
        logger.info(f"Detected task type: {task_type.value}")
        
        # Select appropriate model
        model = self.model_manager.get_model_for_task(task_type, attempt)
        
        # Process files
        files_content = await self._process_files(quiz_task.files, task_type)
        
        # Build prompt
        if previous_feedback:
            prompt = self._build_refinement_prompt(
                quiz_task, 
                files_content, 
                previous_feedback
            )
        else:
            prompt = self._build_initial_prompt(quiz_task, files_content)
        
        # Get AI response
        try:
            response = await self._get_ai_response(model, prompt, task_type, quiz_task.files)
            
            # Parse response
            result = await self._parse_response(response, quiz_task)
            
            # Execute code if needed
            if result.code_executed:
                result = await self._execute_and_refine(result, quiz_task)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in analysis: {e}")
            # Return error result
            return AnalysisResult(
                answer="Error",
                confidence=0.0,
                reasoning=f"Analysis failed: {str(e)}",
                code_executed=None
            )
    
    async def _process_files(
        self, 
        files: Dict[str, str], 
        task_type: TaskType
    ) -> Dict[str, Any]:
        """Process all files and extract relevant information."""
        files_content = {}
        
        for filename, filepath in files.items():
            logger.info(f"Processing file: {filename}")
            
            try:
                ext = filename.lower().split('.')[-1]
                
                if ext == 'pdf':
                    content = await self._process_pdf(filepath)
                elif ext in ['csv', 'xlsx', 'xls']:
                    content = await self._process_data_file(filepath, ext)
                elif ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
                    content = await self._process_image(filepath, task_type)
                elif ext in ['mp3', 'wav', 'ogg', 'm4a']:
                    content = await self._process_audio(filepath)
                elif ext in ['mp4', 'avi', 'mov', 'mkv']:
                    content = await self._process_video(filepath)
                elif ext in ['json', 'txt']:
                    content = await self._process_text_file(filepath)
                else:
                    content = {"error": f"Unsupported file type: {ext}"}
                
                files_content[filename] = content
                
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")
                files_content[filename] = {"error": str(e)}
        
        return files_content
    
    async def _process_pdf(self, filepath: str) -> Dict[str, Any]:
        """Process PDF file."""
        page_texts = self.pdf_processor.extract_text(filepath)
        tables = self.pdf_processor.extract_tables(filepath)
        page_count = self.pdf_processor.get_page_count(filepath)
        
        return {
            "type": "pdf",
            "page_count": page_count,
            "pages": page_texts,
            "tables": tables,
            "path": filepath
        }
    
    async def _process_data_file(self, filepath: str, ext: str) -> Dict[str, Any]:
        """Process CSV or Excel file."""
        if ext == 'csv':
            df = self.data_processor.load_csv(filepath)
        else:
            df = self.data_processor.load_excel(filepath)
        
        if df is None:
            return {"error": "Could not load data file"}
        
        info = self.data_processor.get_data_info(df)
        preview = df.head(10).to_dict('records')
        
        return {
            "type": "data",
            "format": ext,
            "info": info,
            "preview": preview,
            "path": filepath
        }
    
    async def _process_image(self, filepath: str, task_type: TaskType) -> Dict[str, Any]:
        """Process image file."""
        info = self.image_processor.get_image_info(filepath)
        ocr_text = ""
        
        # Extract text if likely to contain text
        if task_type == TaskType.VISION:
            ocr_text = self.image_processor.extract_text_ocr(filepath)
        
        return {
            "type": "image",
            "info": info,
            "ocr_text": ocr_text,
            "path": filepath
        }
    
    async def _process_audio(self, filepath: str) -> Dict[str, Any]:
        """Process audio file."""
        info = self.audio_processor.get_audio_info(filepath)
        transcript = self.audio_processor.transcribe_speech_recognition(filepath)
        
        return {
            "type": "audio",
            "info": info,
            "transcript": transcript,
            "path": filepath
        }
    
    async def _process_video(self, filepath: str) -> Dict[str, Any]:
        """Process video file."""
        info = self.video_processor.get_video_info(filepath)
        
        # Extract a few frames
        frames = self.video_processor.extract_frames(filepath, num_frames=5)
        
        # Extract audio
        audio_path = self.video_processor.extract_audio(filepath)
        
        return {
            "type": "video",
            "info": info,
            "frames": frames,
            "audio_path": audio_path,
            "path": filepath
        }
    
    async def _process_text_file(self, filepath: str) -> Dict[str, Any]:
        """Process text or JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to parse as JSON
            try:
                json_data = json.loads(content)
                return {"type": "json", "data": json_data, "path": filepath}
            except:
                return {"type": "text", "content": content, "path": filepath}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _build_initial_prompt(
        self, 
        quiz_task: QuizTask, 
        files_content: Dict[str, Any]
    ) -> str:
        """Build initial analysis prompt."""
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
        
        # Format file contents
        files_content_str = json.dumps(files_content, indent=2, default=str)
        
        return ANALYZER_USER_TEMPLATE.format(
            question=quiz_task.question,
            files_description=files_description,
            files_content=files_content_str,
            context=f"Submit URL: {quiz_task.submit_url or 'Not specified'}"
        )
    
    def _build_refinement_prompt(
        self, 
        quiz_task: QuizTask, 
        files_content: Dict[str, Any], 
        feedback: str
    ) -> str:
        """Build refinement prompt based on feedback."""
        return REFINEMENT_PROMPT.format(
            feedback=feedback,
            question=quiz_task.question,
            previous_answer="See previous attempt"
        )
    
    async def _get_ai_response(
        self, 
        model: str, 
        prompt: str, 
        task_type: TaskType,
        files: Dict[str, str]
    ) -> Dict[str, Any]:
        """Get response from AI model."""
        messages = [
            {"role": "system", "content": ANALYZER_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        
        # Use vision model if images are involved
        if task_type == TaskType.VISION and files:
            image_files = [
                f for f in files.values() 
                if f.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))
            ]
            if image_files:
                response = await self.client.vision_completion(
                    prompt=prompt,
                    image_paths=image_files[:5],  # Limit to 5 images
                    model=model
                )
            else:
                response = await self.client.chat_completion(messages, model)
        else:
            response = await self.client.chat_completion(messages, model)
        
        return response
    
    async def _parse_response(
        self, 
        response: Dict[str, Any], 
        quiz_task: QuizTask
    ) -> AnalysisResult:
        """Parse AI response into AnalysisResult."""
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
            
            return AnalysisResult(
                answer=data.get("answer"),
                confidence=data.get("confidence", 0.8),
                reasoning=data.get("reasoning", ""),
                code_executed=data.get("code")
            )
        except Exception as e:
            logger.warning(f"Could not parse JSON response: {e}")
            # Return text as-is
            return AnalysisResult(
                answer=text,
                confidence=0.5,
                reasoning="Direct response without JSON format",
                code_executed=None
            )
    
    async def _execute_and_refine(
        self, 
        result: AnalysisResult, 
        quiz_task: QuizTask
    ) -> AnalysisResult:
        """Execute code and refine result."""
        if not result.code_executed:
            return result
        
        logger.info("Executing generated code")
        
        # Prepare code with file paths
        code = self.executor.prepare_code_environment(
            result.code_executed, 
            quiz_task.files
        )
        
        # Execute
        success, output, extracted = await self.executor.execute_code(code)
        
        if success:
            # Extract result from output
            final_result = await self.executor.extract_result_from_output(output)
            result.answer = final_result
            logger.info(f"Code execution successful: {final_result}")
        else:
            logger.error(f"Code execution failed: {output}")
            result.confidence *= 0.5  # Reduce confidence
        
        return result