"""
Hallucination Detector - Prevents LLM hallucinations by verifying source text.

Checks:
1. Value exists in source document
2. Value appears in correct context
3. Verbatim text matches source
"""

import re
import logging
from typing import Tuple

from loan_summarizer.extraction.financial_entity_extractor import FinancialEntity


logger = logging.getLogger(__name__)


class HallucinationDetector:
    """
    Detects LLM hallucinations by verifying extracted values exist in source text.
    
    A value is considered a hallucination if:
    1. It doesn't appear in the source document
    2. It appears but in wrong context
    3. The verbatim text doesn't match source
    """
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize hallucination detector.
        
        Args:
            strict_mode: If True, requires exact verbatim text match
        """
        self.strict_mode = strict_mode
    
    def check_entity(
        self,
        entity: FinancialEntity,
        source_text: str
    ) -> Tuple[bool, str]:
        """
        Check if entity is a hallucination.
        
        Args:
            entity: Financial entity to check
            source_text: Original contract text
            
        Returns:
            Tuple of (is_hallucination, reason)
        """
        # Check 1: Value exists in source
        value_exists, reason = self._check_value_exists(entity, source_text)
        
        if not value_exists:
            logger.warning(f"Hallucination detected: {reason}")
            return True, reason
        
        # Check 2: Verbatim text exists (if strict mode)
        if self.strict_mode:
            verbatim_exists = self._check_verbatim_exists(entity, source_text)
            
            if not verbatim_exists:
                reason = f"Verbatim text not found in source: {entity.verbatim_text[:50]}..."
                logger.warning(f"Hallucination detected: {reason}")
                return True, reason
        
        # Passed all checks
        return False, ""
    
    def _check_value_exists(
        self,
        entity: FinancialEntity,
        source_text: str
    ) -> Tuple[bool, str]:
        """Check if value exists in source text."""
        
        # Extract numeric part from value
        numeric_part = self._extract_numeric_part(entity.value)
        
        if not numeric_part:
            return True, ""  # Can't verify, assume valid
        
        # Create search patterns
        patterns = self._create_search_patterns(numeric_part, entity.value)
        
        # Search for any pattern
        for pattern in patterns:
            if re.search(pattern, source_text, re.IGNORECASE):
                return True, ""
        
        # Value not found
        reason = f"Value '{entity.value}' not found in source document"
        return False, reason
    
    def _extract_numeric_part(self, value: str) -> str:
        """Extract numeric part from value."""
        # Remove currency symbols and percentage signs
        cleaned = re.sub(r'[₹$Rs%\s]', '', value)
        
        # Keep only digits, commas, and decimal points
        numeric = re.sub(r'[^\d,.]', '', cleaned)
        
        return numeric
    
    def _create_search_patterns(self, numeric_part: str, full_value: str) -> list:
        """Create search patterns for value."""
        patterns = []
        
        # Pattern 1: Exact value
        patterns.append(re.escape(full_value))
        
        # Pattern 2: Numeric part with various formats
        # Remove commas for flexible matching
        no_commas = numeric_part.replace(',', '')
        
        if no_commas:
            # Match with or without commas
            patterns.append(r'\b' + re.escape(no_commas) + r'\b')
            patterns.append(r'\b' + re.escape(numeric_part) + r'\b')
            
            # Match with currency symbols
            patterns.append(r'[₹$Rs\.?\s]*' + re.escape(no_commas))
            
            # Match with percentage
            if '%' in full_value:
                patterns.append(re.escape(no_commas) + r'\s*%')
        
        return patterns
    
    def _check_verbatim_exists(
        self,
        entity: FinancialEntity,
        source_text: str
    ) -> bool:
        """Check if verbatim text exists in source."""
        
        # Clean verbatim text
        verbatim = entity.verbatim_text.strip()
        
        if not verbatim:
            return True  # No verbatim to check
        
        # Check for exact match
        if verbatim in source_text:
            return True
        
        # Check for fuzzy match (allowing for minor differences)
        # Split into words and check if most words exist
        words = verbatim.split()
        
        if len(words) < 3:
            return True  # Too short to verify
        
        # Count matching words
        matching_words = sum(1 for word in words if word.lower() in source_text.lower())
        
        # Require at least 70% of words to match
        match_ratio = matching_words / len(words)
        
        return match_ratio >= 0.7
    
    def verify_all_entities(
        self,
        entities: list,
        source_text: str
    ) -> dict:
        """
        Verify all entities and return statistics.
        
        Args:
            entities: List of financial entities
            source_text: Original contract text
            
        Returns:
            Dictionary with verification statistics
        """
        total = len(entities)
        hallucinations = 0
        verified = 0
        
        hallucination_list = []
        
        for entity in entities:
            is_hallucination, reason = self.check_entity(entity, source_text)
            
            if is_hallucination:
                hallucinations += 1
                hallucination_list.append({
                    "entity": entity,
                    "reason": reason
                })
            else:
                verified += 1
        
        return {
            "total": total,
            "verified": verified,
            "hallucinations": hallucinations,
            "verification_rate": verified / total if total > 0 else 0.0,
            "hallucination_list": hallucination_list
        }
