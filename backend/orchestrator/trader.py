import json
import sys
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from backend.models import IntervalContext, AgentDecision, DecisionEnum, CodeExecutionTrace
from backend.llm.client import LLMClient
from backend.daytona.daytona_client import DaytonaClient

def log_realtime(message: str, flush: bool = True):
    """Log message and flush immediately for real-time output."""
    print(message, flush=flush)

class TraderAgent:
    """
    Agent responsible for making trading decisions based on market context.
    Generates Python code that analyzes the context and returns a decision.
    Features iterative error correction and code explanation.
    """
    def __init__(self, llm_client: LLMClient, daytona_client: DaytonaClient, max_retries: int = 3):
        self.llm = llm_client
        self.daytona = daytona_client
        self.max_retries = max_retries

    async def make_decision(
        self, 
        context: IntervalContext, 
        model: str = "openai/gpt-4o-mini",
        simulation_index: int = 0,
        mode: Optional[str] = None
    ) -> AgentDecision:
        """
        Generate a decision using iterative Daytona agent mode or direct LLM.
        Falls back to direct LLM if all retries fail or mode is DIRECT_LLM.
        """
        from backend.models import ExperimentMode
        
        # If mode is DIRECT_LLM, skip Daytona entirely
        if mode == ExperimentMode.DIRECT_LLM.value:
            log_realtime(f"\n    🔵 Using DIRECT_LLM mode (skipping Daytona)")
            return await self._direct_llm_decision(context, model, simulation_index, fallback=False)
        
        # Try iterative Daytona first
        log_realtime(f"\n    🚀 Starting Daytona Agent Mode (max {self.max_retries} attempts)")
        try:
            return await self._iterative_daytona_decision(context, model, simulation_index)
        except Exception as e:
            log_realtime(f"\n    ⚠️  All Daytona attempts failed: {e}")
            log_realtime(f"    🔄 Falling back to direct LLM...")
            return await self._direct_llm_decision(context, model, simulation_index, fallback=True)

    async def _iterative_daytona_decision(
        self, 
        context: IntervalContext, 
        model: str,
        simulation_index: int
    ) -> AgentDecision:
        """
        Iteratively generate and refine code until it executes successfully.
        Includes error feedback loop and code explanation.
        """
        code = None
        execution_history = []  # Track attempts for explanation
        
        for attempt in range(1, self.max_retries + 1):
            try:
                # Generate or refine code
                if attempt == 1:
                    # First attempt: generate fresh code
                    log_realtime(f"\n    🔵 STEP 1: Generating Python code using LLM ({model})...")
                    code = await self._generate_decision_code(context, model, previous_errors=None)
                    log_realtime(f"    ✅ Code generated: {len(code)} characters")
                    log_realtime(f"\n    📝 Generated Code Preview (first 20 lines):")
                    log_realtime(self._format_code_preview(code, max_lines=20))
                else:
                    # Subsequent attempts: refine based on errors
                    last_error = execution_history[-1].get("error")
                    log_realtime(f"\n    🔄 STEP 1 (Retry {attempt}): Refining code based on error...")
                    log_realtime(f"    Previous error: {last_error[:200]}...")
                    code = await self._refine_code(context, model, code, last_error, execution_history)
                    log_realtime(f"    ✅ Refined code: {len(code)} characters")
                    log_realtime(f"\n    📝 Refined Code Preview (first 20 lines):")
                    log_realtime(self._format_code_preview(code, max_lines=20))
                
                # Prepare context for code execution
                log_realtime(f"\n    🔵 STEP 2: Preparing context for code execution...")
                context_dict = self._prepare_context_dict(context)
                log_realtime(f"    ✅ Context prepared:")
                log_realtime(f"      - Market: {context.market_info.get('title', 'N/A')}")
                log_realtime(f"      - Current Price: {context.current_market_state.price:.2%}")
                log_realtime(f"      - News Articles: {len(context.news)}")
                log_realtime(f"      - Timestamp: {context.time}")
                
                # Execute in Daytona
                log_realtime(f"\n    🔵 STEP 3: Executing code in Daytona sandbox...")
                log_realtime(f"    ⏳ Waiting for execution...")
                execution_result, execution_trace_dict = await self.daytona.execute_code(code, context_dict)
                
                # Handle execution failure (exit code != 0)
                if execution_result is None:
                    execution_trace_dict["attempt_number"] = attempt
                    execution_history.append({
                        "attempt": attempt,
                        "code": code,
                        "error": execution_trace_dict.get("error_message", "Execution failed"),
                        "output": None,
                        "trace": execution_trace_dict
                    })
                    log_realtime(f"    ❌ Execution failed!")
                    log_realtime(f"    Error: {execution_trace_dict.get('error_message', 'Unknown error')[:200]}...")
                    if attempt == self.max_retries:
                        raise Exception(f"Code execution failed: {execution_trace_dict.get('error_message', 'Unknown error')}")
                    else:
                        log_realtime(f"    🔄 Retrying (attempt {attempt + 1}/{self.max_retries})...")
                        continue
                
                log_realtime(f"    ✅ Execution completed!")
                log_realtime(f"    Execution time: {execution_trace_dict.get('execution_time_ms', 0):.2f}ms")
                log_realtime(f"    Raw output length: {len(execution_trace_dict.get('raw_output', ''))} characters")
                log_realtime(f"\n    📊 Execution Result:")
                log_realtime(f"      {json.dumps(execution_result, indent=6)}")
                
                # Validate output structure
                log_realtime(f"\n    🔵 STEP 4: Validating output structure...")
                validation_error = self._validate_output(execution_result)
                if validation_error:
                    execution_trace_dict["attempt_number"] = attempt
                    execution_history.append({
                        "attempt": attempt,
                        "code": code,
                        "error": validation_error,
                        "output": execution_result,
                        "trace": execution_trace_dict
                    })
                    log_realtime(f"    ⚠️  Validation failed: {validation_error}")
                    log_realtime(f"    🔄 Will retry with refined code...")
                    continue  # Try again
                log_realtime(f"    ✅ Output validation passed!")
                
                # Success! Get explanation of what the code did
                log_realtime(f"\n    🔵 STEP 5: Generating explanation of code execution...")
                explanation = await self._explain_code_execution(
                    code, execution_result, context, model
                )
                log_realtime(f"    ✅ Explanation generated ({len(explanation)} characters)")
                
                # Build execution trace object
                execution_trace_dict["attempt_number"] = attempt
                execution_trace = CodeExecutionTrace(**execution_trace_dict)
                
                # Build decision with explanation and trace
                log_realtime(f"\n    🔵 STEP 6: Building final decision object...")
                decision = AgentDecision(
                    decision=DecisionEnum(execution_result.get("decision", "NO")),
                    confidence=float(execution_result.get("confidence", 0.5)),
                    rationale=self._build_rationale_with_explanation(
                        execution_result.get("rationale", ""),
                        explanation,
                        attempt,
                        execution_history
                    ),
                    relevant_evidence_ids=execution_result.get("relevant_evidence_ids", []),
                    execution_trace=execution_trace
                )
                
                log_realtime(f"\n    ✅✅✅ Attempt {attempt} SUCCEEDED!")
                log_realtime(f"    📈 Final Decision:")
                log_realtime(f"       Decision: {decision.decision.value}")
                log_realtime(f"       Confidence: {decision.confidence:.2%}")
                log_realtime(f"       Evidence IDs: {len(decision.relevant_evidence_ids)}")
                log_realtime(f"       Rationale length: {len(decision.rationale)} characters")
                return decision
                
            except Exception as e:
                error_msg = str(e)
                import traceback
                error_trace = traceback.format_exc()
                
                # Create a minimal execution trace for the failed attempt
                failed_trace_dict = {
                    "code": code if code else "",
                    "raw_output": error_trace,
                    "exit_code": -1,
                    "executed_successfully": False,
                    "execution_time_ms": None,
                    "error_message": error_msg,
                    "attempt_number": attempt
                }
                
                execution_history.append({
                    "attempt": attempt,
                    "code": code,
                    "error": error_msg,
                    "output": None,
                    "trace": failed_trace_dict
                })
                log_realtime(f"\n    ❌ Attempt {attempt} execution failed!")
                log_realtime(f"    Error: {error_msg}")
                log_realtime(f"    Traceback:\n{error_trace}")
                
                if attempt == self.max_retries:
                    # Last attempt failed, raise to trigger fallback
                    log_realtime(f"\n    ⚠️  All {self.max_retries} attempts exhausted. Falling back to direct LLM...")
                    raise Exception(f"All {self.max_retries} attempts failed. Last error: {error_msg}")
                else:
                    log_realtime(f"    🔄 Retrying (attempt {attempt + 1}/{self.max_retries})...")
        
        # Should never reach here, but just in case
        raise Exception("Iterative decision failed without raising exception")
    
    def _format_code_preview(self, code: str, max_lines: int = 10) -> str:
        """Format code for display, showing first few lines."""
        lines = code.split('\n')
        preview_lines = lines[:max_lines]
        preview = '\n'.join([f"      {i+1:3d}: {line}" for i, line in enumerate(preview_lines)])
        if len(lines) > max_lines:
            preview += f"\n      ... ({len(lines) - max_lines} more lines)"
        return preview
    
    def _prepare_context_dict(self, context: IntervalContext) -> Dict[str, Any]:
        """Prepare context dictionary for code execution."""
        return {
            "time": context.time.isoformat(),
            "market": context.market_info,
            "current_price": context.current_market_state.price,
            "news": [
                {
                    "id": snippet.id,
                    "title": snippet.title,
                    "url": snippet.url,
                    "text": snippet.text[:500],  # Truncate for context window
                    "published_date": snippet.published_date,
                    "score": snippet.score
                }
                for snippet in context.news
            ],
            "recent_history": [
                {
                    "timestamp": state.timestamp.isoformat(),
                    "price": state.price
                }
                for state in context.recent_history
            ]
        }
    
    def _validate_output(self, output: Dict[str, Any]) -> Optional[str]:
        """Validate that the output has the required structure. Returns error message if invalid."""
        if not isinstance(output, dict):
            return "Output is not a dictionary"
        
        if "decision" not in output:
            return "Missing 'decision' field"
        
        decision = output.get("decision")
        if decision not in ["YES", "NO"]:
            return f"Invalid decision value: {decision}. Must be 'YES' or 'NO'"
        
        if "confidence" not in output:
            return "Missing 'confidence' field"
        
        try:
            confidence = float(output.get("confidence"))
            if not (0.0 <= confidence <= 1.0):
                return f"Confidence must be between 0.0 and 1.0, got {confidence}"
        except (ValueError, TypeError):
            return f"Confidence must be a number, got {type(output.get('confidence'))}"
        
        return None  # Valid
    
    async def _refine_code(
        self,
        context: IntervalContext,
        model: str,
        previous_code: str,
        error_message: str,
        execution_history: list
    ) -> str:
        """Use LLM to refine code based on previous errors."""
        
        system_prompt = (
            "You are debugging Python code that failed to execute properly. "
            "Your task is to fix the code based on the error message and execution history. "
            "Return ONLY the corrected Python code, no explanations."
        )
        
        history_summary = "\n".join([
            f"Attempt {h['attempt']}: {h.get('error', 'Unknown error')}"
            for h in execution_history[-3:]  # Last 3 attempts
        ])
        
        # Truncate error message to avoid OpenRouter 400 errors (HTML content can be very long)
        truncated_error = error_message[:500] if error_message else "Unknown error"
        if len(error_message) > 500:
            truncated_error += "... (truncated)"
        
        user_prompt = (
            f"The following code failed to execute:\n\n"
            f"```python\n{previous_code[:2000]}\n```\n\n"
            f"Error: {truncated_error}\n\n"
            f"Execution History:\n{history_summary}\n\n"
            f"Market Context:\n"
            f"- Market: {context.market_info.get('title', 'Unknown')}\n"
            f"- Current Price: {context.current_market_state.price:.2%}\n"
            f"- News Articles: {len(context.news)}\n\n"
            "Fix the code to:\n"
            "1. Execute without errors\n"
            "2. Return a JSON object with: decision (YES/NO), confidence (0.0-1.0), rationale (string), relevant_evidence_ids (list)\n"
            "3. Use the `context` variable which contains all market data\n\n"
            "Return ONLY the corrected Python code."
        )
        
        code = await self.llm.generate_text(model, system_prompt, user_prompt)
        
        # Clean up markdown code blocks
        if code.startswith("```python"):
            code = code[9:]
        elif code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]
        
        return code.strip()
    
    async def _explain_code_execution(
        self,
        code: str,
        execution_result: Dict[str, Any],
        context: IntervalContext,
        model: str
    ) -> str:
        """Ask the LLM to explain what the code did and its outcome."""
        
        system_prompt = (
            "You are analyzing code execution results. "
            "Explain what the code computed and how it arrived at its decision. "
            "Be concise but informative."
        )
        
        user_prompt = (
            f"Code that was executed:\n```python\n{code[:1000]}\n```\n\n"
            f"Execution Result:\n{json.dumps(execution_result, indent=2)}\n\n"
            f"Market Context:\n"
            f"- Market: {context.market_info.get('title')}\n"
            f"- Current Price: {context.current_market_state.price:.2%}\n"
            f"- News Articles Analyzed: {len(context.news)}\n\n"
            "Explain:\n"
            "1. What analysis the code performed\n"
            "2. What factors influenced the decision\n"
            "3. How the confidence score was determined\n"
            "4. What evidence was considered most relevant"
        )
        
        explanation = await self.llm.generate_text(model, system_prompt, user_prompt)
        return explanation.strip()
    
    def _build_rationale_with_explanation(
        self,
        original_rationale: str,
        explanation: str,
        successful_attempt: int,
        execution_history: list
    ) -> str:
        """Combine original rationale with code execution explanation."""
        
        rationale_parts = [
            f"## Decision Rationale\n{original_rationale}\n",
            f"## Code Execution Analysis\n{explanation}\n"
        ]
        
        if successful_attempt > 1:
            rationale_parts.append(
                f"## Execution Notes\n"
                f"This decision required {successful_attempt} attempts. "
                f"The code was refined based on previous execution errors."
            )
        
        return "\n".join(rationale_parts)

    async def _generate_decision_code(
        self, 
        context: IntervalContext, 
        model: str,
        previous_errors: Optional[list] = None
    ) -> str:
        """Generate Python code that analyzes context and returns a decision."""
        
        system_prompt = (
            "You are an expert trading agent analyzing prediction markets. "
            "You will receive market context and news articles. "
            "Write Python code that analyzes this information and returns a decision. "
            "The code must be robust and handle edge cases."
        )
        
        user_prompt = (
            f"Market: {context.market_info.get('title', 'Unknown')}\n"
            f"Description: {context.market_info.get('description', 'N/A')}\n"
            f"Current Price (YES probability): {context.current_market_state.price:.2%}\n"
            f"Time: {context.time.isoformat()}\n"
            f"Number of news articles: {len(context.news)}\n\n"
            "Write Python code that:\n"
            "1. Analyzes the market context and news articles\n"
            "2. Determines if the event will happen (YES) or not (NO)\n"
            "3. Assigns a confidence score (0.0 to 1.0)\n"
            "4. Provides a rationale explaining the decision\n"
            "5. Lists IDs/URLs of the most relevant evidence\n\n"
            "The code should assign a dictionary to a variable named `result` with this exact structure:\n"
            'result = {"decision": "YES" or "NO", "confidence": 0.0-1.0, "rationale": "explanation", "relevant_evidence_ids": ["id1", "id2"]}\n\n'
            "Your code should use the `context` variable which contains all the data. "
            "Make sure to handle cases where news might be empty or context fields might be missing."
        )
        
        # Use LLM to generate code (not JSON, but actual Python code)
        code = await self.llm.generate_text(model, system_prompt, user_prompt)
        
        # Clean up markdown code blocks if present
        if code.startswith("```python"):
            code = code[9:]
        elif code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]
            
        return code.strip()

    async def _direct_llm_decision(
        self, 
        context: IntervalContext, 
        model: str,
        simulation_index: int,
        fallback: bool = False
    ) -> AgentDecision:
        """Fallback: Direct LLM call without code execution."""
        
        fallback_note = " (fallback from Daytona)" if fallback else ""
        
        system_prompt = (
            "You are an expert trading agent analyzing prediction markets. "
            "Analyze the market context and news to make a decision."
        )
        
        user_prompt = (
            f"Market: {context.market_info.get('title')}\n"
            f"Description: {context.market_info.get('description', 'N/A')}\n"
            f"Current Price (YES probability): {context.current_market_state.price:.2%}\n"
            f"Time: {context.time.isoformat()}\n"
            f"News Articles:\n"
        )
        
        for snippet in context.news[:5]:  # Limit to top 5
            user_prompt += f"- [{snippet.published_date}] {snippet.title}\n  {snippet.text[:200]}...\n\n"
        
        user_prompt += (
            "Return your decision as JSON with: decision (YES/NO), confidence (0-1), "
            "rationale (explanation), relevant_evidence_ids (list of URLs/IDs)."
        )
        
        if fallback:
            user_prompt += "\n\nNote: This is a fallback decision after code execution failed."
        
        result = await self.llm.generate_json(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=AgentDecision
        )
        
        if fallback:
            result.rationale = f"[Fallback Mode] {result.rationale}"
        
        log_realtime(f"\n    ✅ Direct LLM Decision Generated:")
        log_realtime(f"       Decision: {result.decision.value}")
        log_realtime(f"       Confidence: {result.confidence:.2%}")
        log_realtime(f"       Evidence IDs: {len(result.relevant_evidence_ids)}")
        return result

