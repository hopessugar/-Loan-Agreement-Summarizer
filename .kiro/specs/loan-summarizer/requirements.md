# Requirements Document

## Introduction

This document specifies the requirements for a production-style proof-of-concept web application that uses Large Language Models (LLMs) to analyze loan agreements and generate simplified summaries with structured financial data extraction. The system provides a FastAPI backend with a Streamlit frontend, enabling users to input loan agreement text and receive validated, structured financial information along with plain-language summaries in multiple languages.

## Glossary

- **System**: The complete loan summarization application including backend and frontend
- **Backend**: The FastAPI server that processes requests and coordinates LLM interactions
- **Frontend**: The Streamlit user interface for contract input and result display
- **LLM_Client**: The component responsible for communicating with OpenAI API
- **Summarizer**: The service that orchestrates contract analysis and summary generation
- **Validator**: The component that verifies extracted financial data for accuracy
- **Contract_Text**: The raw loan agreement text provided by the user
- **Structured_Data**: The extracted financial terms in JSON format
- **Summary_Text**: The plain-language explanation of the loan agreement
- **Target_Language**: The language for output (English or Hindi)
- **Confidence_Score**: A numerical value (0-100) indicating extraction reliability

## Requirements

### Requirement 1: Accept Loan Agreement Input

**User Story:** As a user, I want to input loan agreement text through a web interface, so that I can receive a simplified analysis of the contract terms.

#### Acceptance Criteria

1. WHEN the Frontend starts, THE Frontend SHALL display a text area for contract input
2. WHEN the Frontend starts, THE Frontend SHALL display a dropdown with language options (English, Hindi)
3. WHEN the Frontend starts, THE Frontend SHALL display a submit button
4. WHEN a user enters text in the contract input area, THE Frontend SHALL accept text of any reasonable length
5. WHEN a user clicks the submit button with empty contract text, THE Frontend SHALL prevent submission and display an error message

### Requirement 2: Process Summarization Requests

**User Story:** As a user, I want the system to process my loan agreement and return results, so that I can understand the key terms quickly.

#### Acceptance Criteria

1. WHEN the Frontend receives a submit action, THE Frontend SHALL send a POST request to the Backend endpoint /summarize
2. WHEN the Backend receives a POST request at /summarize, THE Backend SHALL validate the request body against the defined schema
3. WHEN the Backend receives an invalid request, THE Backend SHALL return a 422 status code with validation error details
4. WHEN the Backend receives a valid request, THE Backend SHALL process the contract text and return a response within a reasonable time
5. WHEN the Backend completes processing, THE Backend SHALL return a JSON response containing structured_data, summary, and language fields

### Requirement 3: Extract Structured Financial Data

**User Story:** As a user, I want the system to extract key financial terms from the loan agreement, so that I can quickly identify important numerical values and conditions.

#### Acceptance Criteria

1. WHEN the Summarizer processes contract text, THE Summarizer SHALL extract loan_amount from the contract
2. WHEN the Summarizer processes contract text, THE Summarizer SHALL extract interest_rate from the contract
3. WHEN the Summarizer processes contract text, THE Summarizer SHALL extract repayment_schedule from the contract
4. WHEN the Summarizer processes contract text, THE Summarizer SHALL extract total_cost_of_credit from the contract
5. WHEN the Summarizer processes contract text, THE Summarizer SHALL extract late_fees from the contract
6. WHEN the Summarizer processes contract text, THE Summarizer SHALL extract default_consequences from the contract
7. WHEN the Summarizer completes extraction, THE Summarizer SHALL return data in strict JSON format without additional commentary
8. WHEN the Summarizer completes extraction, THE Summarizer SHALL include a confidence_score between 0 and 100

### Requirement 4: Generate Plain Language Summary

**User Story:** As a user, I want to receive a simplified explanation of the loan agreement, so that I can understand complex legal language without specialized knowledge.

#### Acceptance Criteria

1. WHEN the Summarizer processes contract text, THE Summarizer SHALL generate a summary_text in plain language
2. WHEN the target_language is English, THE Summarizer SHALL generate summary_text in English
3. WHEN the target_language is Hindi, THE Summarizer SHALL generate summary_text in Hindi
4. WHEN generating summary_text, THE Summarizer SHALL include explanations of key financial terms
5. WHEN generating summary_text, THE Summarizer SHALL maintain accuracy with the original contract content

### Requirement 5: Validate Extracted Data

**User Story:** As a user, I want the system to validate extracted financial data, so that I can trust the accuracy of the information and reduce the risk of hallucinations.

#### Acceptance Criteria

