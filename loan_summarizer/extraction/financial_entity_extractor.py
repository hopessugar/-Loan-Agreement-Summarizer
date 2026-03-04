"""
Financial Entity Extractor - Accurate extraction of financial values from loan agreements.

This module implements a hybrid extraction approach:
1. Regex-based detection of financial patterns
2. Context-aware filtering using keyword proximity
3. Entity type classification
4. Confidence scoring
"""

import re
from enum import Enum
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field


class EntityType(str, Enum):
    """Types of financial entities that can be extracted."""
    LOAN_AMOUNT = "loan_amount"
    INTEREST_RATE = "interest_rate"
    MONTHLY_PAYMENT = "monthly_payment"
    LATE_FEE = "late_fee"
    PROCESSING_FEE = "processing_fee"
    INSURANCE_FEE = "insurance_fee"
    ADMINISTRATIVE_FEE = "administrative_fee"
    PENALTY_INTEREST = "penalty_interest"
    REPAYMENT_DURATION = "repayment_duration"
    REPAYMENT_START_DATE = "repayment_start_date"
    PREPAYMENT_PENALTY = "prepayment_penalty"
    DOCUMENTATION_FEE = "documentation_fee"
    TOTAL_COST = "total_cost"
    UNKNOWN = "unknown"


class FinancialEntity(BaseModel):
    """Represents a detected financial entity with full context."""
    
    type: EntityType = Field(..., description="Type of financial entity")
    value: str = Field(..., description="Extracted value (formatted)")
    raw_value: str = Field(..., description="Raw extracted value")
    source_clause: str = Field(..., description="Source clause identifier")
    verbatim_text: str = Field(..., description="Exact text from contract")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    position: int = Field(..., description="Character position in document")
    is_derived: bool = Field(default=False, description="Whether this is a calculated value")
    calculation_source: Optional[List[str]] = Field(default=None, description="Source entities for derived values")


