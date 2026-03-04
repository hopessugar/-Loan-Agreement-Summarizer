"""LLM client for Hugging Face API communication."""

import os
import asyncio
import json
from typing import Dict, Any, Optional
from huggingface_hub import InferenceClient


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
                    fixed_content = content
                    
                    # Try to find and extract JSON from the response
                    start_idx = content.find("{")
                    end_idx = content.rfind("}") + 1
                    
                    if start_idx != -1 and end_idx > start_idx:
                        fixed_content = content[start_idx:end_idx]
                        
                        # Try to fix common issues
                        # 1. Missing commas between fields
                        import re
                        # Add comma after closing quote if followed by quote without comma
                        fixed_content = re.sub(r'"\s*\n\s*"', '",\n"', fixed_content)
                        
                        # 2. Try parsing the fixed content
                        try:
                            result = json.loads(fixed_content)
                        except json.JSONDecodeError:
                            # If still fails, raise original error with context
                            raise ValueError(
                                f"Failed to parse JSON response: {e}\n"
                                f"Response: {content[:500]}"
                            )
                    else:
                        raise ValueError(
                            f"Failed to parse JSON response: {e}\n"
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