1. WHEN the Validator receives extracted data, THE Validator SHALL verify that numerical values are properly formatted
2. WHEN the Validator detects inconsistencies in extracted data, THE Validator SHALL flag the issues
3. WHEN the Validator completes validation, THE Validator SHALL return validation results indicating data quality
4. IF extracted loan_amount is present, THEN THE Validator SHALL verify it is a positive numerical value
5. IF extracted interest_rate is present, THEN THE Validator SHALL verify it is a valid percentage value

### Requirement 6: Integrate with OpenAI API

**User Story:** As a system administrator, I want the application to use OpenAI API for LLM capabilities, so that I can leverage state-of-the-art language models for contract analysis.

#### Acceptance Criteria

1. WHEN the LLM_Client initializes, THE LLM_Client SHALL read the API key from the OPENAI_API_KEY environment variable
2. WHEN the OPENAI_API_KEY is not set, THE System SHALL fail to start and display a clear error message
3. WHEN the LLM_Client makes API calls, THE LLM_Client SHALL use async operations
4. WHEN the LLM_Client receives an API error, THE LLM_Client SHALL handle the error gracefully and return an appropriate error message
5. WHEN the LLM_Client sends prompts to OpenAI, THE LLM_Client SHALL include the JSON schema to enforce structured output

### Requirement 7: Maintain Modular Architecture

**User Story:** As a developer, I want the codebase to be modular and well-organized, so that I can easily maintain, test, and extend the application.

#### Acceptance Criteria

1. THE System SHALL organize code into separate modules: app.py, frontend.py, llm/, services/, utils/, and sample_data/
2. THE System SHALL define LLM interaction logic in the llm/ module
3. THE System SHALL define business logic in the services/ module
4. THE System SHALL use Pydantic models for request and response validation
5. THE System SHALL separate prompt construction logic in prompt_builder.py
6. THE System SHALL separate LLM communication logic in llm_client.py
7. THE System SHALL define JSON schemas in schema.py

### Requirement 8: Provide API Documentation

**User Story:** As an API consumer, I want to access clear API documentation, so that I can understand how to interact with the backend endpoints.

#### Acceptance Criteria

1. WHEN the Backend starts, THE Backend SHALL generate automatic API documentation at /docs
2. WHEN a user accesses /docs, THE Backend SHALL display interactive Swagger UI documentation
3. WHEN viewing API documentation, THE documentation SHALL include request body schemas
4. WHEN viewing API documentation, THE documentation SHALL include response schemas
5. WHEN viewing API documentation, THE documentation SHALL include example requests and responses

### Requirement 9: Handle Errors Gracefully

**User Story:** As a user, I want the system to handle errors gracefully, so that I receive clear feedback when something goes wrong.

#### Acceptance Criteria

1. WHEN the Backend encounters an error during processing, THE Backend SHALL return an appropriate HTTP status code
2. WHEN the Backend encounters an error, THE Backend SHALL return a JSON response with error details
3. WHEN the Frontend receives an error response, THE Frontend SHALL display the error message to the user
4. WHEN the LLM_Client fails to connect to OpenAI API, THE System SHALL return a clear error message indicating the connection issue
5. IF the OpenAI API rate limit is exceeded, THEN THE System SHALL return an error message indicating rate limiting

### Requirement 10: Provide Sample Data

**User Story:** As a developer or tester, I want access to sample loan agreement text, so that I can test the application without needing to find real contracts.

#### Acceptance Criteria

1. THE System SHALL include a sample_contract.txt file in the sample_data/ directory
2. WHEN sample_contract.txt is read, THE file SHALL contain a realistic loan agreement with all required financial terms
3. THE sample_contract.txt SHALL include loan_amount, interest_rate, repayment_schedule, total_cost_of_credit, late_fees, and default_consequences

### Requirement 11: Configure Dependencies

**User Story:** As a developer, I want a clear list of project dependencies, so that I can set up the development environment easily.

#### Acceptance Criteria

1. THE System SHALL include a requirements.txt file listing all Python dependencies
2. THE requirements.txt SHALL specify FastAPI and its dependencies
3. THE requirements.txt SHALL specify Streamlit
4. THE requirements.txt SHALL specify OpenAI Python client library
5. THE requirements.txt SHALL specify Pydantic for data validation
6. THE requirements.txt SHALL specify uvicorn for running the FastAPI server
7. THE requirements.txt SHALL pin Python version to 3.11 or higher

### Requirement 12: Provide Documentation

**User Story:** As a new user or developer, I want clear documentation on how to set up and use the application, so that I can get started quickly.

#### Acceptance Criteria

1. THE System SHALL include a README.md file with setup instructions
2. THE README.md SHALL document how to set the OPENAI_API_KEY environment variable
3. THE README.md SHALL document how to install dependencies using requirements.txt
4. THE README.md SHALL document how to start the Backend server
5. THE README.md SHALL document how to start the Frontend application
6. THE README.md SHALL document the project structure and module responsibilities
