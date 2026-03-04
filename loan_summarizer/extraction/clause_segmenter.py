"""
Clause Segmenter - Splits loan agreements into logical clauses for analysis.

This module segments contracts into clauses to enable clause-level processing,
which improves extraction accuracy by providing focused context.
"""

import re
from typing import List, Optional
from pydantic import BaseModel, Field


class Clause(BaseModel):
    """Represents a single clause in a loan agreement."""
    
    clause_id: str = Field(..., description="Unique identifier for the clause")
    text: str = Field(..., description="Full text of the clause")
    clause_type: str = Field(default="general", description="Type of clause")
    position: int = Field(..., description="Character position in document")
    length: int = Field(..., description="Length of clause in characters")


class ClauseSegmenter:
    """
    Segments loan agreements into logical clauses.
    
    Supports multiple segmentation strategies:
    1. Section-based (SECTION 1, SECTION 2, etc.)
    2. Numbered headings (1., 2., 3., etc.)
    3. Paragraph-based (double newlines)
    4. Hybrid approach
    """
    
    def __init__(self):
        """Initialize the clause segmenter."""
        
        # Patterns for section headers
        self.section_patterns = [
            r'SECTION\s+(\d+)[:\.]?\s*([^\n]*)',  # SECTION 1: Title
            r'Article\s+(\d+)[:\.]?\s*([^\n]*)',  # Article 1: Title
            r'Clause\s+(\d+)[:\.]?\s*([^\n]*)',   # Clause 1: Title
            r'(\d+)\.\s+([A-Z][^\n]{5,50})',      # 1. TITLE
        ]
        
        # Clause type keywords
        self.clause_type_keywords = {
            "loan_amount": ["loan amount", "principal", "advance", "disbursement"],
            "interest": ["interest", "rate", "APR", "per annum"],
            "repayment": ["repayment", "payment", "installment", "EMI"],
            "fees": ["fee", "charge", "cost", "expense"],
            "default": ["default", "breach", "violation", "non-payment"],
            "security": ["security", "collateral", "pledge", "mortgage"],
            "termination": ["termination", "cancellation", "closure"],
            "miscellaneous": ["miscellaneous", "general", "other"]
        }
    
    def segment(self, contract_text: str) -> List[Clause]:
        """
        Segment contract into clauses.
        
        Args:
            contract_text: The full loan agreement text
            
        Returns:
            List of Clause objects
        """
        # Try section-based segmentation first
        clauses = self._segment_by_sections(contract_text)
        
        # If no sections found, try paragraph-based
        if len(clauses) <= 1:
            clauses = self._segment_by_paragraphs(contract_text)
        
        # Classify clause types
        for clause in clauses:
            clause.clause_type = self._classify_clause(clause.text)
        
        return clauses
    
    def _segment_by_sections(self, text: str) -> List[Clause]:
        """Segment by section headers."""
        clauses = []
        
        # Find all section headers
        section_matches = []
        for pattern in self.section_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                section_num = match.group(1)
                section_title = match.group(2).strip() if len(match.groups()) > 1 else ""
                section_matches.append({
                    "number": section_num,
                    "title": section_title,
                    "position": match.start(),
                    "header_end": match.end()
                })
        
        # Sort by position
        section_matches.sort(key=lambda x: x["position"])
        
        # Extract text between sections
        for i, section in enumerate(section_matches):
            # Determine end position (start of next section or end of document)
            if i < len(section_matches) - 1:
                end_pos = section_matches[i + 1]["position"]
            else:
                end_pos = len(text)
            
            # Extract clause text
            clause_text = text[section["header_end"]:end_pos].strip()
            
            # Create clause ID
            clause_id = f"Section {section['number']}"
            if section["title"]:
                clause_id += f": {section['title']}"
            
            clause = Clause(
                clause_id=clause_id,
                text=clause_text,
                position=section["position"],
                length=len(clause_text)
            )
            
            clauses.append(clause)
        
        # If no sections found, return entire document as one clause
        if not clauses:
            clauses.append(Clause(
                clause_id="Full Document",
                text=text,
                position=0,
                length=len(text)
            ))
        
        return clauses
    
    def _segment_by_paragraphs(self, text: str) -> List[Clause]:
        """Segment by paragraphs (double newlines)."""
        clauses = []
        
        # Split by double newlines
        paragraphs = re.split(r'\n\s*\n', text)
        
        position = 0
        for i, para in enumerate(paragraphs):
            para = para.strip()
            
            if not para or len(para) < 50:  # Skip very short paragraphs
                position += len(para) + 2  # Account for newlines
                continue
            
            clause = Clause(
                clause_id=f"Paragraph {i + 1}",
                text=para,
                position=position,
                length=len(para)
            )
            
            clauses.append(clause)
            position += len(para) + 2
        
        return clauses
    
    def _classify_clause(self, clause_text: str) -> str:
        """Classify clause type based on content."""
        text_lower = clause_text.lower()
        
        # Check each clause type
        scores = {}
        for clause_type, keywords in self.clause_type_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[clause_type] = score
        
        # Return type with highest score
        if scores:
            return max(scores, key=scores.get)
        
        return "general"
    
    def get_clause_by_type(
        self,
        clauses: List[Clause],
        clause_type: str
    ) -> List[Clause]:
        """Get all clauses of a specific type."""
        return [c for c in clauses if c.clause_type == clause_type]
    
    def get_clause_by_id(
        self,
        clauses: List[Clause],
        clause_id: str
    ) -> Optional[Clause]:
        """Get a specific clause by ID."""
        for clause in clauses:
            if clause.clause_id == clause_id:
                return clause
        return None
    
    def merge_clauses(
        self,
        clauses: List[Clause],
        clause_ids: List[str]
    ) -> Optional[Clause]:
        """Merge multiple clauses into one."""
        selected_clauses = [c for c in clauses if c.clause_id in clause_ids]
        
        if not selected_clauses:
            return None
        
        # Sort by position
        selected_clauses.sort(key=lambda c: c.position)
        
        # Merge text
        merged_text = "\n\n".join(c.text for c in selected_clauses)
        
        # Create merged clause
        merged = Clause(
            clause_id=f"Merged: {', '.join(clause_ids)}",
            text=merged_text,
            clause_type="merged",
            position=selected_clauses[0].position,
            length=len(merged_text)
        )
        
        return merged
    
    def format_clauses(self, clauses: List[Clause]) -> str:
        """Format clauses for display."""
        lines = []
        lines.append("=" * 70)
        lines.append("CONTRACT CLAUSE SEGMENTATION")
        lines.append("=" * 70)
        lines.append(f"\nTotal Clauses: {len(clauses)}\n")
        
        for clause in clauses:
            lines.append("-" * 70)
            lines.append(f"ID: {clause.clause_id}")
            lines.append(f"Type: {clause.clause_type}")
            lines.append(f"Length: {clause.length} characters")
            lines.append(f"\nText Preview:")
            
            # Show first 200 characters
            preview = clause.text[:200]
            if len(clause.text) > 200:
                preview += "..."
            
            lines.append(preview)
            lines.append("")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)
