import httpx
import json
import sys
import time
from typing import Dict, Any, Optional, Tuple
from backend.config import settings

def log_realtime(message: str, flush: bool = True):
    """Log message and flush immediately for real-time output."""
    print(message, flush=flush)

class DaytonaClient:
    """
    Client for executing code in Daytona sandbox.
    Uses the Daytona SDK for code execution.
    """
    def __init__(self):
        self.api_key = settings.DAYTONA_API_KEY
        self.api_url = settings.DAYTONA_API_URL
        
    async def execute_code(self, code: str, context: Dict[str, Any], timeout: int = 30) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Execute Python code in a Daytona sandbox with provided context.
        
        Args:
            code: Python code string to execute
            context: JSON-serializable context data (will be injected as a variable)
            timeout: Maximum execution time in seconds
            
        Returns:
            Tuple of (parsed_result, execution_trace):
            - parsed_result: Dict containing the parsed JSON result (should match AgentDecision schema)
            - execution_trace: Dict containing execution details (code, raw_output, exit_code, etc.)
            
        Raises:
            Exception if execution fails or times out
        """
        try:
            # Import Daytona SDK (async version)
            log_realtime(f"      📦 Importing Daytona SDK (async)...")
            from daytona import AsyncDaytona, DaytonaConfig
            
            log_realtime(f"      🔧 Initializing Daytona client (async)...")
            # Initialize async client
            config = DaytonaConfig(api_key=self.api_key, api_url=self.api_url)
            daytona = AsyncDaytona(config)
            
            try:
                log_realtime(f"      🏗️  Creating Daytona sandbox...")
                log_realtime(f"      Using API URL: {self.api_url}")
                log_realtime(f"      API key present: {bool(self.api_key)}")
                log_realtime(f"      API key length: {len(self.api_key) if self.api_key else 0}")
                # Create sandbox
                sandbox = await daytona.create()
                log_realtime(f"      ✅ Sandbox created: {sandbox.id}")
            except Exception as create_error:
                error_type = type(create_error).__name__
                error_msg = str(create_error)
                log_realtime(f"      ❌ Sandbox creation failed!")
                log_realtime(f"      Error type: {error_type}")
                log_realtime(f"      Error message: {error_msg[:500]}")
                # Try to get more details if it's an HTTP error
                if hasattr(create_error, 'response'):
                    log_realtime(f"      Response status: {getattr(create_error.response, 'status_code', 'N/A')}")
                    log_realtime(f"      Response headers: {dict(getattr(create_error.response, 'headers', {}))}")
                raise
            
            try:
                # Inject context as JSON in the code
                # The code should expect a `context` variable and assign result to `result`
                context_json = json.dumps(context, default=str)
                log_realtime(f"      📝 Preparing code with context injection...")
                log_realtime(f"      Context size: {len(context_json)} characters")
                
                # Wrap code to ensure it assigns result
                full_code = f"""
import json
context = json.loads('''{context_json}''')

# User's code
{code}

# Ensure result exists
if 'result' not in locals():
    raise ValueError("Code must assign a 'result' variable with the decision")
    
