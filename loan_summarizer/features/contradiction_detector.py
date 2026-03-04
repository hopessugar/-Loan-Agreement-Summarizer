"""Contradiction Detector - Identifies inconsistencies in loan agreements."""

import re
from typing import List, Dict, Optional
from pydantic import BaseModel


class Contradiction(BaseModel):
    """A detected contradiction in the contract."""
    type: str  # interest_rate, late_fee, loan_amount, etc.
    values: List[str]
    locations: List[str]
    severity: str  # high, medium, low
    description: str


class ContradictionReport(BaseModel):
    """Complete report of contradictions found."""
    contradictions: List[Contradiction] = []
    total_count: int = 0
    high_severity_count: int = 0
    medium_severity_count: int = 0
    low_severity_count: int = 0


class ContradictionDetector:
    """Detects contradictions and inconsistencies in loan agreements."""
    
    def __init__(self):
        """Initialize the contradiction detector."""
        self.patterns = {
            "interest_rate": [
                r'interest rate.*?(\d+(?:\.\d+)?)\s*%',
                r'APR.*?(\d+(?:\.\d+)?)\s*%',
                r'(\d+(?:\.\d+)?)\s*%\s*(?:per annum|annual)',
            ],
            "late_fee": [
                r'late fee.*?\$?([\d,]+(?:\.\d{2})?)',
                r'late payment.*?\$?([\d,]+(?:\.\d{2})?)',
                r'penalty.*?\$?([\d,]+(?:\.\d{2})?)',
            ],
            "loan_amount": [
                r'loan amount.*?\$?([\d,]+(?:\.\d{2})?)',
                r'principal.*?\$?([\d,]+(?:\.\d{2})?)',
                r'sum of.*?\$?([\d,]+(?:\.\d{2})?)',
            ],
            "payment_amount": [
                r'(?:monthly\s+)?payment.*?\$?([\d,]+(?:\.\d{2})?)',
                r'installment.*?\$?([\d,]+(?:\.\d{2})?)',
            ],
            "term_length": [
                r'(\d+)\s+(?:month|year)s?\s+term',
                r'term of\s+(\d+)\s+(?:month|year)s?',
                r'over\s+(\d+)\s+(?:month|year)s?',
            ],
        }
    
    def detect_contradictions(self, contract_text: str) -> ContradictionReport:
        """
        Detect all contradictions in the contract.
        
        Args:
            contract_text: The loan agreement text
            
        Returns:
            ContradictionReport with all detected contradictions
        """
        contradictions = []
        
        # Check each type of value for contradictions
        for value_type, patterns in self.patterns.items():
            found_contradictions = self._check_value_type(
                contract_text, value_type, patterns
            )
            contradictions.extend(found_contradictions)
        
        # Count by severity
        high_count = sum(1 for c in contradictions if c.severity == "high")
        medium_count = sum(1 for c in contradictions if c.severity == "medium")
        low_count = sum(1 for c in contradictions if c.severity == "low")
        
        return ContradictionReport(
            contradictions=contradictions,
            total_count=len(contradictions),
            high_severity_count=high_count,
            medium_severity_count=medium_count,
            low_severity_count=low_count
        )
    
    def _check_value_type(
        self,
        text: str,
        value_type: str,
        patterns: List[str]
    ) -> List[Contradiction]:
        """Check for contradictions in a specific value type."""
        # Extract all values of this type
        found_values = []
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = match.group(1)
                # Get location context
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                
                # Try to find section number
                section_match = re.search(r'Section\s+(\d+)', text[:match.start()][::-1])
                section = f"Section {section_match.group(1)}" if section_match else f"Position {match.start()}"
                
                found_values.append({
                    "value": value,
                    "location": section,
                    "context": context
                })
        
        # Check for contradictions
        contradictions = []
        
        if len(found_values) > 1:
            # Group by unique values
            unique_values = {}
            for item in found_values:
                val = item["value"]
                if val not in unique_values:
                    unique_values[val] = []
                unique_values[val].append(item)
            
            # If we have multiple different values, that's a contradiction
            if len(unique_values) > 1:
                values = list(unique_values.keys())
                locations = []
                
                for val in values:
                    locs = [item["location"] for item in unique_values[val]]
                    locations.extend(locs[:2])  # Max 2 locations per value
                
                # Determine severity
                severity = self._determine_severity(value_type, values)
                
                # Create description
                description = self._create_description(value_type, values, locations)
                
                contradiction = Contradiction(
                    type=value_type,
                    values=values,
                    locations=locations[:4],  # Max 4 locations total
                    severity=severity,
                    description=description
                )
                contradictions.append(contradiction)
        
        return contradictions
    
    def _determine_severity(self, value_type: str, values: List[str]) -> str:
        """Determine severity of contradiction."""
        # Critical financial terms are high severity
        if value_type in ["interest_rate", "loan_amount", "term_length"]:
            return "high"
        
        # Fees and payments are medium severity
        elif value_type in ["late_fee", "payment_amount"]:
            return "medium"
        
        # Everything else is low severity
        else:
            return "low"
    
    def _create_description(
        self,
        value_type: str,
        values: List[str],
        locations: List[str]
    ) -> str:
        """Create human-readable description of contradiction."""
        type_names = {
            "interest_rate": "Interest Rate",
            "late_fee": "Late Fee",
            "loan_amount": "Loan Amount",
            "payment_amount": "Payment Amount",
            "term_length": "Loan Term",
        }
        
        type_name = type_names.get(value_type, value_type.replace("_", " ").title())
        
        if len(values) == 2:
            return f"{type_name} is listed as {values[0]} in one place and {values[1]} in another"
        else:
            values_str = ", ".join(values[:-1]) + f", and {values[-1]}"
            return f"{type_name} has multiple conflicting values: {values_str}"
    
    def format_report(self, report: ContradictionReport) -> str:
        """Format contradiction report as readable text."""
        lines = []
        lines.append("=" * 60)
        lines.append("CONTRADICTION DETECTION REPORT")
        lines.append("=" * 60)
        
        if report.total_count == 0:
            lines.append("\n✓ No contradictions detected")
            lines.append("\nThe contract appears to be internally consistent.")
        else:
            lines.append(f"\n⚠️  {report.total_count} contradiction(s) detected")
            lines.append(f"\n  High Severity: {report.high_severity_count}")
            lines.append(f"  Medium Severity: {report.medium_severity_count}")
            lines.append(f"  Low Severity: {report.low_severity_count}")
            
            lines.append("\n" + "-" * 60)
            lines.append("DETAILS:")
            lines.append("-" * 60)
            
            for i, contradiction in enumerate(report.contradictions, 1):
                severity_symbol = {
                    "high": "🔴",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(contradiction.severity, "⚪")
                
                lines.append(f"\n{i}. {severity_symbol} {contradiction.type.replace('_', ' ').title()}")
                lines.append(f"   Severity: {contradiction.severity.upper()}")
                lines.append(f"   {contradiction.description}")
                lines.append(f"   Locations: {', '.join(contradiction.locations)}")
                lines.append(f"   Values: {', '.join(contradiction.values)}")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)
