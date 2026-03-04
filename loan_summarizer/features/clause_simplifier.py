"""Clause Simplifier - Simplifies legal clauses to different reading levels."""

from typing import Optional, Literal
from pydantic import BaseModel
from loan_summarizer.llm.llm_client import LLMClient
from loan_summarizer.evaluation.readability_metrics import ReadabilityMetrics, ReadabilityScore


ReadingLevel = Literal["loan_officer", "borrower", "low_literacy"]


class SimplifiedClause(BaseModel):
    """A simplified version of a legal clause."""
    original_text: str
    simplified_text: str
    reading_level: ReadingLevel
    original_score: Optional[ReadabilityScore] = None
    simplified_score: Optional[ReadabilityScore] = None
    improvement_percentage: Optional[float] = None


class ClauseSimplifier:
    """Simplifies legal clauses to different reading levels."""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize the clause simplifier.
        
        Args:
            llm_client: LLM client for text generation
        """
        self.llm_client = llm_client or LLMClient()
        self.readability = ReadabilityMetrics()
    
    async def simplify_clause(
        self,
        clause_text: str,
        reading_level: ReadingLevel = "borrower"
    ) -> SimplifiedClause:
        """
        Simplify a legal clause to the specified reading level.
        
        Args:
            clause_text: The original legal clause
            reading_level: Target reading level
            
        Returns:
            SimplifiedClause with original and simplified versions
        """
        # Build prompt based on reading level
        prompt = self._build_simplification_prompt(clause_text, reading_level)
        
        # Generate simplified version
        try:
            response = await self.llm_client.generate_structured_output(
                prompt=prompt,
                schema={"type": "object", "properties": {"simplified": {"type": "string"}}},
                temperature=0.3,
                max_tokens=500
            )
            simplified_text = response.get("simplified", clause_text)
        except Exception as e:
            # Fallback to basic simplification
            simplified_text = self._basic_simplification(clause_text, reading_level)
        
        # Calculate readability scores
        original_score = self.readability.calculate_scores(clause_text)
        simplified_score = self.readability.calculate_scores(simplified_text)
        
        # Calculate improvement
        improvement = None
        if original_score.flesch_kincaid_grade and simplified_score.flesch_kincaid_grade:
            grade_reduction = original_score.flesch_kincaid_grade - simplified_score.flesch_kincaid_grade
            improvement = (grade_reduction / original_score.flesch_kincaid_grade) * 100
        
        return SimplifiedClause(
            original_text=clause_text,
            simplified_text=simplified_text,
            reading_level=reading_level,
            original_score=original_score,
            simplified_score=simplified_score,
            improvement_percentage=round(improvement, 1) if improvement else None
        )
    
    def _build_simplification_prompt(self, clause_text: str, reading_level: ReadingLevel) -> str:
        """Build prompt for clause simplification."""
        level_instructions = {
            "loan_officer": """
Simplify this legal clause for a loan officer (professional audience):
- Maintain technical accuracy
- Use financial terminology appropriately
- Keep it concise and professional
- Target reading level: Grade 12-14
""",
            "borrower": """
Simplify this legal clause for a typical borrower:
- Use clear, everyday language
- Explain financial terms simply
- Be accurate but accessible
- Target reading level: Grade 8-10
""",
            "low_literacy": """
Simplify this legal clause for someone with low literacy:
- Use very simple words
- Write short sentences
- Avoid all jargon
- Explain everything clearly
- Target reading level: Grade 4-6
"""
        }
        
        instruction = level_instructions.get(reading_level, level_instructions["borrower"])
        
        prompt = f"""{instruction}

Original Clause:
{clause_text}

Provide ONLY the simplified version as JSON:
{{"simplified": "your simplified text here"}}

Remember: Be accurate, clear, and appropriate for the target reading level."""
        
        return prompt
    
    def _basic_simplification(self, text: str, reading_level: ReadingLevel) -> str:
        """Basic rule-based simplification as fallback."""
        simplified = text
        
        # Common legal term replacements
        replacements = {
            "shall": "must" if reading_level != "low_literacy" else "will",
            "herein": "in this document",
            "thereof": "of it",
            "pursuant to": "according to",
            "notwithstanding": "despite",
            "aforementioned": "mentioned before",
            "heretofore": "before this",
            "hereafter": "after this",
            "whereas": "because",
            "whereby": "by which",
        }
        
        for old, new in replacements.items():
            simplified = simplified.replace(old, new)
            simplified = simplified.replace(old.capitalize(), new.capitalize())
        
        # For low literacy, add extra simplification
        if reading_level == "low_literacy":
            # Break long sentences
            simplified = simplified.replace(", and ", ". ")
            simplified = simplified.replace("; ", ". ")
            
            # More replacements
            extra_replacements = {
                "remit payment": "pay",
                "exceeding": "more than",
                "constitutes": "means",
                "default": "breaking the agreement",
                "installments": "payments",
                "borrower": "you",
                "lender": "the bank",
            }
            
            for old, new in extra_replacements.items():
                simplified = simplified.replace(old, new)
                simplified = simplified.replace(old.capitalize(), new.capitalize())
        
        return simplified
    
    def format_comparison(self, simplified: SimplifiedClause) -> str:
        """Format clause comparison as readable text."""
        lines = []
        lines.append("=" * 60)
        lines.append(f"CLAUSE SIMPLIFICATION ({simplified.reading_level.replace('_', ' ').title()} Mode)")
        lines.append("=" * 60)
        
        lines.append("\nORIGINAL:")
        lines.append("-" * 60)
        lines.append(simplified.original_text)
        
        if simplified.original_score and simplified.original_score.flesch_kincaid_grade:
            lines.append(f"\nReadability: Grade {simplified.original_score.flesch_kincaid_grade}")
            lines.append(f"Level: {simplified.original_score.reading_level}")
        
        lines.append("\n" + "=" * 60)
        lines.append("SIMPLIFIED:")
        lines.append("-" * 60)
        lines.append(simplified.simplified_text)
        
        if simplified.simplified_score and simplified.simplified_score.flesch_kincaid_grade:
            lines.append(f"\nReadability: Grade {simplified.simplified_score.flesch_kincaid_grade}")
            lines.append(f"Level: {simplified.simplified_score.reading_level}")
        
        if simplified.improvement_percentage:
            lines.append("\n" + "=" * 60)
            lines.append(f"IMPROVEMENT: {simplified.improvement_percentage}% easier to read")
            lines.append("=" * 60)
        
        return "\n".join(lines)