# Output result as JSON
print(json.dumps(result))
"""
                
                log_realtime(f"      🚀 Executing code in sandbox (timeout: {timeout}s)...")
                log_realtime(f"      Code length: {len(full_code)} characters")
                
                # Execute code and track execution time
                start_time = time.time()
                response = await sandbox.process.code_run(full_code)
                execution_time_ms = (time.time() - start_time) * 1000
                
                log_realtime(f"      ✅ Code execution completed")
                log_realtime(f"      Exit code: {response.exit_code}")
                log_realtime(f"      Output length: {len(response.result)} characters")
                log_realtime(f"      Execution time: {execution_time_ms:.2f}ms")
                
                # Build execution trace
                raw_output = response.result
                
                # Try to extract JSON from output first (even if exit code is non-zero)
                # Sometimes code prints JSON successfully but then has an error
                result_text = raw_output.strip()
                log_realtime(f"      📊 Parsing execution result...")
                
                parsed_result = None
                # Try to extract JSON if code printed it
                if result_text.startswith("{") or result_text.startswith("["):
                    try:
                        parsed_result = json.loads(result_text)
                        log_realtime(f"      ✅ Successfully parsed JSON result from start")
                    except json.JSONDecodeError:
                        pass
                
                # If not found at start, try to find JSON anywhere in output
                if parsed_result is None:
                    import re
                    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', result_text, re.DOTALL)
                    if json_match:
                        try:
                            parsed_result = json.loads(json_match.group())
                            log_realtime(f"      ✅ Found and parsed JSON in output")
                        except json.JSONDecodeError:
                            pass
                
                # Determine if execution was successful
                # Success = exit code 0 OR we successfully parsed JSON
                executed_successfully = response.exit_code == 0 or parsed_result is not None
                error_message = None if executed_successfully else raw_output[:1000]  # First 1000 chars of error
                
                execution_trace = {
                    "code": code,  # Store original code, not wrapped code
                    "raw_output": raw_output,
                    "exit_code": response.exit_code,
                    "executed_successfully": executed_successfully,
                    "execution_time_ms": execution_time_ms,
                    "error_message": error_message
                }
                
                # If we successfully parsed JSON, return it even if exit code is non-zero
                if parsed_result is not None:
                    log_realtime(f"      ✅ Execution completed with valid JSON result")
                    if response.exit_code != 0:
                        log_realtime(f"      ⚠️  Note: Exit code was {response.exit_code} but JSON was successfully parsed")
                    return parsed_result, execution_trace
                
                # No JSON found - this is a real failure
                if response.exit_code != 0:
                    log_realtime(f"      ❌ Execution failed!")
                    log_realtime(f"      Exit code: {response.exit_code}")
                    log_realtime(f"      Error output: {raw_output[:500]}")
                    # Return trace even on failure, but raise exception for error handling
                    return None, execution_trace
                
                # Exit code 0 but no JSON - parsing failure
                log_realtime(f"      ❌ No JSON found in output")
                log_realtime(f"      Output preview: {result_text[:200]}...")
                execution_trace["error_message"] = f"Code did not return valid JSON. Output: {result_text[:500]}"
                execution_trace["executed_successfully"] = False
                raise Exception(f"Code did not return valid JSON. Output: {result_text[:500]}")
                        
            finally:
                # Clean up sandbox and close client
                try:
                    if 'sandbox' in locals():
                        log_realtime(f"      🧹 Cleaning up sandbox...")
                        await sandbox.delete()
                        log_realtime(f"      ✅ Sandbox deleted")
                except Exception as cleanup_error:
                    log_realtime(f"      ⚠️  Error cleaning up sandbox: {cleanup_error}")
                finally:
                    try:
                        await daytona.close()
                        log_realtime(f"      ✅ Daytona client closed")
                    except Exception as close_error:
                        log_realtime(f"      ⚠️  Error closing client: {close_error}")
                
        except ImportError:
            raise Exception("Daytona SDK not installed. Run: pip install daytona")
        except Exception as e:
            # Capture detailed error information
            error_type = type(e).__name__
            error_msg = str(e)
            error_repr = repr(e)
            
            # Log detailed error information
            log_realtime(f"      ❌ Daytona error details:")
            log_realtime(f"      Error type: {error_type}")
            log_realtime(f"      Error message: {error_msg[:1000]}")
            
            # Try to extract more details from the exception
            error_details = {
                "type": error_type,
                "message": error_msg,
                "repr": error_repr
            }
            
            # If it's an HTTP error, try to get response details
            if hasattr(e, 'response'):
                try:
                    response = e.response
                    error_details["response_status"] = getattr(response, 'status_code', None)
                    error_details["response_headers"] = dict(getattr(response, 'headers', {}))
                    if hasattr(response, 'text'):
                        error_details["response_text"] = response.text[:500]
                    if hasattr(response, 'json'):
                        try:
                            error_details["response_json"] = response.json()
                        except:
                            pass
                except Exception as detail_error:
                    error_details["detail_error"] = str(detail_error)
            
            # If it has request info, capture that too
            if hasattr(e, 'request'):
                try:
                    request = e.request
                    error_details["request_url"] = str(getattr(request, 'url', 'N/A'))
                    error_details["request_method"] = getattr(request, 'method', 'N/A')
                except:
                    pass
            
            # Log the detailed error info
            log_realtime(f"      Full error details: {json.dumps(error_details, indent=6, default=str)[:1000]}")
            
            # Create execution trace with detailed error
            execution_trace = {
                "code": code,
                "raw_output": json.dumps(error_details, default=str),
                "exit_code": -1,
                "executed_successfully": False,
                "execution_time_ms": None,
                "error_message": f"{error_type}: {error_msg}"
            }
            raise Exception(f"Daytona execution error: {error_type}: {error_msg}")

