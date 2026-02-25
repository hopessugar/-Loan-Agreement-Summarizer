"""FastAPI application for loan summarization service."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings
from pydantic import Field
from loan_summarizer.llm.schema import SummarizeRequest, SummarizeResponse


class Settings(BaseSettings):
    """Application settings."""
    
    huggingface_api_key: str = Field(..., validation_alias="HUGGINGFACE_API_KEY")
    huggingface_model: str = Field(default="meta-llama/Llama-3.2-3B-Instruct")
    api_timeout: int = Field(default=60)
    max_tokens: int = Field(default=2000)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings: Settings = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    Validates that HUGGINGFACE_API_KEY is set before starting the application.
    """
    global settings
    
    # Startup: Validate environment configuration
    try:
        settings = Settings()
        print(f"✓ Hugging Face API key loaded successfully")
        print(f"✓ Using model: {settings.huggingface_model}")
    except Exception as e:
        print(f"✗ Failed to load settings: {str(e)}")
        print(f"✗ Please ensure HUGGINGFACE_API_KEY environment variable is set")
        raise RuntimeError(
            "Application startup failed: HUGGINGFACE_API_KEY environment variable is not set. "
            "Please set it before starting the application."
        )
    
    yield
    
    # Shutdown: Cleanup if needed
    print("Shutting down application...")


# Create FastAPI application
app = FastAPI(
    title="Loan Summarizer API",
    description="LLM-based loan agreement summarization and financial data extraction service",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loan_summarizer.llm.schema import ErrorResponse


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors (422)."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "detail": str(exc),
            "status_code": 422
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle value errors (422)."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValueError",
            "detail": str(exc),
            "status_code": 422
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions (500)."""
    error_message = str(exc)
    
    # Determine status code based on error message
    if "authentication" in error_message.lower() or "api key" in error_message.lower():
        status_code = status.HTTP_401_UNAUTHORIZED
        error_type = "AuthenticationError"
    elif "rate limit" in error_message.lower():
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
        error_type = "RateLimitError"
    elif "connection" in error_message.lower() or "timeout" in error_message.lower():
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        error_type = "ServiceUnavailable"
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_type = "InternalServerError"
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_type,
            "detail": error_message,
            "status_code": status_code
        }
    )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Loan Summarizer API",
        "version": "0.1.0",
        "description": "LLM-based loan agreement analysis service",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "summarize": "/summarize"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns the health status of the service and configuration status.
    """
    return {
        "status": "healthy",
        "service": "Loan Summarizer API",
        "version": "0.1.0",
        "huggingface_configured": settings.huggingface_api_key is not None and len(settings.huggingface_api_key) > 0,
        "model": settings.huggingface_model
    }


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize_contract(request: SummarizeRequest):
    """
    Analyze a loan contract and extract structured financial data.
    
    This endpoint accepts loan agreement text and returns:
    - Structured financial data (loan amount, interest rate, etc.)
    - Plain language summary in the requested language
    - Confidence score for the extraction
    
    Args:
        request: SummarizeRequest with contract_text and target_language
        
    Returns:
        SummarizeResponse with structured_data, summary, and language
        
    Raises:
        HTTPException: If processing fails
    """
    from fastapi import HTTPException
    from loan_summarizer.services.summarizer import SummarizerService
    from loan_summarizer.llm.llm_client import LLMClient
    
    try:
        # Create LLM client with settings
        llm_client = LLMClient(
            api_key=settings.huggingface_api_key,
            model=settings.huggingface_model
        )
        
        # Create summarizer service
        summarizer = SummarizerService(llm_client=llm_client)
        
        # Process the contract
        response = await summarizer.summarize_contract(
            contract_text=request.contract_text,
            target_language=request.target_language
        )
        
        return response
        
    except ValueError as e:
        # Validation or parsing errors
        raise HTTPException(
            status_code=422,
            detail=f"Invalid input or response format: {str(e)}"
        )
    except Exception as e:
        # General errors (LLM API errors, etc.)
        error_message = str(e)
        
        # Determine appropriate status code based on error
        if "authentication" in error_message.lower() or "api key" in error_message.lower():
            status_code = 401
        elif "rate limit" in error_message.lower():
            status_code = 429
        elif "connection" in error_message.lower() or "timeout" in error_message.lower():
            status_code = 503
        else:
            status_code = 500
        
        raise HTTPException(
            status_code=status_code,
            detail=error_message
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
