"""Prompt builder for constructing LLM prompts with schema constraints."""

import json
from typing import Dict, Any


class PromptBuilder:
    """Builds prompts for loan contract analysis with structured output constraints."""
    
    def build_extraction_prompt(
        self,
        contract_text: str,
        target_language: str,
        schema: Dict[str, Any]
    ) -> str:
        """
        Build a prompt for extracting financial data from a loan contract.
        
        Args:
            contract_text: The loan agreement text to analyze.
            target_language: Target language for the summary (English or Hindi).
            schema: JSON schema defining the expected output structure.
            
        Returns:
            Formatted prompt string with instructions, contract text, and schema.
        """
        # Format the schema for inclusion in the prompt
        schema_str = json.dumps(schema, indent=2)
        
        # Build language-specific instructions
        language_instruction = self._get_language_instruction(target_language)
        
        # Construct the complete prompt
        prompt = f"""Analyze the following loan agreement and extract key financial information.

INSTRUCTIONS:
1. Extract all available financial terms from the contract
2. Generate a plain-language summary explaining the loan terms in simple words
3. Provide a confidence score (0-100) indicating how confident you are in the extraction
4. {language_instruction}
5. Return ONLY valid JSON matching the schema below - no additional text, markdown, or commentary

CRITICAL: You MUST include these two required fields in your JSON response:
- "summary_text": A plain language summary of the loan (REQUIRED)
- "confidence_score": A number from 0-100 (REQUIRED)

FINANCIAL TERMS TO EXTRACT:
- loan_amount: The principal amount being borrowed
- interest_rate: The annual percentage rate (APR) or interest rate
- repayment_schedule: How and when payments must be made
- total_cost_of_credit: Total amount to be repaid including interest and fees
- late_fees: Penalties for late or missed payments
- default_consequences: What happens if the borrower defaults

SUMMARY REQUIREMENTS:
- Write in plain, simple language that anyone can understand
- Explain what the borrower is agreeing to in clear terms
- Highlight the most important financial obligations
- Avoid legal jargon - use everyday language
- Be accurate and faithful to the original contract

JSON SCHEMA:
{schema_str}

LOAN CONTRACT TEXT:
{contract_text}

IMPORTANT: Your response must be ONLY valid JSON with NO markdown formatting, NO code blocks, NO explanatory text.
Example format:
{{
  "loan_amount": "$25,000",
  "interest_rate": "8.5% APR",
  "repayment_schedule": "60 monthly payments",
  "total_cost_of_credit": "$30,750",
  "late_fees": "$50 or 5%",
  "default_consequences": "Legal action and credit impact",
  "summary_text": "This is a loan for $25,000 at 8.5% interest...",
  "confidence_score": 85
}}

All text output (including the summary) must be in {target_language}."""

        return prompt
    
    def _get_language_instruction(self, target_language: str) -> str:
        """
        Get language-specific instruction text.
        
        Args:
            target_language: Target language (English or Hindi).
            
        Returns:
            Language instruction string.
        """
        if target_language.lower() == "hindi":
            return "Write the summary_text in Hindi (हिंदी में सारांश लिखें)"
        else:
            return "Write the summary_text in English"
