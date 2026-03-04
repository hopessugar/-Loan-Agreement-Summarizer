"""
Financial Validation Layer - Validates and verifies extracted financial entities.

This module provides a comprehensive validation layer that:
1. Validates entity classifications
2. Verifies source text existence (prevents hallucinations)
3. Checks mathematical consistency
4. Filters invalid entities
5. Provides detailed logging
"""

import logging
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field

from loan_summarizer.extraction.financial_entity_extractor import (
    FinancialEntity,
    EntityType
)
from .mathematical_validator import MathematicalValidator
from .hallucination_detector import HallucinationDetector


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationResult(BaseModel):
    """Result of financial validation."""
    
    valid_entities: List[FinancialEntity] = Field(default_factory=list)
    invalid_entities: List[FinancialEntity] = Field(default_factory=list)
    corrected_entities: List[FinancialEntity] = Field(default_factory=list)
    validation_issues: List[str] = Field(default_factory=list)
    mathematical_issues: List[str] = Field(default_factory=list)
    hallucination_warnings: List[str] = Field(default_factory=list)
    
    total_detected: int = 0
    total_valid: int = 0
    total_invalid: int = 0
    total_corrected: int = 0
    
    accuracy_score: float = 0.0


class FinancialValidator:
    """
    Comprehensive financial validation layer.
    
    Validates extracted financial entities through multiple checks:
    - Entity type validation
    - Source text verification (anti-hallucination)
    - Mathematical consistency
    - Context validation
    - Confidence thresholds
    """
    
    def __init__(
        self,
        min_confidence: float = 0.3,
        enable_math_validation: bool = True,
        enable_hallucination_detection: bool = True,
        enable_logging: bool = True
    ):
        """
        Initialize the financial validator.
        
        Args:
            min_confidence: Minimum confidence threshold (0-1)
            enable_math_validation: Enable mathematical consistency checks
            enable_hallucination_detection: Enable LLM hallucination detection
            enable_logging: Enable detailed logging
        """
        self.min_confidence = min_confidence
        self.enable_math_validation = enable_math_validation
        self.enable_hallucination_detection = enable_hallucination_detection
        self.enable_logging = enable_logging
        
        # Initialize sub-validators
        self.math_validator = MathematicalValidator() if enable_math_validation else None
        self.hallucination_detector = HallucinationDetector() if enable_hallucination_detection else None
        
        # Validation statistics
        self.stats = {
            "total_validated": 0,
            "passed": 0,
            "failed": 0,
            "corrected": 0
        }
    
    def validate(
        self,
        entities: List[FinancialEntity],
        source_text: str
    ) -> ValidationResult:
        """
        Validate a list of financial entities.
        
        Args:
            entities: List of extracted financial entities
            source_text: Original contract text
            
        Returns:
            ValidationResult with validated entities and issues
        """
        if self.enable_logging:
            logger.info(f"Starting validation of {len(entities)} entities")
        
        result = ValidationResult(total_detected=len(entities))
        
        # Step 1: Confidence filtering
        entities = self._filter_by_confidence(entities, result)
        
        # Step 2: Hallucination detection
        if self.enable_hallucination_detection:
            entities = self._detect_hallucinations(entities, source_text, result)
        
        # Step 3: Entity type validation
        entities = self._validate_entity_types(entities, result)
        
        # Step 4: Mathematical consistency validation
        if self.enable_math_validation:
            entities = self._validate_mathematical_consistency(entities, result)
        
        # Step 5: Finalize results
        result.valid_entities = entities
        result.total_valid = len(result.valid_entities)
        result.total_invalid = len(result.invalid_entities)
        result.total_corrected = len(result.corrected_entities)
        
        # Calculate accuracy score
        if result.total_detected > 0:
            result.accuracy_score = result.total_valid / result.total_detected
        
        # Update statistics
        self.stats["total_validated"] += result.total_detected
        self.stats["passed"] += result.total_valid
        self.stats["failed"] += result.total_invalid
        self.stats["corrected"] += result.total_corrected
        
        if self.enable_logging:
            logger.info(f"Validation complete: {result.total_valid}/{result.total_detected} valid")
            logger.info(f"Accuracy: {result.accuracy_score:.2%}")
        
        return result
    
    def _filter_by_confidence(
        self,
        entities: List[FinancialEntity],
        result: ValidationResult
    ) -> List[FinancialEntity]:
        """Filter entities by confidence threshold."""
        valid = []
        
        for entity in entities:
            if entity.confidence >= self.min_confidence:
                valid.append(entity)
            else:
                result.invalid_entities.append(entity)
                result.validation_issues.append(
                    f"Low confidence: {entity.type.value} = {entity.value} "
                    f"(confidence: {entity.confidence:.2%})"
                )
                
                if self.enable_logging:
                    logger.debug(f"Filtered out low confidence entity: {entity.type.value}")
        
        return valid
    
    def _detect_hallucinations(
        self,
        entities: List[FinancialEntity],
        source_text: str,
        result: ValidationResult
    ) -> List[FinancialEntity]:
        """Detect and filter LLM hallucinations."""
        if not self.hallucination_detector:
            return entities
        
        valid = []
        
        for entity in entities:
            is_hallucination, reason = self.hallucination_detector.check_entity(
                entity, source_text
            )
            
            if is_hallucination:
                result.invalid_entities.append(entity)
                result.hallucination_warnings.append(
                    f"Possible hallucination: {entity.type.value} = {entity.value} - {reason}"
                )
                
                if self.enable_logging:
                    logger.warning(f"Hallucination detected: {entity.type.value} = {entity.value}")
            else:
                valid.append(entity)
        
        return valid
    
    def _validate_entity_types(
        self,
        entities: List[FinancialEntity],
        result: ValidationResult
    ) -> List[FinancialEntity]:
        """Validate entity type classifications."""
        valid = []
        
        for entity in entities:
            # Check if entity type is appropriate for the value
            is_valid, issue = self._check_entity_type_validity(entity)
            
            if is_valid:
                valid.append(entity)
            else:
                result.invalid_entities.append(entity)
                result.validation_issues.append(issue)
                
                if self.enable_logging:
                    logger.debug(f"Invalid entity type: {issue}")
        
        return valid
    
    def _check_entity_type_validity(
        self,
        entity: FinancialEntity
    ) -> Tuple[bool, Optional[str]]:
        """Check if entity type is valid for the value."""
        
        # Interest rates should be percentages
        if entity.type == EntityType.INTEREST_RATE:
            if '%' not in entity.value:
                return False, f"Interest rate missing %: {entity.value}"
        
        # Currency values should have currency symbols
        currency_types = [
            EntityType.LOAN_AMOUNT,
            EntityType.MONTHLY_PAYMENT,
            EntityType.LATE_FEE,
            EntityType.PROCESSING_FEE,
            EntityType.INSURANCE_FEE,
            EntityType.ADMINISTRATIVE_FEE,
            EntityType.DOCUMENTATION_FEE,
            EntityType.PREPAYMENT_PENALTY,
            EntityType.TOTAL_COST
        ]
        
        if entity.type in currency_types:
            if not any(symbol in entity.value for symbol in ['₹', '$', 'Rs']):
                # Allow if it's a pure number (will be formatted later)
                try:
                    float(entity.value.replace(',', ''))
                except ValueError:
                    return False, f"Currency value invalid format: {entity.value}"
        
        # Duration should have time units
        if entity.type == EntityType.REPAYMENT_DURATION:
            if not any(unit in entity.value.lower() for unit in ['month', 'year', 'day']):
                return False, f"Duration missing time unit: {entity.value}"
        
        return True, None
    
    def _validate_mathematical_consistency(
        self,
        entities: List[FinancialEntity],
        result: ValidationResult
    ) -> List[FinancialEntity]:
        """Validate mathematical consistency between entities."""
        if not self.math_validator:
            return entities
        
        # Check consistency
        issues, corrections = self.math_validator.validate_consistency(entities)
        
        # Add issues to result
        result.mathematical_issues.extend(issues)
        
        # Apply corrections if any
        if corrections:
            for correction in corrections:
                result.corrected_entities.append(correction)
                
                if self.enable_logging:
                    logger.info(f"Applied correction: {correction.type.value} = {correction.value}")
        
        return entities
    
    def get_statistics(self) -> Dict[str, any]:
        """Get validation statistics."""
        stats = self.stats.copy()
        
        if stats["total_validated"] > 0:
            stats["pass_rate"] = stats["passed"] / stats["total_validated"]
            stats["fail_rate"] = stats["failed"] / stats["total_validated"]
            stats["correction_rate"] = stats["corrected"] / stats["total_validated"]
        else:
            stats["pass_rate"] = 0.0
            stats["fail_rate"] = 0.0
            stats["correction_rate"] = 0.0
        
        return stats
    
    def reset_statistics(self):
        """Reset validation statistics."""
        self.stats = {
            "total_validated": 0,
            "passed": 0,
            "failed": 0,
            "corrected": 0
        }
    
    def format_validation_report(self, result: ValidationResult) -> str:
        """Format validation result as readable report."""
        lines = []
        lines.append("=" * 70)
        lines.append("FINANCIAL VALIDATION REPORT")
        lines.append("=" * 70)
        
        lines.append(f"\nTotal Entities Detected: {result.total_detected}")
        lines.append(f"Valid Entities: {result.total_valid}")
        lines.append(f"Invalid Entities: {result.total_invalid}")
        lines.append(f"Corrected Entities: {result.total_corrected}")
        lines.append(f"Accuracy Score: {result.accuracy_score:.2%}")
        
        if result.validation_issues:
            lines.append("\n" + "-" * 70)
            lines.append("VALIDATION ISSUES:")
            lines.append("-" * 70)
            for issue in result.validation_issues:
                lines.append(f"  • {issue}")
        
        if result.hallucination_warnings:
            lines.append("\n" + "-" * 70)
            lines.append("HALLUCINATION WARNINGS:")
            lines.append("-" * 70)
            for warning in result.hallucination_warnings:
                lines.append(f"  ⚠️  {warning}")
        
        if result.mathematical_issues:
            lines.append("\n" + "-" * 70)
            lines.append("MATHEMATICAL ISSUES:")
            lines.append("-" * 70)
            for issue in result.mathematical_issues:
                lines.append(f"  • {issue}")
        
        if result.corrected_entities:
            lines.append("\n" + "-" * 70)
            lines.append("CORRECTIONS APPLIED:")
            lines.append("-" * 70)
            for entity in result.corrected_entities:
                lines.append(f"  ✓ {entity.type.value}: {entity.value}")
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)
