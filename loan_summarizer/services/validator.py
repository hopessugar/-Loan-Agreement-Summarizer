"""Validator service for financial data validation."""

import re
from typing import List, Optional
from pydantic import BaseModel
from loan_summarizer.llm.schema import StructuredLoanData


class ValidationIssue(BaseModel):
    """Represents a validation issue found in the data."""
    
    field: str
    issue: str
    severity: str  # "error" or "warning"


class ValidationResult(BaseModel):
    """Result of financial data validation."""
    
    is_valid: bool
    issues: List[ValidationIssue]
    quality_score: int  # 0-100, higher is better


class ValidatorService:
    """Service for validating extracted financial data."""
    
    def validate_financial_data(
        self,
        data: StructuredLoanData
    ) -> ValidationResult:
        """
        Validate extracted financial data for consistency and format.
        
        Args:
            data: The structured loan data to validate.
            
        Returns:
            ValidationResult with issues list and quality indicator.
        """
        issues: List[ValidationIssue] = []
        
        # Validate loan_amount
        if data.loan_amount:
            loan_issues = self._validate_loan_amount(data.loan_amount)
            issues.extend(loan_issues)
        
        # Validate interest_rate
        if data.interest_rate:
            rate_issues = self._validate_interest_rate(data.interest_rate)
            issues.extend(rate_issues)
        
        # Validate total_cost_of_credit
        if data.total_cost_of_credit:
            cost_issues = self._validate_total_cost(data.total_cost_of_credit)
            issues.extend(cost_issues)
        
        # Validate late_fees
        if data.late_fees:
            fee_issues = self._validate_late_fees(data.late_fees)
            issues.extend(fee_issues)
        
        # Check for missing critical fields
        missing_issues = self._check_missing_fields(data)
        issues.extend(missing_issues)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(data, issues)
        
        # Determine if valid (no errors, warnings are ok)
        has_errors = any(issue.severity == "error" for issue in issues)
        is_valid = not has_errors
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            quality_score=quality_score
        )
    
    def _validate_loan_amount(self, loan_amount: str) -> List[ValidationIssue]:
        """Validate loan amount is positive and properly formatted."""
        issues = []
        
        # Extract numerical value
        numbers = re.findall(r'\d+(?:,\d{3})*(?:\.\d+)?', loan_amount)
        
        if not numbers:
            issues.append(ValidationIssue(
                field="loan_amount",
                issue="No numerical value found in loan amount",
                severity="error"
            ))
            return issues
        
        # Check if negative (contains minus sign)
        if '-' in loan_amount and loan_amount.index('-') < loan_amount.index(numbers[0]):
            issues.append(ValidationIssue(
                field="loan_amount",
                issue="Loan amount appears to be negative",
                severity="error"
            ))
        
        # Try to parse and check if positive
        try:
            # Remove currency symbols and commas
            clean_value = re.sub(r'[^\d.]', '', numbers[0])
            value = float(clean_value)
            
            if value <= 0:
                issues.append(ValidationIssue(
                    field="loan_amount",
                    issue=f"Loan amount must be positive, got {value}",
                    severity="error"
                ))
        except ValueError:
            issues.append(ValidationIssue(
                field="loan_amount",
                issue="Could not parse loan amount as a number",
                severity="error"
            ))
        
        return issues
    
    def _validate_interest_rate(self, interest_rate: str) -> List[ValidationIssue]:
        """Validate interest rate is a valid percentage."""
        issues = []
        
        # Extract numerical value
        numbers = re.findall(r'\d+(?:\.\d+)?', interest_rate)
        
        if not numbers:
            issues.append(ValidationIssue(
                field="interest_rate",
                issue="No numerical value found in interest rate",
                severity="error"
            ))
            return issues
        
        try:
            rate = float(numbers[0])
            
            # Check if rate is reasonable (0-100% for most loans)
            if rate < 0:
                issues.append(ValidationIssue(
                    field="interest_rate",
                    issue=f"Interest rate cannot be negative: {rate}%",
                    severity="error"
                ))
            elif rate > 100:
                issues.append(ValidationIssue(
                    field="interest_rate",
                    issue=f"Interest rate seems unusually high: {rate}%",
                    severity="warning"
                ))
        except ValueError:
            issues.append(ValidationIssue(
                field="interest_rate",
                issue="Could not parse interest rate as a number",
                severity="error"
            ))
        
        return issues
    
    def _validate_total_cost(self, total_cost: str) -> List[ValidationIssue]:
        """Validate total cost of credit."""
        issues = []
        
        # Extract numerical value
        numbers = re.findall(r'\d+(?:,\d{3})*(?:\.\d+)?', total_cost)
        
        if not numbers:
            issues.append(ValidationIssue(
                field="total_cost_of_credit",
                issue="No numerical value found in total cost",
                severity="warning"
            ))
            return issues
        
        try:
            # Remove currency symbols and commas
            clean_value = re.sub(r'[^\d.]', '', numbers[0])
            value = float(clean_value)
            
            if value <= 0:
                issues.append(ValidationIssue(
                    field="total_cost_of_credit",
                    issue="Total cost should be positive",
                    severity="warning"
                ))
        except ValueError:
            issues.append(ValidationIssue(
                field="total_cost_of_credit",
                issue="Could not parse total cost as a number",
                severity="warning"
            ))
        
        return issues
    
    def _validate_late_fees(self, late_fees: str) -> List[ValidationIssue]:
        """Validate late fees format."""
        issues = []
        
        # Extract numerical value
        numbers = re.findall(r'\d+(?:,\d{3})*(?:\.\d+)?', late_fees)
        
        if not numbers:
            issues.append(ValidationIssue(
                field="late_fees",
                issue="No numerical value found in late fees",
                severity="warning"
            ))
            return issues
        
        try:
            # Remove currency symbols and commas
            clean_value = re.sub(r'[^\d.]', '', numbers[0])
            value = float(clean_value)
            
            if value < 0:
                issues.append(ValidationIssue(
                    field="late_fees",
                    issue="Late fees cannot be negative",
                    severity="warning"
                ))
        except ValueError:
            issues.append(ValidationIssue(
                field="late_fees",
                issue="Could not parse late fees as a number",
                severity="warning"
            ))
        
        return issues
    
    def _check_missing_fields(self, data: StructuredLoanData) -> List[ValidationIssue]:
        """Check for missing critical fields."""
        issues = []
        
        critical_fields = {
            "loan_amount": data.loan_amount,
            "interest_rate": data.interest_rate,
        }
        
        for field_name, field_value in critical_fields.items():
            if not field_value:
                issues.append(ValidationIssue(
                    field=field_name,
                    issue=f"Critical field '{field_name}' is missing",
                    severity="warning"
                ))
        
        return issues
    
    def _calculate_quality_score(
        self,
        data: StructuredLoanData,
        issues: List[ValidationIssue]
    ) -> int:
        """
        Calculate overall quality score (0-100).
        
        Higher score means better data quality.
        """
        score = 100
        
        # Deduct points for errors
        error_count = sum(1 for issue in issues if issue.severity == "error")
        score -= error_count * 20
        
        # Deduct points for warnings
        warning_count = sum(1 for issue in issues if issue.severity == "warning")
        score -= warning_count * 10
        
        # Deduct points for missing optional fields
        optional_fields = [
            data.repayment_schedule,
            data.total_cost_of_credit,
            data.late_fees,
            data.default_consequences
        ]
        missing_optional = sum(1 for field in optional_fields if not field)
        score -= missing_optional * 5
        
        # Ensure score is in valid range
        return max(0, min(100, score))
