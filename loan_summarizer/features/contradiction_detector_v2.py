"""
Contradiction Detector V2 - Improved accuracy with entity-type filtering.

This version only compares entities of the same type, eliminating false positives
from comparing unrelated numbers (e.g., interest rates vs. dates).
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from loan_summarizer.extraction.financial_entity_extractor import (
    FinancialEntityExtractor,
    FinancialEntity,
    EntityType
)
from loan_summarizer.extraction.clause_segmenter import ClauseSegmenter


class Contradiction(BaseModel):
    """A detected contradiction with full context."""
    type: str = Field(..., description="Type of entity with contradiction")
    values: List[str] = Field(..., description="Conflicting values")
    locations: List[str] = Field(..., description="Source clauses")
    verbatim_texts: List[str] = Field(..., description="Exact text from contract")
    severity: str = Field(..., description="Severity: high, medium, low")
    description: str = Field(..., description="Human-readable description")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in contradiction")


class ContradictionReport(BaseModel):
    """Complete report of contradictions found."""
    contradictions: List[Contradiction] = []
    total_count: int = 0
    high_severity_count: int = 0
    medium_severity_count: int = 0
    low_severity_count: int = 0
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ContradictionDetectorV2:
    """
    Improved contradiction detector using entity-type filtering.
    
    Key improvements:
    1. Only compares entities of the same type
    2. Uses confidence scores to filter false positives
    3. Provides source clause tracking
    4. Handles numeric comparisons properly
    5. Distinguishes between true contradictions and variations
    """
    
    def __init__(self):
        """Initialize the improved contradiction detector."""
        self.extractor = FinancialEntityExtractor()
        self.segmenter = ClauseSegmenter()
        
        # Severity mapping for entity types
        self.severity_map = {
            EntityType.LOAN_AMOUNT: "high",
            EntityType.INTEREST_RATE: "high",
            EntityType.MONTHLY_PAYMENT: "high",
            EntityType.REPAYMENT_DURATION: "high",
            EntityType.LATE_FEE: "medium",
            EntityType.PROCESSING_FEE: "medium",
            EntityType.INSURANCE_FEE: "medium",
            EntityType.ADMINISTRATIVE_FEE: "medium",
            EntityType.DOCUMENTATION_FEE: "low",
            EntityType.PREPAYMENT_PENALTY: "medium"
        }
        
        # Tolerance for numeric comparisons (percentage)
        self.numeric_tolerance = 0.01  # 1% tolerance
    
    def detect_contradictions(self, contract_text: str) -> ContradictionReport:
        """
        Detect contradictions in the contract.
        
        Args:
            contract_text: The loan agreement text
            
        Returns:
            ContradictionReport with all detected contradictions
        """
        # Segment contract
        clauses = self.segmenter.segment(contract_text)
        
        # Extract entities from each clause
        all_entities = []
        for clause in clauses:
            entities = self.extractor.extract_entities(clause.text, clause.clause_id)
            all_entities.extend(entities)
        
        # Group entities by type
        entities_by_type = self._group_by_type(all_entities)
        
        # Check each type for contradictions
        contradictions = []
        for entity_type, entities in entities_by_type.items():
            if len(entities) > 1:
                type_contradictions = self._check_entity_type(entity_type, entities)
                contradictions.extend(type_contradictions)
        
        # Count by severity
        high_count = sum(1 for c in contradictions if c.severity == "high")
        medium_count = sum(1 for c in contradictions if c.severity == "medium")
        low_count = sum(1 for c in contradictions if c.severity == "low")
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(contradictions)
        
        return ContradictionReport(
            contradictions=contradictions,
            total_count=len(contradictions),
            high_severity_count=high_count,
            medium_severity_count=medium_count,
            low_severity_count=low_count,
            overall_confidence=overall_confidence
        )
    
    def _group_by_type(
        self,
        entities: List[FinancialEntity]
    ) -> Dict[EntityType, List[FinancialEntity]]:
        """Group entities by type."""
        grouped = {}
        
        for entity in entities:
            if entity.type not in grouped:
                grouped[entity.type] = []
            grouped[entity.type].append(entity)
        
        return grouped
    
    def _check_entity_type(
        self,
        entity_type: EntityType,
        entities: List[FinancialEntity]
    ) -> List[Contradiction]:
        """Check for contradictions within a specific entity type."""
        contradictions = []
        
        # Filter out low-confidence entities
        high_confidence_entities = [e for e in entities if e.confidence >= 0.5]
        
        if len(high_confidence_entities) <= 1:
            return contradictions
        
        # Group by unique values
        value_groups = {}
        for entity in high_confidence_entities:
            # Normalize value for comparison
            normalized = self._normalize_value(entity.value, entity_type)
            
            if normalized not in value_groups:
                value_groups[normalized] = []
            value_groups[normalized].append(entity)
        
        # Check if we have multiple different values
        if len(value_groups) > 1:
            # Check if values are within tolerance (for numeric types)
            if self._is_numeric_type(entity_type):
                if not self._values_within_tolerance(list(value_groups.keys()), entity_type):
                    # True contradiction
                    contradiction = self._create_contradiction(
                        entity_type, value_groups
                    )
                    contradictions.append(contradiction)
            else:
                # Non-numeric type - any difference is a contradiction
                contradiction = self._create_contradiction(
                    entity_type, value_groups
                )
                contradictions.append(contradiction)
        
        return contradictions
    
    def _normalize_value(self, value: str, entity_type: EntityType) -> str:
        """Normalize value for comparison."""
        # Remove currency symbols and whitespace
        normalized = value.replace('₹', '').replace('$', '').replace(',', '').strip()
        
        # For percentages, ensure consistent format
        if '%' in value:
            normalized = normalized.replace('%', '').strip()
        
        return normalized
    
    def _is_numeric_type(self, entity_type: EntityType) -> bool:
        """Check if entity type is numeric."""
        numeric_types = [
            EntityType.LOAN_AMOUNT,
            EntityType.INTEREST_RATE,
            EntityType.MONTHLY_PAYMENT,
            EntityType.LATE_FEE,
            EntityType.PROCESSING_FEE,
            EntityType.INSURANCE_FEE,
            EntityType.ADMINISTRATIVE_FEE,
            EntityType.DOCUMENTATION_FEE,
            EntityType.PREPAYMENT_PENALTY,
            EntityType.TOTAL_COST
        ]
        
        return entity_type in numeric_types
    
    def _values_within_tolerance(
        self,
        values: List[str],
        entity_type: EntityType
    ) -> bool:
        """Check if numeric values are within tolerance."""
        try:
            # Convert to floats
            numeric_values = [float(v) for v in values]
            
            # Check if all values are within tolerance of each other
            min_val = min(numeric_values)
            max_val = max(numeric_values)
            
            if min_val == 0:
                return False  # Avoid division by zero
            
            # Calculate percentage difference
            diff_percent = (max_val - min_val) / min_val
            
            return diff_percent <= self.numeric_tolerance
        
        except ValueError:
            # If conversion fails, treat as contradiction
            return False
    
    def _create_contradiction(
        self,
        entity_type: EntityType,
        value_groups: Dict[str, List[FinancialEntity]]
    ) -> Contradiction:
        """Create a contradiction object."""
        # Get unique values
        values = list(value_groups.keys())
        
        # Get locations and verbatim texts
        locations = []
        verbatim_texts = []
        confidences = []
        
        for value, entities in value_groups.items():
            # Take up to 2 entities per value
            for entity in entities[:2]:
                locations.append(entity.source_clause)
                verbatim_texts.append(entity.verbatim_text)
                confidences.append(entity.confidence)
        
        # Determine severity
        severity = self.severity_map.get(entity_type, "low")
        
        # Create description
        description = self._create_description(entity_type, values)
        
        # Calculate confidence (average of entity confidences)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        
        return Contradiction(
            type=entity_type.value,
            values=[self._format_value(v, entity_type) for v in values],
            locations=locations[:4],  # Max 4 locations
            verbatim_texts=verbatim_texts[:4],
            severity=severity,
            description=description,
            confidence=avg_confidence
        )
    
    def _format_value(self, value: str, entity_type: EntityType) -> str:
        """Format value for display."""
        # Add back currency symbols or percentage signs
        if entity_type == EntityType.INTEREST_RATE:
            return f"{value}%"
        elif entity_type in [
            EntityType.LOAN_AMOUNT,
            EntityType.MONTHLY_PAYMENT,
            EntityType.LATE_FEE,
            EntityType.PROCESSING_FEE,
            EntityType.INSURANCE_FEE,
            EntityType.ADMINISTRATIVE_FEE,
            EntityType.DOCUMENTATION_FEE,
            EntityType.PREPAYMENT_PENALTY,
            EntityType.TOTAL_COST
        ]:
            return f"₹{value}"
        else:
            return value
    
    def _create_description(
        self,
        entity_type: EntityType,
        values: List[str]
    ) -> str:
        """Create human-readable description."""
        type_names = {
            EntityType.LOAN_AMOUNT: "Loan Amount",
            EntityType.INTEREST_RATE: "Interest Rate",
            EntityType.MONTHLY_PAYMENT: "Monthly Payment",
            EntityType.LATE_FEE: "Late Fee",
            EntityType.PROCESSING_FEE: "Processing Fee",
            EntityType.INSURANCE_FEE: "Insurance Fee",
            EntityType.ADMINISTRATIVE_FEE: "Administrative Fee",
            EntityType.DOCUMENTATION_FEE: "Documentation Fee",
            EntityType.PREPAYMENT_PENALTY: "Prepayment Penalty",
            EntityType.REPAYMENT_DURATION: "Repayment Duration",
            EntityType.TOTAL_COST: "Total Cost"
        }
        
        type_name = type_names.get(entity_type, entity_type.value.replace('_', ' ').title())
        
        formatted_values = [self._format_value(v, entity_type) for v in values]
        
        if len(formatted_values) == 2:
            return f"{type_name} is stated as {formatted_values[0]} in one clause and {formatted_values[1]} in another clause"
        else:
            values_str = ", ".join(formatted_values[:-1]) + f", and {formatted_values[-1]}"
            return f"{type_name} has multiple conflicting values: {values_str}"
    
    def _calculate_overall_confidence(
        self,
        contradictions: List[Contradiction]
    ) -> float:
        """Calculate overall confidence in contradiction detection."""
        if not contradictions:
            return 1.0  # High confidence that there are no contradictions
        
        # Average confidence of all contradictions
        avg_confidence = sum(c.confidence for c in contradictions) / len(contradictions)
        
        return avg_confidence
    
    def format_report(self, report: ContradictionReport) -> str:
        """Format contradiction report as readable text."""
        lines = []
        lines.append("=" * 70)
        lines.append("CONTRADICTION DETECTION REPORT (V2 - Improved Accuracy)")
        lines.append("=" * 70)
        lines.append(f"\nOverall Confidence: {report.overall_confidence:.1%}\n")
        
        if report.total_count == 0:
            lines.append("✓ No contradictions detected")
            lines.append("\nThe contract appears to be internally consistent.")
        else:
            lines.append(f"⚠️  {report.total_count} contradiction(s) detected\n")
            lines.append(f"  High Severity: {report.high_severity_count}")
            lines.append(f"  Medium Severity: {report.medium_severity_count}")
            lines.append(f"  Low Severity: {report.low_severity_count}")
            
            lines.append("\n" + "-" * 70)
            lines.append("DETAILS:")
            lines.append("-" * 70)
            
            for i, contradiction in enumerate(report.contradictions, 1):
                severity_symbol = {
                    "high": "🔴",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(contradiction.severity, "⚪")
                
                lines.append(f"\n{i}. {severity_symbol} {contradiction.type.replace('_', ' ').title()}")
                lines.append(f"   Severity: {contradiction.severity.upper()}")
                lines.append(f"   Confidence: {contradiction.confidence:.1%}")
                lines.append(f"   {contradiction.description}")
                lines.append(f"\n   Conflicting Values:")
                for j, (value, location, verbatim) in enumerate(zip(
                    contradiction.values,
                    contradiction.locations,
                    contradiction.verbatim_texts
                ), 1):
                    lines.append(f"     {j}. {value}")
                    lines.append(f"        Location: {location}")
                    lines.append(f"        Context: {verbatim[:100]}...")
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)
