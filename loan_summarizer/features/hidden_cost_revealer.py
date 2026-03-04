"""Hidden Cost Revealer - Detects and classifies all fees in loan agreements."""

import re
from typing import List, Dict, Optional
from pydantic import BaseModel


class Fee(BaseModel):
    """Represents a detected fee."""
    type: str
    amount: str
    description: str
    location: Optional[str] = None


class CostAnalysis(BaseModel):
    """Complete cost analysis of a loan agreement."""
    loan_amount: Optional[str] = None
    fees: List[Fee] = []
    total_fees: str = "0"
    interest_amount: Optional[str] = None
    total_cost: str = "0"
    effective_rate: Optional[str] = None


class HiddenCostRevealer:
    """Analyzes loan agreements to reveal all hidden costs and fees."""
    
    def __init__(self):
        """Initialize the hidden cost revealer."""
        self.fee_keywords = {
            "processing": ["processing fee", "origination fee", "application fee", "setup fee"],
            "insurance": ["insurance premium", "insurance fee", "coverage fee"],
            "administrative": ["administrative fee", "admin fee", "service charge", "handling fee"],
            "late_payment": ["late fee", "late payment", "penalty", "overdue charge"],
            "prepayment": ["prepayment penalty", "early payment fee", "prepayment charge"],
            "documentation": ["documentation fee", "document charge", "paperwork fee"],
            "other": ["miscellaneous", "other charges", "additional fee"]
        }
    
    def analyze_costs(self, contract_text: str) -> CostAnalysis:
        """
        Analyze contract text to detect all costs and fees.
        
        Args:
            contract_text: The loan agreement text
            
        Returns:
            CostAnalysis with all detected costs
        """
        # Extract loan amount
        loan_amount = self._extract_loan_amount(contract_text)
        
        # Extract all monetary values
        monetary_values = self._extract_monetary_values(contract_text)
        
        # Classify fees
        fees = self._classify_fees(contract_text, monetary_values)
        
        # Calculate totals
        total_fees = self._calculate_total_fees(fees)
        interest_amount = self._extract_interest_amount(contract_text)
        total_cost = self._calculate_total_cost(loan_amount, total_fees, interest_amount)
        effective_rate = self._calculate_effective_rate(loan_amount, total_cost)
        
        return CostAnalysis(
            loan_amount=loan_amount,
            fees=fees,
            total_fees=total_fees,
            interest_amount=interest_amount,
            total_cost=total_cost,
            effective_rate=effective_rate
        )
    
    def _extract_loan_amount(self, text: str) -> Optional[str]:
        """Extract the principal loan amount."""
        patterns = [
            r'loan amount[:\s]+\$?([\d,]+(?:\.\d{2})?)',
            r'principal[:\s]+\$?([\d,]+(?:\.\d{2})?)',
            r'sum of[:\s]+\$?([\d,]+(?:\.\d{2})?)',
            r'\$?([\d,]+(?:\.\d{2})?)\s*\(.*loan amount.*\)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = match.group(1)
                return f"${amount}"
        
        return None
    
    def _extract_monetary_values(self, text: str) -> List[Dict[str, str]]:
        """Extract all monetary values from text."""
        # Pattern to match currency amounts
        pattern = r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)|(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:dollars|USD|\$)'
        
        matches = []
        for match in re.finditer(pattern, text, re.IGNORECASE):
            amount = match.group(1) or match.group(2)
            # Get surrounding context (50 chars before and after)
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end]
            
            matches.append({
                "amount": f"${amount}",
                "context": context.strip(),
                "position": match.start()
            })
        
        return matches
    
    def _classify_fees(self, text: str, monetary_values: List[Dict[str, str]]) -> List[Fee]:
        """Classify detected monetary values as specific fee types."""
        fees = []
        text_lower = text.lower()
        
        for value in monetary_values:
            context_lower = value["context"].lower()
            amount = value["amount"]
            
            # Skip if this looks like the loan amount
            if any(keyword in context_lower for keyword in ["loan amount", "principal sum", "borrowing"]):
                continue
            
            # Try to classify the fee
            fee_type = "other"
            description = "Unclassified fee"
            
            for fee_category, keywords in self.fee_keywords.items():
                for keyword in keywords:
                    if keyword in context_lower:
                        fee_type = fee_category
                        description = keyword.title()
                        break
                if fee_type != "other":
                    break
            
            # Extract more context for description
            if fee_type == "other":
                # Try to extract a better description from context
                desc_match = re.search(r'([a-z\s]+)\s*(?:fee|charge|cost|premium)', context_lower)
                if desc_match:
                    description = desc_match.group(1).strip().title() + " Fee"
            
            fees.append(Fee(
                type=fee_type,
                amount=amount,
                description=description,
                location=value["context"][:100]
            ))
        
        return fees
    
    def _calculate_total_fees(self, fees: List[Fee]) -> str:
        """Calculate total of all fees."""
        total = 0.0
        
        for fee in fees:
            # Extract numeric value
            amount_str = fee.amount.replace("$", "").replace(",", "")
            try:
                total += float(amount_str)
            except ValueError:
                continue
        
        return f"${total:,.2f}"
    
    def _extract_interest_amount(self, text: str) -> Optional[str]:
        """Extract total interest amount if mentioned."""
        patterns = [
            r'total interest[:\s]+\$?([\d,]+(?:\.\d{2})?)',
            r'interest charge[:\s]+\$?([\d,]+(?:\.\d{2})?)',
            r'interest.*\$?([\d,]+(?:\.\d{2})?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = match.group(1)
                return f"${amount}"
        
        return None
    
    def _calculate_total_cost(
        self,
        loan_amount: Optional[str],
        total_fees: str,
        interest_amount: Optional[str]
    ) -> str:
        """Calculate total cost of the loan."""
        try:
            loan = float(loan_amount.replace("$", "").replace(",", "")) if loan_amount else 0
            fees = float(total_fees.replace("$", "").replace(",", ""))
            interest = float(interest_amount.replace("$", "").replace(",", "")) if interest_amount else 0
            
            total = loan + fees + interest
            return f"${total:,.2f}"
        except (ValueError, AttributeError):
            return "$0.00"
    
    def _calculate_effective_rate(
        self,
        loan_amount: Optional[str],
        total_cost: str
    ) -> Optional[str]:
        """Calculate effective cost as percentage of loan amount."""
        try:
            if not loan_amount:
                return None
            
            loan = float(loan_amount.replace("$", "").replace(",", ""))
            cost = float(total_cost.replace("$", "").replace(",", ""))
            
            if loan == 0:
                return None
            
            rate = (cost / loan) * 100
            return f"{rate:.1f}%"
        except (ValueError, AttributeError):
            return None
    
    def format_analysis(self, analysis: CostAnalysis) -> str:
        """Format cost analysis as readable text."""
        lines = []
        lines.append("=" * 50)
        lines.append("HIDDEN COST ANALYSIS")
        lines.append("=" * 50)
        
        if analysis.loan_amount:
            lines.append(f"\nLoan Amount: {analysis.loan_amount}")
        
        if analysis.fees:
            lines.append("\nDetected Fees:")
            lines.append("-" * 50)
            
            # Group fees by type
            fees_by_type = {}
            for fee in analysis.fees:
                if fee.type not in fees_by_type:
                    fees_by_type[fee.type] = []
                fees_by_type[fee.type].append(fee)
            
            for fee_type, fees in fees_by_type.items():
                lines.append(f"\n{fee_type.replace('_', ' ').title()}:")
                for fee in fees:
                    lines.append(f"  • {fee.description}: {fee.amount}")
        
        lines.append("\n" + "-" * 50)
        lines.append(f"Total Fees: {analysis.total_fees}")
        
        if analysis.interest_amount:
            lines.append(f"Total Interest: {analysis.interest_amount}")
        
        lines.append("=" * 50)
        lines.append(f"TOTAL COST: {analysis.total_cost}")
        lines.append("=" * 50)
        
        if analysis.effective_rate:
            lines.append(f"\nEffective Cost: {analysis.effective_rate} of loan amount")
        
        return "\n".join(lines)
