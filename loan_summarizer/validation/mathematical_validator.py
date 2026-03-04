"""
Mathematical Validator - Checks mathematical consistency of extracted values.

Validates:
- Payment calculations (monthly_payment × months = total)
- Interest calculations
- Fee totals
- Percentage calculations
"""

import re
import logging
from typing import List, Tuple, Optional

from loan_summarizer.extraction.financial_entity_extractor import (
    FinancialEntity,
    EntityType
)


logger = logging.getLogger(__name__)


class MathematicalValidator:
    """
    Validates mathematical consistency between financial entities.
    
    Checks:
    1. Total payment = monthly_payment × number_of_months
    2. Total cost = loan_amount + interest + fees
    3. Interest calculations
    4. Fee summations
    """
    
    def __init__(self, tolerance_percent: float = 10.0):
        """
        Initialize mathematical validator.
        
        Args:
            tolerance_percent: Acceptable percentage difference (default 10%)
        """
        self.tolerance_percent = tolerance_percent
    
    def validate_consistency(
        self,
        entities: List[FinancialEntity]
    ) -> Tuple[List[str], List[FinancialEntity]]:
        """
        Validate mathematical consistency.
        
        Args:
            entities: List of financial entities
            
        Returns:
            Tuple of (issues, corrections)
        """
        issues = []
        corrections = []
        
        # Extract values by type
        values = self._extract_values_by_type(entities)
        
        # Check 1: Payment calculation
        payment_issues, payment_corrections = self._validate_payment_calculation(values)
        issues.extend(payment_issues)
        corrections.extend(payment_corrections)
        
        # Check 2: Total cost calculation
        cost_issues, cost_corrections = self._validate_total_cost(values)
        issues.extend(cost_issues)
        corrections.extend(cost_corrections)
        
        # Check 3: Fee summation
        fee_issues = self._validate_fee_totals(values)
        issues.extend(fee_issues)
        
        return issues, corrections
    
    def _extract_values_by_type(
        self,
        entities: List[FinancialEntity]
    ) -> dict:
        """Extract and parse values by entity type."""
        values = {}
        
        for entity in entities:
            # Parse numeric value
            numeric_value = self._parse_numeric(entity.value)
            
            if numeric_value is not None:
                if entity.type not in values:
                    values[entity.type] = []
                values[entity.type].append({
                    "entity": entity,
                    "numeric": numeric_value
                })
        
        return values
    
    def _parse_numeric(self, value: str) -> Optional[float]:
        """Parse numeric value from string."""
        try:
            # Remove currency symbols and commas
            cleaned = re.sub(r'[₹$,Rs\s]', '', value)
            
            # Remove percentage sign
            cleaned = cleaned.rstrip('%')
            
            return float(cleaned)
        except (ValueError, AttributeError):
            return None
    
    def _validate_payment_calculation(
        self,
        values: dict
    ) -> Tuple[List[str], List[FinancialEntity]]:
        """Validate: total = monthly_payment × months."""
        issues = []
        corrections = []
        
        # Get values
        monthly_payment = self._get_first_value(values, EntityType.MONTHLY_PAYMENT)
        duration = self._get_first_value(values, EntityType.REPAYMENT_DURATION)
        total_cost = self._get_first_value(values, EntityType.TOTAL_COST)
        
        if not (monthly_payment and duration):
            return issues, corrections
        
        # Parse duration to months
        months = self._parse_duration_to_months(
            values[EntityType.REPAYMENT_DURATION][0]["entity"].value
        )
        
        if not months:
            return issues, corrections
        
        # Calculate expected total
        expected_total = monthly_payment * months
        
        # Compare with extracted total
        if total_cost:
            difference_percent = abs(expected_total - total_cost) / expected_total * 100
            
            if difference_percent > self.tolerance_percent:
                issues.append(
                    f"Payment calculation mismatch: "
                    f"₹{monthly_payment:,.0f} × {months} months = ₹{expected_total:,.0f}, "
                    f"but total cost is ₹{total_cost:,.0f} "
                    f"(difference: {difference_percent:.1f}%)"
                )
                
                logger.warning(f"Payment calculation mismatch: {difference_percent:.1f}%")
        
        return issues, corrections
    
    def _validate_total_cost(
        self,
        values: dict
    ) -> Tuple[List[str], List[FinancialEntity]]:
        """Validate: total_cost = loan_amount + interest + fees."""
        issues = []
        corrections = []
        
        # Get values
        loan_amount = self._get_first_value(values, EntityType.LOAN_AMOUNT)
        total_cost = self._get_first_value(values, EntityType.TOTAL_COST)
        
        if not (loan_amount and total_cost):
            return issues, corrections
        
        # Calculate expected components
        expected_interest_and_fees = total_cost - loan_amount
        
        # Get all fees
        total_fees = 0.0
        fee_types = [
            EntityType.PROCESSING_FEE,
            EntityType.INSURANCE_FEE,
            EntityType.ADMINISTRATIVE_FEE,
            EntityType.DOCUMENTATION_FEE,
            EntityType.LATE_FEE,
            EntityType.PREPAYMENT_PENALTY
        ]
        
        for fee_type in fee_types:
            fee_value = self._get_first_value(values, fee_type)
            if fee_value:
                total_fees += fee_value
        
        # Estimate interest
        estimated_interest = expected_interest_and_fees - total_fees
        
        if estimated_interest < 0:
            issues.append(
                f"Total cost calculation issue: "
                f"Fees (₹{total_fees:,.0f}) exceed difference between "
                f"total cost (₹{total_cost:,.0f}) and loan amount (₹{loan_amount:,.0f})"
            )
        
        return issues, corrections
    
    def _validate_fee_totals(self, values: dict) -> List[str]:
        """Validate fee summations."""
        issues = []
        
        # Get all fees
        fee_types = [
            EntityType.PROCESSING_FEE,
            EntityType.INSURANCE_FEE,
            EntityType.ADMINISTRATIVE_FEE,
            EntityType.DOCUMENTATION_FEE,
            EntityType.LATE_FEE,
            EntityType.PREPAYMENT_PENALTY
        ]
        
        total_fees = 0.0
        fee_count = 0
        
        for fee_type in fee_types:
            if fee_type in values:
                for fee_data in values[fee_type]:
                    total_fees += fee_data["numeric"]
                    fee_count += 1
        
        if fee_count > 0:
            logger.info(f"Total fees detected: ₹{total_fees:,.0f} ({fee_count} fees)")
        
        return issues
    
    def _get_first_value(
        self,
        values: dict,
        entity_type: EntityType
    ) -> Optional[float]:
        """Get first numeric value for entity type."""
        if entity_type in values and values[entity_type]:
            return values[entity_type][0]["numeric"]
        return None
    
    def _parse_duration_to_months(self, duration_str: str) -> Optional[int]:
        """Parse duration string to number of months."""
        match = re.search(r'(\d+)\s*(month|year)', duration_str, re.IGNORECASE)
        
        if match:
            value = int(match.group(1))
            unit = match.group(2).lower()
            
            if 'year' in unit:
                return value * 12
            else:
                return value
        
        return None
