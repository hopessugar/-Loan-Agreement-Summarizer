# Loan Summarizer

A production-style proof-of-concept web application that uses Large Language Models (LLMs) to analyze loan agreements and extract structured financial data with plain-language summaries.

## Features

- **Structured Data Extraction**: Automatically extracts key financial terms including loan amount, interest rate, repayment schedule, total cost of credit, late fees, and default consequences
- **Plain Language Summaries**: Generates easy-to-understand summaries of complex loan agreements
- **Multi-language Support**: Provides summaries in English or Hindi
- **Data Validation**: Validates extracted financial data to reduce hallucinations
- **Clean UI**: Simple Streamlit interface for easy interaction
- **RESTful API**: FastAPI backend with automatic OpenAPI documentation

## Prerequisites

- Python 3.11 or higher
- Google Gemini API key (Get one at https://makersuite.google.com/app/apikey)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd loan-summarizer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Google Gemini API key:

**On Windows (Command Prompt):**
```cmd
set GEMINI_API_KEY=your-api-key-here
```

**On Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your-api-key-here"
```

**On Linux/Mac:**
```bash
export GEMINI_API_KEY=your-api-key-here
```

**Using .env file (recommended):**
Create a `.env` file in the project root:
```
GEMINI_API_KEY=your-api-key-here
```

## Usage

### Starting the Backend Server

Run the FastAPI backend server:

```bash
uvicorn app:app --reload
```

The API will be available at `http://localhost:8000`

- API Documentation (Swagger UI): `http://localhost:8000/docs`
- Alternative Documentation (ReDoc): `http://localhost:8000/redoc`
- Health Check: `http://localhost:8000/health`

### Starting the Frontend

In a separate terminal, run the Streamlit frontend:

```bash
streamlit run frontend.py
```

The web interface will open automatically in your browser (typically at `http://localhost:8501`)

### Using the Application

1. Open the Streamlit interface in your browser
2. Paste your loan agreement text into the text area
3. Select your preferred summary language (English or Hindi)
4. Click "Analyze Contract"
5. View the extracted financial data and plain-language summary
6. Optionally download the results as JSON

### Sample Contract

A sample loan agreement is provided in `loan_summarizer/sample_data/sample_contract.txt` for testing purposes.

## Project Structure

```
loan-summarizer/
│
├── app.py                          # FastAPI backend entry point
├── frontend.py                     # Streamlit frontend
├── requirements.txt                # Python dependencies
├── README.md                       # This file
│
├── loan_summarizer/                # Main application package
│   ├── __init__.py
│   │
│   ├── llm/                        # LLM integration module
│   │   ├── __init__.py
│   │   ├── llm_client.py          # Google Gemini API client
│   │   ├── prompt_builder.py      # Prompt construction
│   │   └── schema.py              # Pydantic models and schemas
│   │
│   ├── services/                   # Business logic services
│   │   ├── __init__.py
│   │   ├── summarizer.py          # Contract analysis orchestration
│   │   └── validator.py           # Financial data validation
│   │
│   ├── utils/                      # Utility functions
│   │   ├── __init__.py
│   │   └── text_utils.py          # Text processing utilities
│   │
│   └── sample_data/                # Sample contracts for testing
│       └── sample_contract.txt
│
└── tests/                          # Test suite
    ├── __init__.py
    ├── unit_tests/                 # Unit tests
    ├── property_tests/             # Property-based tests
    └── integration_tests/          # Integration tests
```

## Module Responsibilities

### `app.py`
- FastAPI application setup and configuration
- API endpoint definitions
- Request/response handling
- Error handling and exception management

### `frontend.py`
- Streamlit user interface
- User input collection
- API communication
- Results display

### `llm/` Module
- **llm_client.py**: Manages Google Gemini API communication with async operations, error handling, and retry logic
- **prompt_builder.py**: Constructs prompts with JSON schema constraints and language requirements
- **schema.py**: Defines Pydantic models for request/response validation and JSON schemas

### `services/` Module
- **summarizer.py**: Orchestrates the complete analysis workflow (prompt building → LLM call → validation)
- **validator.py**: Validates extracted financial data for consistency and format

### `utils/` Module
- **text_utils.py**: Text preprocessing, validation, and formatting utilities

## API Endpoints

### POST /summarize
Analyze a loan contract and extract structured financial data.

**Request Body:**
```json
{
  "contract_text": "LOAN AGREEMENT...",
  "target_language": "English"
}
```

**Response:**
```json
{
  "structured_data": {
    "loan_amount": "$25,000",
    "interest_rate": "8.5% APR",
    "repayment_schedule": "60 monthly payments",
    "total_cost_of_credit": "$30,750",
    "late_fees": "$50 or 5%",
    "default_consequences": "Legal action, credit impact...",
    "summary_text": "Plain language summary...",
    "confidence_score": 85
  },
  "summary": "Plain language summary...",
  "language": "English"
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "Loan Summarizer API",
  "version": "0.1.0",
  "gemini_configured": true,
  "model": "gemini-1.5-flash"
}
```

## Configuration

The application can be configured through environment variables:

- `GEMINI_API_KEY` (required): Your Google Gemini API key
- `GEMINI_MODEL` (optional): Gemini model to use (default: "gemini-1.5-flash")
- `API_TIMEOUT` (optional): API timeout in seconds (default: 60)
- `MAX_TOKENS` (optional): Maximum tokens for LLM response (default: 2000)

## Error Handling

The application provides comprehensive error handling:

- **422 Unprocessable Entity**: Invalid input or validation errors
- **401 Unauthorized**: Missing or invalid Gemini API key
- **429 Too Many Requests**: Rate limit exceeded
- **503 Service Unavailable**: Gemini API connection issues
- **500 Internal Server Error**: Unexpected errors

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit_tests/

# Run with coverage
pytest --cov=loan_summarizer
```

### Code Style

The project follows PEP 8 style guidelines. Use tools like `black` and `flake8` for formatting and linting.

## Limitations

- Requires active internet connection for Gemini API
- Processing time depends on contract length and API response time
- Accuracy depends on contract clarity and LLM capabilities
- Currently supports English and Hindi summaries only

## License

[Your License Here]

## Support

For issues, questions, or contributions, please [open an issue](your-repo-url/issues) on GitHub.
