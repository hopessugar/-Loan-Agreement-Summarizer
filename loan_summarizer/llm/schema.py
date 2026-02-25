"""Pydantic models and JSON schemas for loan summarization."""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class StructuredLoanData(BaseModel):
    """Structured financial data extracted from loan agreement."""
    
    loan_amount: Optional[str] = Field(
        None,
        description="The principal loan amount"
    )
    interest_rate: Optional[str] = Field(
        None,
        description="The interest rate (annual percentage rate)"
    )
    repayment_schedule: Optional[str] = Field(
        None,
        description="The repayment schedule (e.g., monthly, quarterly)"
    )
    total_cost_of_credit: Optional[str] = Field(
        None,
        description="Total cost of credit including all fees and interest"
    )
    late_fees: Optional[str] = Field(
        None,
        description="Late payment fees and penalties"
    )
    default_consequences: Optional[str] = Field(
        None,
        description="Consequences of defaulting on the loan"
    )
    summary_text: str = Field(
        ...,
        description="Plain language summary of the loan agreement"
    )
    confidence_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confidence score for the extraction (0-100)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "loan_amount": "$10,000",
                "interest_rate": "12% APR",
                "repayment_schedule": "Monthly payments over 24 months",
                "total_cost_of_credit": "$11,200",
                "late_fees": "$25 per late payment",
                "default_consequences": "Legal action and credit score impact",
                "summary_text": "This is a personal loan of $10,000...",
                "confidence_score": 85
            }
        }


class SummarizeRequest(BaseModel):
    """Request model for loan summarization endpoint."""
    
    contract_text: str = Field(
        ...,
        min_length=1,
        description="The loan agreement text to analyze"
    )
    target_language: Literal["English", "Hindi"] = Field(
        default="English",
        description="Target language for the summary"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "contract_text": "LOAN AGREEMENT\n\nThis agreement is made between...",
                "target_language": "English"
            }
        }


class SummarizeResponse(BaseModel):
    """Response model for loan summarization endpoint."""
    
    structured_data: StructuredLoanData = Field(
        ...,
        description="Extracted structured financial data"
    )
    summary: str = Field(
        ...,
        description="Plain language summary in the requested language"
    )
    language: str = Field(
        ...,
        description="Language of the summary"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "structured_data": {
                    "loan_amount": "$10,000",
                    "interest_rate": "12% APR",
                    "repayment_schedule": "Monthly",
                    "total_cost_of_credit": "$11,200",
                    "late_fees": "$25",
                    "default_consequences": "Legal action",
                    "summary_text": "Summary text...",
                    "confidence_score": 85
                },
                "summary": "This loan agreement is for $10,000...",
                "language": "English"
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(
        ...,
        description="Error type or category"
    )
    detail: str = Field(
        ...,
        description="Detailed error message"
    )
    status_code: int = Field(
        ...,
        description="HTTP status code"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "detail": "Contract text cannot be empty",
                "status_code": 422
            }
        }


# JSON schema for LLM output constraint
LLM_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "loan_amount": {
            "type": "string",
            "description": "The principal loan amount"
        },
        "interest_rate": {
            "type": "string",
            "description": "The interest rate (annual percentage rate)"
        },
        "repayment_schedule": {
            "type": "string",
            "description": "The repayment schedule"
        },
        "total_cost_of_credit": {
            "type": "string",
            "description": "Total cost of credit"
        },
        "late_fees": {
            "type": "string",
            "description": "Late payment fees"
        },
        "default_consequences": {
            "type": "string",
            "description": "Consequences of default"
        },
        "summary_text": {
            "type": "string",
            "description": "Plain language summary"
        },
        "confidence_score": {
            "type": "integer",
            "minimum": 0,
            "maximum": 100,
            "description": "Confidence score (0-100)"
        }
    },
    "required": ["summary_text", "confidence_score"],
    "additionalProperties": False
}
