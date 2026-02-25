# Implementation Plan: Loan Summarizer

## Overview

This implementation plan breaks down the loan summarizer application into discrete, incremental coding tasks. Each task builds on previous work, starting with core infrastructure, then adding LLM integration, services, API endpoints, and finally the frontend. The plan ensures that functionality is validated early through tests and that all components are properly integrated.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create directory structure: `loan_summarizer/`, `llm/`, `services/`, `utils/`, `sample_data/`, `tests/`
  - Create `requirements.txt` with FastAPI, Streamlit, OpenAI, Pydantic, Uvicorn, Hypothesis, pytest, httpx
  - Create empty `__init__.py` files in each module directory
  - _Requirements: 7.1, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_

- [ ] 2. Implement data models and schemas
  - [x] 2.1 Create Pydantic models in `llm/schema.py`
    - Define `StructuredLoanData` model with all financial fields and confidence_score
    - Define `SummarizeRequest` model with contract_text and target_language
    - Define `SummarizeResponse` model with structured_data, summary, and language
    - Define `ErrorResponse` model for error handling
    - Define JSON schema dictionary for LLM output constraint
    - _Requirements: 2.2, 2.5, 3.7, 3.8, 7.4, 7.7_

  - [ ]* 2.2 Write property test for confidence score range
    - **Property 5: Confidence Score Range**
    - **Validates: Requirements 3.8**

  - [ ]* 2.3 Write unit tests for Pydantic model validation
    - Test valid and invalid request bodies
    - Test field constraints and defaults
    - _Requirements: 2.2, 2.3_

- [ ] 3. Implement LLM client
  - [x] 3.1 Create `llm/llm_client.py` with LLMClient class
    - Implement `__init__` to read OPENAI_API_KEY from environment
    - Implement async `generate_structured_output` method
    - Use OpenAI client with JSON mode or function calling for structured output
    - Include error handling for API errors (connection, rate limit, timeout)
    - Add retry logic with exponential backoff for transient failures
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 3.2 Write property test for LLM error handling
    - **Property 10: LLM Error Handling**
    - **Validates: Requirements 6.4**

  - [ ]* 3.3 Write unit tests for LLM client
    - Test API key initialization
    - Test error handling with mocked OpenAI responses
    - Test retry logic
    - _Requirements: 6.1, 6.2, 6.4_

- [ ] 4. Implement prompt builder
  - [x] 4.1 Create `llm/prompt_builder.py` with PromptBuilder class
    - Implement `build_extraction_prompt` method
    - Include contract text, extraction instructions, JSON schema, and language requirements
    - Format prompt to encourage structured output and accuracy
    - _Requirements: 6.5, 7.5_

  - [ ]* 4.2 Write property test for schema inclusion in prompts
    - **Property 11: Schema Inclusion in Prompts**
    - **Validates: Requirements 6.5**

  - [ ]* 4.3 Write unit tests for prompt builder
    - Test prompt generation with different languages
    - Verify schema is included in output
    - Test with sample contract text
    - _Requirements: 6.5_

- [ ] 5. Implement validator service
  - [x] 5.1 Create `services/validator.py` with ValidatorService class
    - Implement `validate_financial_data` method
    - Check numerical format for loan_amount, interest_rate, total_cost_of_credit, late_fees
    - Verify loan_amount is positive if present
    - Verify interest_rate is valid percentage if present
    - Return ValidationResult with issues list and overall quality indicator
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ]* 5.2 Write property test for numerical validation
    - **Property 7: Numerical Validation Consistency**
    - **Validates: Requirements 5.1, 5.4, 5.5**

  - [ ]* 5.3 Write property test for inconsistency detection
    - **Property 9: Inconsistency Detection**
    - **Validates: Requirements 5.2**

  - [ ]* 5.4 Write property test for validation result completeness
    - **Property 8: Validation Result Completeness**
    - **Validates: Requirements 5.3**

  - [ ]* 5.5 Write unit tests for validator service
    - Test with valid financial data
    - Test with invalid data (negative amounts, invalid percentages)
    - Test with missing fields
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 6. Implement summarizer service
  - [x] 6.1 Create `services/summarizer.py` with SummarizerService class
    - Implement async `summarize_contract` method
    - Orchestrate: build prompt → call LLM client → validate data → return response
    - Handle errors from LLM client gracefully
    - Ensure all required fields are present in response
    - _Requirements: 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 4.1, 4.2, 4.3, 7.3_

  - [ ]* 6.2 Write property test for extraction completeness
    - **Property 3: Financial Data Extraction Completeness**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

  - [ ]* 6.3 Write property test for JSON output format
    - **Property 4: JSON Output Format Strictness**
    - **Validates: Requirements 3.7**

  - [ ]* 6.4 Write property test for language output matching
    - **Property 6: Language Output Matching**
    - **Validates: Requirements 4.2, 4.3**

  - [ ]* 6.5 Write unit tests for summarizer service
    - Test with mocked LLM client
    - Test error propagation
    - Test with sample contracts
    - _Requirements: 2.5, 3.7, 4.2, 4.3_

- [ ] 7. Create sample data
  - [x] 7.1 Create `sample_data/sample_contract.txt`
    - Write realistic loan agreement text
    - Include all required financial terms: loan_amount, interest_rate, repayment_schedule, total_cost_of_credit, late_fees, default_consequences
    - Use clear, identifiable values for testing
    - _Requirements: 10.1, 10.2, 10.3_

