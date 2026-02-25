"""Summarizer service for orchestrating loan contract analysis."""

from loan_summarizer.llm.llm_client import LLMClient
from loan_summarizer.llm.prompt_builder import PromptBuilder
from loan_summarizer.llm.schema import (
    StructuredLoanData,
    SummarizeResponse,
    LLM_OUTPUT_SCHEMA
)
from loan_summarizer.services.validator import ValidatorService


class SummarizerService:
    """Service for orchestrating loan contract summarization."""
    
    def __init__(
        self,
        llm_client: LLMClient = None,
        prompt_builder: PromptBuilder = None,
        validator: ValidatorService = None
    ):
        """
        Initialize the summarizer service.
        
        Args:
            llm_client: LLM client for API communication. Creates default if None.
            prompt_builder: Prompt builder for constructing prompts. Creates default if None.
            validator: Validator service for data validation. Creates default if None.
        """
        self.llm_client = llm_client or LLMClient()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.validator = validator or ValidatorService()
    
    async def summarize_contract(
        self,
        contract_text: str,
        target_language: str = "English"
    ) -> SummarizeResponse:
        """
        Analyze a loan contract and generate structured summary.
        
        This method orchestrates the complete workflow:
        1. Build prompt with schema
        2. Call LLM client to extract data
        3. Validate extracted data
        4. Return structured response
        
        Args:
            contract_text: The loan agreement text to analyze.
            target_language: Target language for summary (English or Hindi).
            
        Returns:
            SummarizeResponse with structured data and summary.
            
        Raises:
            Exception: If any step in the process fails.
        """
        try:
            # Step 1: Build the extraction prompt
            prompt = self.prompt_builder.build_extraction_prompt(
                contract_text=contract_text,
                target_language=target_language,
                schema=LLM_OUTPUT_SCHEMA
            )
            
            # Step 2: Call LLM to extract structured data
            llm_output = await self.llm_client.generate_structured_output(
                prompt=prompt,
                schema=LLM_OUTPUT_SCHEMA,
                temperature=0.1
            )
            
            # Step 3: Parse LLM output into StructuredLoanData
            structured_data = self._parse_llm_output(llm_output)
            
            # Step 4: Validate the extracted data
            validation_result = self.validator.validate_financial_data(structured_data)
            
            # Log validation issues if any (in production, use proper logging)
            if validation_result.issues:
                print(f"Validation issues found: {len(validation_result.issues)}")
                for issue in validation_result.issues:
                    print(f"  - {issue.field}: {issue.issue} ({issue.severity})")
            
            # Step 5: Construct and return response
            # Use summary_text from structured_data as the main summary
            response = SummarizeResponse(
                structured_data=structured_data,
                summary=structured_data.summary_text,
                language=target_language
            )
            
            return response
            
        except Exception as e:
            # Re-raise with context
            raise Exception(f"Failed to summarize contract: {str(e)}")
    
    def _parse_llm_output(self, llm_output: dict) -> StructuredLoanData:
        """
        Parse LLM output dictionary into StructuredLoanData model.
        
        Args:
            llm_output: Dictionary from LLM containing extracted data.
            
        Returns:
            StructuredLoanData instance.
            
        Raises:
            ValueError: If required fields are missing or invalid.
        """
        try:
            # Ensure required fields are present
            if "summary_text" not in llm_output:
                raise ValueError("Missing required field: summary_text")
            
            if "confidence_score" not in llm_output:
                raise ValueError("Missing required field: confidence_score")
            
            # Create StructuredLoanData instance
            # Pydantic will handle validation
            structured_data = StructuredLoanData(**llm_output)
            
            return structured_data
            
        except Exception as e:
            raise ValueError(f"Failed to parse LLM output: {str(e)}")