class FinancialEntityExtractor:
    """
    Extracts financial entities from loan agreements with high accuracy.
    
    Uses a multi-stage approach:
    1. Pattern matching for financial values
    2. Context analysis for entity type classification
    3. Filtering to remove non-financial numbers
    4. Confidence scoring
    """
    
    def __init__(self):
        """Initialize the financial entity extractor."""
        
        # Financial value patterns
        self.currency_patterns = [
            r'(?:INR|Rs\.?|₹)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # Indian Rupee
            r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # Dollar
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:rupees?|dollars?)',  # Word form
        ]
        
        self.percentage_pattern = r'(\d+(?:\.\d+)?)\s*%'
        
        # Context keywords for each entity type
        self.entity_keywords = {
            EntityType.LOAN_AMOUNT: [
                "loan amount", "principal", "principal amount", "sum of",
                "borrowing", "advance", "sanctioned amount", "disbursed amount"
            ],
            EntityType.INTEREST_RATE: [
                "interest rate", "rate of interest", "APR", "annual percentage rate",
                "per annum", "p.a.", "interest", "rate"
            ],
            EntityType.MONTHLY_PAYMENT: [
                "monthly payment", "installment", "EMI", "equated monthly installment",
                "monthly installment", "payment", "repayment"
            ],
            EntityType.LATE_FEE: [
                "late fee", "late payment", "overdue", "penalty", "late charge",
                "delayed payment", "default charge"
            ],
            EntityType.PROCESSING_FEE: [
                "processing fee", "origination fee", "application fee", "setup fee",
                "processing charge", "handling charge"
            ],
            EntityType.INSURANCE_FEE: [
                "insurance", "insurance premium", "coverage", "insurance fee",
                "insurance charge"
            ],
            EntityType.ADMINISTRATIVE_FEE: [
                "administrative fee", "admin fee", "service charge", "service fee",
                "administrative charge"
            ],
            EntityType.DOCUMENTATION_FEE: [
                "documentation fee", "document charge", "paperwork fee",
                "documentation charge", "stamp duty"
            ],
            EntityType.PREPAYMENT_PENALTY: [
                "prepayment penalty", "early payment", "foreclosure", "prepayment charge",
                "early repayment"
            ],
            EntityType.TOTAL_COST: [
                "total cost", "total amount", "total repayment", "total payable",
                "aggregate amount"
            ]
        }
        
        # Keywords that indicate NON-financial numbers (to filter out)
        self.exclusion_keywords = [
            "days", "day", "months", "month", "years", "year",
            "section", "clause", "paragraph", "page", "article",
            "dated", "date", "march", "april", "may", "june", "july",
            "august", "september", "october", "november", "december",
            "january", "february", "monday", "tuesday", "wednesday",
            "thursday", "friday", "saturday", "sunday",
            "first", "second", "third", "fourth", "fifth",
            "witness", "party", "parties", "signatory"
        ]
        
        # Minimum confidence threshold
        self.min_confidence = 0.3
    
    def extract_entities(
        self,
        contract_text: str,
        clause_id: Optional[str] = None
    ) -> List[FinancialEntity]:
        """
        Extract all financial entities from contract text.
        
        Args:
            contract_text: The loan agreement text
            clause_id: Optional clause identifier for source tracking
            
        Returns:
            List of detected financial entities
        """
        entities = []
        
        # Extract currency values
        currency_entities = self._extract_currency_values(contract_text, clause_id)
        entities.extend(currency_entities)
        
        # Extract percentages (interest rates)
        percentage_entities = self._extract_percentages(contract_text, clause_id)
        entities.extend(percentage_entities)
        
        # Extract durations (repayment terms)
        duration_entities = self._extract_durations(contract_text, clause_id)
        entities.extend(duration_entities)
        
        # Filter out low-confidence entities
        entities = [e for e in entities if e.confidence >= self.min_confidence]
        
        # Sort by position
        entities.sort(key=lambda e: e.position)
        
        return entities
    
    def _extract_currency_values(
        self,
        text: str,
        clause_id: Optional[str]
    ) -> List[FinancialEntity]:
        """Extract currency values from text."""
        entities = []
        
        for pattern in self.currency_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                raw_value = match.group(1)
                position = match.start()
                
                # Get context (100 chars before and after)
                context_start = max(0, position - 100)
                context_end = min(len(text), position + 100)
                context = text[context_start:context_end]
                
                # Check if this is a financial value (not a date, section number, etc.)
                if self._is_excluded_context(context):
                    continue
                
                # Classify entity type based on context
                entity_type, confidence = self._classify_currency_entity(context)
                
                # Extract verbatim text (sentence containing the value)
                verbatim = self._extract_verbatim_text(text, position)
                
                # Format value
                formatted_value = self._format_currency(raw_value, match.group(0))
                
                entity = FinancialEntity(
                    type=entity_type,
                    value=formatted_value,
                    raw_value=raw_value,
                    source_clause=clause_id or "Unknown",
                    verbatim_text=verbatim,
                    confidence=confidence,
                    position=position
                )
                
                entities.append(entity)
        
        return entities
    
    def _extract_percentages(
        self,
        text: str,
        clause_id: Optional[str]
    ) -> List[FinancialEntity]:
        """Extract percentage values (interest rates)."""
        entities = []
        
        for match in re.finditer(self.percentage_pattern, text, re.IGNORECASE):
            raw_value = match.group(1)
            position = match.start()
            
            # Get context
            context_start = max(0, position - 100)
            context_end = min(len(text), position + 100)
            context = text[context_start:context_end]
            
            # Check if this is excluded
            if self._is_excluded_context(context):
                continue
            
            # Check if this is an interest rate
            confidence = self._calculate_keyword_proximity(
                context,
                self.entity_keywords[EntityType.INTEREST_RATE]
            )
            
            if confidence < 0.3:
                continue  # Not an interest rate
            
            # Extract verbatim text
            verbatim = self._extract_verbatim_text(text, position)
            
            entity = FinancialEntity(
                type=EntityType.INTEREST_RATE,
                value=f"{raw_value}%",
                raw_value=raw_value,
                source_clause=clause_id or "Unknown",
                verbatim_text=verbatim,
                confidence=confidence,
                position=position
            )
            
            entities.append(entity)
        
        return entities
    
    def _extract_durations(
        self,
        text: str,
        clause_id: Optional[str]
    ) -> List[FinancialEntity]:
        """Extract repayment durations."""
        entities = []
        
        # Pattern for durations in financial context
        duration_pattern = r'(\d+)\s+(months?|years?)'
        
        for match in re.finditer(duration_pattern, text, re.IGNORECASE):
            raw_value = match.group(1)
            unit = match.group(2)
            position = match.start()
            
            # Get context
            context_start = max(0, position - 100)
            context_end = min(len(text), position + 100)
            context = text[context_start:context_end]
            
            # Only extract if in repayment context
            repayment_keywords = ["repay", "term", "tenure", "period", "duration", "installment"]
            if not any(kw in context.lower() for kw in repayment_keywords):
                continue
            
            # Calculate confidence
            confidence = self._calculate_keyword_proximity(context, repayment_keywords)
            
            if confidence < 0.4:
                continue
            
            # Extract verbatim text
            verbatim = self._extract_verbatim_text(text, position)
            
            entity = FinancialEntity(
                type=EntityType.REPAYMENT_DURATION,
                value=f"{raw_value} {unit}",
                raw_value=raw_value,
                source_clause=clause_id or "Unknown",
                verbatim_text=verbatim,
                confidence=confidence,
                position=position
            )
            
            entities.append(entity)
        
        return entities
    
    def _is_excluded_context(self, context: str) -> bool:
        """Check if context contains exclusion keywords."""
        context_lower = context.lower()
        
        for keyword in self.exclusion_keywords:
            if keyword in context_lower:
                # Check if it's really a date/section reference
                # Allow if it's clearly a financial context
                financial_indicators = ["fee", "charge", "payment", "amount", "rate", "interest"]
                if not any(ind in context_lower for ind in financial_indicators):
                    return True
        
        return False
    
    def _classify_currency_entity(self, context: str) -> Tuple[EntityType, float]:
        """
        Classify a currency value based on context.
        
        Returns:
            Tuple of (EntityType, confidence_score)
        """
        context_lower = context.lower()
        
        # Calculate proximity scores for each entity type
        scores = {}
        for entity_type, keywords in self.entity_keywords.items():
            if entity_type == EntityType.INTEREST_RATE:
                continue  # Interest rates are percentages, not currency
            
            score = self._calculate_keyword_proximity(context, keywords)
            scores[entity_type] = score
        
        # Get best match
        if not scores:
            return EntityType.UNKNOWN, 0.3
        
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        
        # If score is too low, mark as unknown
        if best_score < 0.3:
            return EntityType.UNKNOWN, best_score
        
        return best_type, best_score
    
    def _calculate_keyword_proximity(self, context: str, keywords: List[str]) -> float:
        """
        Calculate confidence based on keyword proximity.
        
        Returns:
            Confidence score between 0 and 1
        """
        context_lower = context.lower()
        
        # Check for exact keyword matches
        exact_matches = sum(1 for kw in keywords if kw in context_lower)
        
        if exact_matches == 0:
            return 0.0
        
        # Calculate score based on number of matches and proximity
        # More matches = higher confidence
        base_score = min(exact_matches / len(keywords), 0.8)
        
        # Boost score if keyword is very close (within 20 chars)
        for kw in keywords:
            if kw in context_lower:
                # Find position of keyword relative to center
                kw_pos = context_lower.find(kw)
                center = len(context) // 2
                distance = abs(kw_pos - center)
                
                if distance < 20:
                    base_score = min(base_score + 0.2, 1.0)
                    break
        
        return base_score
    
    def _extract_verbatim_text(self, text: str, position: int) -> str:
        """Extract the sentence containing the value."""
        # Find sentence boundaries
        start = position
        while start > 0 and text[start] not in '.!?\n':
            start -= 1
        
        end = position
        while end < len(text) and text[end] not in '.!?\n':
            end += 1
        
        # Extract and clean
        verbatim = text[start:end].strip()
        
        # Remove leading punctuation
        verbatim = verbatim.lstrip('.!?\n ')
        
        # Limit length
        if len(verbatim) > 200:
            verbatim = verbatim[:200] + "..."
        
        return verbatim
    
    def _format_currency(self, raw_value: str, matched_text: str) -> str:
        """Format currency value consistently."""
        # Detect currency symbol from matched text
        if '₹' in matched_text or 'INR' in matched_text or 'Rs' in matched_text:
            return f"₹{raw_value}"
        elif '$' in matched_text:
            return f"${raw_value}"
        else:
            return f"₹{raw_value}"  # Default to INR
    
    def calculate_derived_values(
        self,
        entities: List[FinancialEntity]
    ) -> List[FinancialEntity]:
        """
        Calculate derived values from extracted entities.
        
        For example:
        - Total cost = loan amount + interest + fees
        - Effective rate = (total cost / loan amount) * 100
        
        Args:
            entities: List of extracted entities
            
        Returns:
            List of derived entities
        """
        derived = []
        
        # Extract values by type
        loan_amount = self._get_entity_value(entities, EntityType.LOAN_AMOUNT)
        interest_rate = self._get_entity_value(entities, EntityType.INTEREST_RATE)
        duration = self._get_entity_value(entities, EntityType.REPAYMENT_DURATION)
        
        # Get all fees
        fee_types = [
            EntityType.PROCESSING_FEE,
            EntityType.INSURANCE_FEE,
            EntityType.ADMINISTRATIVE_FEE,
            EntityType.DOCUMENTATION_FEE
        ]
        
        total_fees = 0.0
        fee_sources = []
        
        for fee_type in fee_types:
            fee_value = self._get_entity_value(entities, fee_type)
            if fee_value:
                total_fees += self._parse_currency(fee_value)
                fee_sources.append(fee_type.value)
        
        # Calculate total cost if we have loan amount
        if loan_amount and total_fees > 0:
            loan_numeric = self._parse_currency(loan_amount)
            
            # Simple interest calculation if we have rate and duration
            interest_amount = 0.0
            if interest_rate and duration:
                rate = float(interest_rate.rstrip('%'))
                months = self._parse_duration(duration)
                interest_amount = (loan_numeric * rate * months) / (100 * 12)
            
            total_cost = loan_numeric + total_fees + interest_amount
            
            # Create derived entity
            derived_entity = FinancialEntity(
                type=EntityType.TOTAL_COST,
                value=f"₹{total_cost:,.2f}",
                raw_value=str(total_cost),
                source_clause="CALCULATED",
                verbatim_text=f"Calculated from loan amount, fees, and interest",
                confidence=0.8,
                position=-1,
                is_derived=True,
                calculation_source=["loan_amount"] + fee_sources
            )
            
            derived.append(derived_entity)
        
        return derived
    
    def _get_entity_value(
        self,
        entities: List[FinancialEntity],
        entity_type: EntityType
    ) -> Optional[str]:
        """Get the value of a specific entity type."""
        for entity in entities:
            if entity.type == entity_type:
                return entity.value
        return None
    
    def _parse_currency(self, value: str) -> float:
        """Parse currency string to float."""
        # Remove currency symbols and commas
        cleaned = re.sub(r'[₹$,]', '', value)
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    def _parse_duration(self, duration: str) -> int:
        """Parse duration string to months."""
        match = re.search(r'(\d+)\s+(month|year)', duration, re.IGNORECASE)
        if match:
            value = int(match.group(1))
            unit = match.group(2).lower()
            
            if 'year' in unit:
                return value * 12
            else:
                return value
        
        return 0
