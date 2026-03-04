"""
Hidden Cost Revealer V2 - Improved accuracy using financial entity extraction.

This version uses the FinancialEntityExtractor for accurate fee detection
and classification, eliminating false positives from dates and section numbers.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from loan_summarizer.extraction.financial_entity_extractor import (
    FinancialEntityExtractor,
    FinancialEntity,
    EntityType
)
from loan_summarizer.extraction.clause_segmenter import ClauseSegmenter


class Fee(BaseModel):
    """Represents a detected fee with full traceability."""
    type: str = Field(..., description="Type of fee")
    amount: str = Field(..., description="Fee amount")
    description: str = Field(..., description="Fee description")
    source_clause: str = Field(..., description="Source clause identifier")
    verbatim_text: str = Field(..., description="Exact text from contract")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")


class CostAnalysis(BaseModel):
    """Complete cost analysis with improved accuracy."""
    loan_amount: Optional[str] = None
    interest_rate: Optional[str] = None
    fees: List[Fee] = []
    total_fees: str = "₹0.00"
    interest_amount: Optional[str] = None
    total_cost: str = "₹0.00"
    effective_rate: Optional[str] = None
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)


class HiddenCostRevealerV2:
    """
    Improved hidden cost revealer using financial entity extraction.
    
    Key improvements:
    1. Uses FinancialEntityExtractor for accurate value detection
    2. Filters out dates, section numbers, and other non-financial values
    3. Provides source clause tracking
    4. Includes confidence scores
    5. Handles multiple currency formats
    """
    
    def __init__(self):
        """Initialize the improved hidden cost revealer."""
        self.extractor = FinancialEntityExtractor()
        self.segmenter = ClauseSegmenter()
        
        # Fee type mapping
        self.fee_type_names = {
            EntityType.PROCESSING_FEE: "Processing Fee",
            EntityType.INSURANCE_FEE: "Insurance Fee",
            EntityType.ADMINISTRATIVE_FEE: "Administrative Fee",
            EntityType.DOCUMENTATION_FEE: "Documentation Fee",
            EntityType.LATE_FEE: "Late Payment Fee",
            EntityType.PREPAYMENT_PENALTY: "Prepayment Penalty"
        }
    
    def analyze_costs(self, contract_text: str) -> CostAnalysis:
        """
        Analyze contract to detect all costs and fees with high accuracy.
        
        Args:
            contract_text: The loan agreement text
            
        Returns:
            CostAnalysis with all detected costs
        """
        # Segment contract into clauses
        clauses = self.segmenter.segment(contract_text)
        
        # Extract entities from each clause
        all_entities = []
        for clause in clauses:
            entities = self.extractor.extract_entities(clause.text, clause.clause_id)
            all_entities.extend(entities)
        
        # Extract loan amount
        loan_amount = self._get_entity_value(all_entities, EntityType.LOAN_AMOUNT)
        
        # Extract interest rate
        interest_rate = self._get_entity_value(all_entities, EntityType.INTEREST_RATE)
        
        # Extract all fees
        fees = self._extract_fees(all_entities)
        
        # Calculate totals
        total_fees = self._calculate_total_fees(fees)
        
        # Estimate interest amount if possible
        interest_amount = self._estimate_interest(
            all_entities, loan_amount, interest_rate
        )
        
        # Calculate total cost
        total_cost = self._calculate_total_cost(
            loan_amount, total_fees, interest_amount
        )
        
        # Calculate effective rate
        effective_rate = self._calculate_effective_rate(loan_amount, total_cost)
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(all_entities, fees)
        
        return CostAnalysis(
            loan_amount=loan_amount,
            interest_rate=interest_rate,
            fees=fees,
            total_fees=total_fees,
            interest_amount=interest_amount,
            total_cost=total_cost,
            effective_rate=effective_rate,
            confidence_score=confidence
        )
    
    def _get_entity_value(
        self,
        entities: List[FinancialEntity],
        entity_type: EntityType
    ) -> Optional[str]:
        """Get the value of a specific entity type (highest confidence)."""
        matching = [e for e in entities if e.type == entity_type]
        
        if not matching:
            return None
        
        # Return highest confidence match
        best = max(matching, key=lambda e: e.confidence)
        return best.value
    
    def _extract_fees(self, entities: List[FinancialEntity]) -> List[Fee]:
        """Extract all fee entities."""
        fee_types = [
            EntityType.PROCESSING_FEE,
            EntityType.INSURANCE_FEE,
            EntityType.ADMINISTRATIVE_FEE,
            EntityType.DOCUMENTATION_FEE,
            EntityType.LATE_FEE,
            EntityType.PREPAYMENT_PENALTY
        ]
        
        fees = []
        
        for entity in entities:
            if entity.type in fee_types:
                fee = Fee(
                    type=self.fee_type_names.get(entity.type, entity.type.value),
                    amount=entity.value,
                    description=self.fee_type_names.get(entity.type, entity.type.value),
                    source_clause=entity.source_clause,
                    verbatim_text=entity.verbatim_text,
                    confidence=entity.confidence
                )
                fees.append(fee)
        
        return fees
    
    def _calculate_total_fees(self, fees: List[Fee]) -> str:
        """Calculate total of all fees."""
        total = 0.0
        
        for fee in fees:
            # Parse amount
            amount_str = fee.amount.replace('₹', '').replace('$', '').replace(',', '')
            try:
                total += float(amount_str)
            except ValueError:
                continue
        
        return f"₹{total:,.2f}"
    
    def _estimate_interest(
        self,
        entities: List[FinancialEntity],
        loan_amount: Optional[str],
        interest_rate: Optional[str]
    ) -> Optional[str]:
        """Estimate total interest amount."""
        if not loan_amount or not interest_rate:
            return None
        
        # Get duration
        duration_entity = next(
            (e for e in entities if e.type == EntityType.REPAYMENT_DURATION),
            None
        )
        
        if not duration_entity:
            return None
        
        try:
            # Parse values
            loan = float(loan_amount.replace('₹', '').replace('$', '').replace(',', ''))
            rate = float(interest_rate.rstrip('%'))
            
            # Parse duration
            import re
            duration_match = re.search(r'(\d+)\s+(month|year)', duration_entity.value, re.IGNORECASE)
            if not duration_match:
                return None
            
            duration_value = int(duration_match.group(1))
            duration_unit = duration_match.group(2).lower()
            
            # Convert to months
            months = duration_value if 'month' in duration_unit else duration_value * 12
            
            # Simple interest calculation
            interest = (loan * rate * months) / (100 * 12)
            
            return f"₹{interest:,.2f}"
        
        except (ValueError, AttributeError):
            return None
    
    def _calculate_total_cost(
        self,
        loan_amount: Optional[str],
        total_fees: str,
        interest_amount: Optional[str]
    ) -> str:
        """Calculate total cost of the loan."""
        try:
            loan = float(loan_amount.replace('₹', '').replace('$', '').replace(',', '')) if loan_amount else 0
            fees = float(total_fees.replace('₹', '').replace('$', '').replace(',', ''))
            interest = float(interest_amount.replace('₹', '').replace('$', '').replace(',', '')) if interest_amount else 0
            
            total = loan + fees + interest
            return f"₹{total:,.2f}"
        except (ValueError, AttributeError):
            return "₹0.00"
    
    def _calculate_effective_rate(
        self,
        loan_amount: Optional[str],
        total_cost: str
    ) -> Optional[str]:
        """Calculate effective cost as percentage of loan amount."""
        try:
            if not loan_amount:
                return None
            
            loan = float(loan_amount.replace('₹', '').replace('$', '').replace(',', ''))
            cost = float(total_cost.replace('₹', '').replace('$', '').replace(',', ''))
            
            if loan == 0:
                return None
            
            rate = ((cost - loan) / loan) * 100
            return f"{rate:.2f}%"
        except (ValueError, AttributeError):
            return None
    
    def _calculate_confidence(
        self,
        entities: List[FinancialEntity],
        fees: List[Fee]
    ) -> float:
        """Calculate overall confidence score."""
        if not entities:
            return 0.0
        
        # Average confidence of all entities
        total_confidence = sum(e.confidence for e in entities)
        avg_confidence = total_confidence / len(entities)
        
        # Boost if we found key entities
        has_loan_amount = any(e.type == EntityType.LOAN_AMOUNT for e in entities)
        has_interest_rate = any(e.type == EntityType.INTEREST_RATE for e in entities)
        has_fees = len(fees) > 0
        
        boost = 0.0
        if has_loan_amount:
            boost += 0.1
        if has_interest_rate:
            boost += 0.1
        if has_fees:
            boost += 0.1
        
        return min(avg_confidence + boost, 1.0)
    
    def format_analysis(self, analysis: CostAnalysis) -> str:
        """Format cost analysis as readable text."""
        lines = []
        lines.append("=" * 70)
        lines.append("HIDDEN COST ANALYSIS (V2 - Improved Accuracy)")
        lines.append("=" * 70)
        lines.append(f"\nConfidence Score: {analysis.confidence_score:.1%}\n")
        
        if analysis.loan_amount:
            lines.append(f"Loan Amount: {analysis.loan_amount}")
        
        if analysis.interest_rate:
            lines.append(f"Interest Rate: {analysis.interest_rate}")
        
        if analysis.fees:
            lines.append("\n" + "-" * 70)
            lines.append("DETECTED FEES:")
            lines.append("-" * 70)
            
            # Group fees by type
            fees_by_type = {}
            for fee in analysis.fees:
                if fee.type not in fees_by_type:
                    fees_by_type[fee.type] = []
                fees_by_type[fee.type].append(fee)
            
            for fee_type, fees in fees_by_type.items():
                lines.append(f"\n{fee_type}:")
                for fee in fees:
                    lines.append(f"  • {fee.amount}")
                    lines.append(f"    Source: {fee.source_clause}")
                    lines.append(f"    Confidence: {fee.confidence:.1%}")
                    lines.append(f"    Context: {fee.verbatim_text[:100]}...")
        
        lines.append("\n" + "=" * 70)
        lines.append("SUMMARY:")
        lines.append("=" * 70)
        lines.append(f"Total Fees: {analysis.total_fees}")
        
        if analysis.interest_amount:
            lines.append(f"Estimated Interest: {analysis.interest_amount}")
        
        lines.append(f"\nTOTAL COST: {analysis.total_cost}")
        
        if analysis.effective_rate:
            lines.append(f"Effective Cost Rate: {analysis.effective_rate}")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)
