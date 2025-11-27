"""Code execution agent with sandboxing."""
import os
import sys
import subprocess
import tempfile
from typing import Tuple, Optional, Dict, Any
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ExecutorAgent:
    """Executes Python code safely with timeout and resource limits."""
    
    def __init__(self):
        self.timeout = 60  # 60 seconds max per execution
        self.work_dir = settings.work_dir
    
    async def execute_code(
        self, 
        code: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str, Any]:
        """
        Execute Python code safely.
        
        Args:
            code: Python code to execute
            context: Optional context variables
            
        Returns:
            Tuple of (success, output/error, result)
        """
        logger.info("Executing Python code")
        logger.debug(f"Code length: {len(code)} characters")
        
        try:
            # Create temporary file for code
            with tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.py', 
                delete=False,
                dir=self.work_dir
            ) as f:
                code_file = f.name
                f.write(code)
            
            # Execute code in subprocess
            result = subprocess.run(
                [sys.executable, code_file],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.work_dir
            )
            
            # Clean up
            os.unlink(code_file)
            
            if result.returncode == 0:
                logger.info("Code executed successfully")
                return True, result.stdout, result.stdout
            else:
                logger.warning(f"Code execution failed with return code {result.returncode}")
                return False, result.stderr, None
                
        except subprocess.TimeoutExpired:
            logger.error(f"Code execution timeout after {self.timeout}s")
            try:
                os.unlink(code_file)
            except:
                pass
            return False, f"Execution timeout after {self.timeout} seconds", None
            
        except Exception as e:
            logger.error(f"Error executing code: {e}")
            try:
                os.unlink(code_file)
            except:
                pass
            return False, str(e), None
    
    async def execute_code_with_output(self, code: str) -> str:
        """
        Execute code and return output as string.
        
        Args:
            code: Python code to execute
            
        Returns:
            Output string
        """
        success, output, _ = await self.execute_code(code)
        return output if success else f"Error: {output}"
    
    async def validate_code_syntax(self, code: str) -> Tuple[bool, str]:
        """
        Validate Python code syntax without executing.
        
        Args:
            code: Python code to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            compile(code, '<string>', 'exec')
            return True, ""
        except SyntaxError as e:
            return False, str(e)
    
    def prepare_code_environment(self, code: str, files: Dict[str, str]) -> str:
        """
        Prepare code with file paths injected.
        
        Args:
            code: Python code
            files: Dictionary of filename: filepath
            
        Returns:
            Code with file paths added
        """
        # Add file path variables at the beginning
        file_vars = "\n".join([
            f"{self._sanitize_varname(filename)} = r'{filepath}'"
            for filename, filepath in files.items()
        ])
        
        if file_vars:
            code = f"# File paths\n{file_vars}\n\n{code}"
        
        # Add work directory
        code = f"import os\nos.chdir(r'{self.work_dir}')\n\n{code}"
        
        return code
    
    def _sanitize_varname(self, filename: str) -> str:
        """Convert filename to valid Python variable name."""
        # Remove extension and convert to valid identifier
        name = os.path.splitext(filename)[0]
        name = name.replace('-', '_').replace(' ', '_').replace('.', '_')
        
        # Ensure it starts with letter or underscore
        if name and not (name[0].isalpha() or name[0] == '_'):
            name = 'file_' + name
        
        return name or 'file_path'
    
    async def extract_result_from_output(self, output: str) -> Any:
        """
        Extract structured result from code output.
        
        Args:
            output: Code execution output
            
        Returns:
            Extracted result
        """
        # Try to parse as JSON
        import json
        
        lines = output.strip().split('\n')
        
        # Try last line first (common pattern)
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            
            try:
                return json.loads(line)
            except:
                pass
            
            # Try to parse as number
            try:
                if '.' in line:
                    return float(line)
                else:
                    return int(line)
            except:
                pass
            
            # Return as string
            return line
        
        return output