- [ ] 8. Implement utility functions
  - [x] 8.1 Create `utils/text_utils.py`
    - Implement text preprocessing functions (trim whitespace, normalize line breaks)
    - Implement text validation (check for minimum length, detect language if needed)
    - Add helper functions for formatting output
    - _Requirements: 1.4, 1.5_

  - [ ]* 8.2 Write unit tests for text utilities
    - Test preprocessing functions
    - Test validation functions
    - _Requirements: 1.4, 1.5_

- [ ] 9. Checkpoint - Ensure core services work
  - Run all tests for LLM client, prompt builder, validator, and summarizer
  - Verify services can be instantiated and called
  - Ensure all tests pass, ask the user if questions arise

- [ ] 10. Implement FastAPI backend
  - [x] 10.1 Create `app.py` with FastAPI application
    - Initialize FastAPI app with title, description, version
    - Create Settings class for environment configuration
    - Implement startup event to validate OPENAI_API_KEY
    - Add CORS middleware if needed
    - _Requirements: 6.1, 6.2, 7.1_

  - [x] 10.2 Implement POST /summarize endpoint
    - Accept SummarizeRequest body
    - Call SummarizerService.summarize_contract
    - Return SummarizeResponse
    - Handle errors and return appropriate status codes
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 10.3 Implement GET /health endpoint
    - Return simple health status
    - _Requirements: 8.1_

  - [x] 10.4 Add exception handlers
    - Handle validation errors (422)
    - Handle authentication errors (401)
    - Handle external service errors (502/503)
    - Handle internal errors (500)
    - Return ErrorResponse format consistently
    - _Requirements: 9.1, 9.2_

  - [ ]* 10.5 Write property test for request validation
    - **Property 1: Request Validation Consistency**
    - **Validates: Requirements 2.3**

  - [ ]* 10.6 Write property test for response structure
    - **Property 2: Response Structure Completeness**
    - **Validates: Requirements 2.5**

  - [ ]* 10.7 Write property test for error response format
    - **Property 12: Error Response Format**
    - **Validates: Requirements 9.1, 9.2**

  - [ ]* 10.8 Write integration tests for API endpoints
    - Test /summarize with valid requests
    - Test /summarize with invalid requests
    - Test /health endpoint
    - Test error handling
    - _Requirements: 2.1, 2.2, 2.3, 2.5, 8.1, 9.1, 9.2_

- [ ] 11. Verify API documentation
  - [ ] 11.1 Test automatic documentation generation
    - Start the FastAPI server
    - Verify /docs endpoint is accessible
    - Verify Swagger UI displays correctly
    - Check that request/response schemas are documented
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 12. Implement Streamlit frontend
  - [x] 12.1 Create `frontend.py` with Streamlit UI
    - Add title and description
    - Create text area for contract input with label
    - Create dropdown for language selection (English, Hindi)
    - Create submit button
    - _Requirements: 1.1, 1.2, 1.3, 7.1_

  - [x] 12.2 Implement input validation
    - Check for empty contract text before submission
    - Display error message if text is empty
    - _Requirements: 1.5_

  - [x] 12.3 Implement API communication
    - Send POST request to Backend /summarize endpoint
    - Handle successful responses
    - Display structured data in formatted sections
    - Display summary text
    - _Requirements: 2.1, 2.5_

  - [x] 12.4 Implement error handling
    - Catch request exceptions
    - Display error messages from backend
    - Show user-friendly error messages
    - _Requirements: 9.3_

  - [ ]* 12.5 Write property test for text input acceptance
    - **Property 14: Text Input Acceptance**
    - **Validates: Requirements 1.4**

  - [ ]* 12.6 Write property test for error display
    - **Property 13: Frontend Error Display**
    - **Validates: Requirements 9.3**

  - [ ]* 12.7 Write unit tests for frontend components
    - Test UI rendering (requires Streamlit testing utilities)
    - Test input validation
    - Test error display
    - _Requirements: 1.1, 1.2, 1.3, 1.5, 9.3_

- [ ] 13. Create documentation
  - [x] 13.1 Create `README.md`
    - Add project overview and description
    - Document prerequisites (Python 3.11+, OpenAI API key)
    - Document installation steps (clone, install requirements)
    - Document how to set OPENAI_API_KEY environment variable
    - Document how to start the backend server (uvicorn command)
    - Document how to start the frontend (streamlit command)
    - Document project structure with module descriptions
    - Add usage examples
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

- [ ] 14. Final integration and testing
  - [ ] 14.1 End-to-end integration test
    - Start backend server
    - Start frontend application
    - Test complete flow with sample contract
    - Verify extraction accuracy
    - Test with both English and Hindi outputs
    - Test error scenarios
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.5, 4.2, 4.3_

  - [ ] 14.2 Run full test suite
    - Execute all unit tests
    - Execute all property tests with 100 iterations
    - Verify code coverage meets 80% target
    - Fix any failing tests

- [ ] 15. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties with minimum 100 iterations
- Unit tests validate specific examples and edge cases
- The implementation follows a bottom-up approach: models → services → API → frontend
- All async operations should use proper async/await patterns
- Mock external dependencies (OpenAI API) in tests for deterministic results
