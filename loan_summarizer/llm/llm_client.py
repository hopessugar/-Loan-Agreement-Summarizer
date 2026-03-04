"""LLM client for Hugging Face API communication."""

import os
import asyncio
import json
from typing import Dict, Any, Optional
from huggingface_hub import InferenceClient

try:
    from json_repair import repair_json
    JSON_REPAIR_AVAILABLE = True
except ImportError:
    JSON_REPAIR_AVAILABLE = False


class LLMClient:
    """Client for interacting with Hugging Face Inference API with structured output support."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "meta-llama/Llama-3.2-3B-Instruct"):
        """
        Initialize the LLM client.
        
        Args:
            api_key: Hugging Face API key. If None, reads from HUGGINGFACE_API_KEY environment variable.
            model: Hugging Face model to use for generation.
            
        Raises:
            ValueError: If API key is not provided and not found in environment.
        """
        self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Hugging Face API key not found. Please set the HUGGINGFACE_API_KEY environment variable "
                "or pass it as an argument."
            )
        
        self.model_name = model
        self.client = InferenceClient(token=self.api_key)
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay for exponential backoff in seconds
    
    async def generate_structured_output(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: float = 0.1,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Generate structured output from Hugging Face API with JSON schema constraint.
        
        Args:
            prompt: The prompt to send to the LLM.
            schema: JSON schema to constrain the output format.
            temperature: Sampling temperature (0.0 to 2.0).
            max_tokens: Maximum tokens in the response.
            
        Returns:
            Dictionary containing the structured output from the LLM.
            
        Raises:
            Exception: If API call fails after all retries or encounters non-retryable error.
        """
        for attempt in range(self.max_retries):
            try:
                # Add instruction to return JSON in the prompt
                json_prompt = f"{prompt}\n\nIMPORTANT: Return ONLY valid JSON matching the schema, no other text or markdown formatting."
                
                # Use chat completion for better model support
                messages = [
                    {
                        "role": "user",
                        "content": json_prompt
                    }
                ]
                
                # Generate content using Hugging Face Inference API
                response = await asyncio.to_thread(
                    self.client.chat_completion,
                    messages=messages,
                    model=self.model_name,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                # Extract and parse the JSON response
                content = response.choices[0].message.content.strip()
                
                if not content:
                    raise ValueError("Empty response from Hugging Face API")
                
                # Try to extract JSON from markdown code blocks if present
                if content.startswith("```"):
                    # Remove markdown code block formatting
                    lines = content.split("\n")
                    content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
                    content = content.replace("```json", "").replace("```", "").strip()
                
                try:
                    result = json.loads(content)
                except json.JSONDecodeError as e:
                    # Try to fix common JSON issues
                    import re
                    
                    # Extract JSON from the response
                    start_idx = content.find("{")
                    end_idx = content.rfind("}")
                    
                    if start_idx != -1:
                        # If no closing brace found (truncated), use entire content from start
                        if end_idx == -1 or end_idx < start_idx:
                            fixed_content = content[start_idx:]
                        else:
                            fixed_content = content[start_idx:end_idx + 1]
                        
                        # Fix 1: Add comma after closing quote if followed by opening quote (newline)
                        fixed_content = re.sub(r'"\s*\n\s*"', '",\n"', fixed_content)
                        
                        # Fix 2: Add comma after closing quote if followed by opening quote (same line)
                        fixed_content = re.sub(r'"\s+"', '", "', fixed_content)
                        
                        # Fix 3: Add comma after value if followed by new field without comma
                        # Matches: "value" "field": or "value"\n"field":
                        fixed_content = re.sub(r'(["\d])\s*\n?\s*("[\w_]+"\s*:)', r'\1,\n\2', fixed_content)
                        
                        # Fix 4: Ensure proper comma after string values before next key
                        # Pattern: "value" followed by "key": without comma
                        fixed_content = re.sub(r'("(?:[^"\\]|\\.)*")\s+("[\w_]+"\s*:)', r'\1, \2', fixed_content)
                        
                        # Fix 5: Handle the specific case of missing comma after field value
                        # Pattern: "field": "value" "next_field": (missing comma between value and next field)
                        fixed_content = re.sub(r':\s*"([^"]*?)"\s+"', r': "\1", "', fixed_content)
                        
                        # Fix 6: Handle missing comma after field value with newline
                        # Pattern: "field": "value"\n"next_field":
                        fixed_content = re.sub(r':\s*"([^"]*?)"\s*\n\s*"', r': "\1",\n"', fixed_content)
                        
                        # Fix 7: More aggressive - find all field:value pairs and ensure commas
                        # This catches cases where previous patterns missed
                        # Pattern: "field": "value" followed by "next_field": without comma
                        lines = fixed_content.split('\n')
                        for i in range(len(lines) - 1):
                            # If current line ends with a quoted value and next line starts with a quoted field
                            if lines[i].strip().endswith('"') and not lines[i].strip().endswith('",'):
                                if lines[i+1].strip().startswith('"') and ':' in lines[i+1]:
                                    # Add comma to current line
                                    lines[i] = lines[i].rstrip() + ','
                        fixed_content = '\n'.join(lines)
                        
                        # Fix 8: Handle truncated JSON - ensure it ends properly
                        if not fixed_content.rstrip().endswith("}"):
                            # Count open and close braces
                            open_braces = fixed_content.count("{")
                            close_braces = fixed_content.count("}")
                            
                            # If there are unclosed braces, close them
                            if open_braces > close_braces:
                                # First, try to close any open string
                                if fixed_content.count('"') % 2 != 0:
                                    fixed_content += '"'
                                
                                # Then close the braces
                                fixed_content += "}" * (open_braces - close_braces)
                        
                        # Try parsing the fixed content
                        try:
                            result = json.loads(fixed_content)
                        except json.JSONDecodeError as e2:
                            # Try json-repair library as last resort
                            if JSON_REPAIR_AVAILABLE:
                                try:
                                    repaired = repair_json(fixed_content)
                                    result = json.loads(repaired)
                                except Exception:
                                    # json-repair also failed, try truncation handling
                                    result = self._handle_truncated_json(fixed_content, content, e, e2)
                            else:
                                # json-repair not available, try truncation handling
                                result = self._handle_truncated_json(fixed_content, content, e, e2)
                    else:
                        raise ValueError(
                            f"Failed to parse JSON response: {e}\n"
                            f"No JSON object found in response\n"
                            f"Response: {content[:500]}"
                        )
                
                return result
                
            except json.JSONDecodeError as e:
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise ValueError(f"Failed to parse JSON after {self.max_retries} attempts: {e}")
            
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check for rate limiting
                if "rate limit" in error_msg or "429" in error_msg:
                    if attempt < self.max_retries - 1:
                        delay = self.base_delay * (2 ** attempt)
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise Exception(
                            f"Rate limit exceeded. Please try again later. Details: {str(e)}"
                        )
                
                # Check for authentication errors
                elif "unauthorized" in error_msg or "401" in error_msg or "authentication" in error_msg:
                    raise Exception(
                        f"Authentication failed. Please check your Hugging Face API key. Details: {str(e)}"
                    )
                
                # Check for service unavailable
                elif "503" in error_msg or "service unavailable" in error_msg:
                    if attempt < self.max_retries - 1:
                        delay = self.base_delay * (2 ** attempt)
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise Exception(
                            f"Hugging Face API service unavailable after {self.max_retries} attempts. "
                            f"Please try again later. Details: {str(e)}"
                        )
                
                # Check for timeout
                elif "timeout" in error_msg:
                    if attempt < self.max_retries - 1:
                        delay = self.base_delay * (2 ** attempt)
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise Exception(
                            f"Hugging Face API request timed out after {self.max_retries} attempts. "
                            f"Details: {str(e)}"
                        )
                
                # For other errors, retry once
                elif attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise Exception(f"Unexpected error during LLM generation: {str(e)}")
        
        # Should not reach here, but just in case
        raise Exception("Failed to generate structured output after all retries")
    
    def _handle_truncated_json(self, fixed_content: str, original_content: str, 
                               original_error: Exception, fixed_error: Exception) -> Dict[str, Any]:
        """
        Handle truncated JSON by attempting to complete it.
        
        Args:
            fixed_content: The content after regex fixes
            original_content: The original content from LLM
            original_error: The original JSON decode error
            fixed_error: The error after applying fixes
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            ValueError: If JSON cannot be repaired
        """
        # Last attempt: try to complete truncated JSON
        if not fixed_content.endswith("}"):
            # JSON might be truncated, try to close it
            # Count open braces
            open_braces = fixed_content.count("{")
            close_braces = fixed_content.count("}")
            
            if open_braces > close_braces:
                # Add missing closing braces
                fixed_content += "}" * (open_braces - close_braces)
                
                try:
                    return json.loads(fixed_content)
                except json.JSONDecodeError:
                    raise ValueError(
                        f"Failed to parse JSON response after all fixes: {fixed_error}\n"
                        f"Original error: {original_error}\n"
                        f"Response: {original_content[:500]}"
                    )
            else:
                raise ValueError(
                    f"Failed to parse JSON response: {fixed_error}\n"
                    f"Original error: {original_error}\n"
                    f"Response: {original_content[:500]}"
                )
        else:
            raise ValueError(
                f"Failed to parse JSON response: {fixed_error}\n"
                f"Original error: {original_error}\n"
                f"Response: {original_content[:500]}"
            )
