"""Readability metrics for measuring text complexity."""

try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False

from typing import Dict, Optional
from pydantic import BaseModel


class ReadabilityScore(BaseModel):
    """Readability scores for a text."""
    flesch_reading_ease: Optional[float] = None
    flesch_kincaid_grade: Optional[float] = None
    gunning_fog: Optional[float] = None
    smog_index: Optional[float] = None
    automated_readability_index: Optional[float] = None
    coleman_liau_index: Optional[float] = None
    reading_level: str = "Unknown"
    interpretation: str = ""


class ReadabilityMetrics:
    """Calculate readability metrics for text."""
    
    def __init__(self):
        """Initialize readability metrics calculator."""
        self.available = TEXTSTAT_AVAILABLE
    
    def calculate_scores(self, text: str) -> ReadabilityScore:
        """
        Calculate comprehensive readability scores for text.
        
        Args:
            text: The text to analyze
            
        Returns:
            ReadabilityScore with all metrics
        """
        if not self.available or not text or len(text.strip()) == 0:
            return ReadabilityScore(
                reading_level="Unknown",
                interpretation="Unable to calculate readability scores"
            )
        
        try:
            # Calculate various readability metrics
            flesch_ease = textstat.flesch_reading_ease(text)
            flesch_grade = textstat.flesch_kincaid_grade(text)
            gunning = textstat.gunning_fog(text)
            smog = textstat.smog_index(text)
            ari = textstat.automated_readability_index(text)
            coleman = textstat.coleman_liau_index(text)
            
            # Determine reading level
            reading_level = self._determine_reading_level(flesch_grade)
            interpretation = self._interpret_flesch_ease(flesch_ease)
            
            return ReadabilityScore(
                flesch_reading_ease=round(flesch_ease, 1),
                flesch_kincaid_grade=round(flesch_grade, 1),
                gunning_fog=round(gunning, 1),
                smog_index=round(smog, 1),
                automated_readability_index=round(ari, 1),
                coleman_liau_index=round(coleman, 1),
                reading_level=reading_level,
                interpretation=interpretation
            )
        except Exception as e:
            return ReadabilityScore(
                reading_level="Error",
                interpretation=f"Error calculating scores: {str(e)}"
            )
    
    def _determine_reading_level(self, grade: float) -> str:
        """Determine reading level from grade level."""
        if grade < 6:
            return "Elementary (Grade 1-5)"
        elif grade < 9:
            return "Middle School (Grade 6-8)"
        elif grade < 13:
            return "High School (Grade 9-12)"
        elif grade < 16:
            return "College (Grade 13-16)"
        else:
            return "Graduate Level (16+)"
    
    def _interpret_flesch_ease(self, score: float) -> str:
        """Interpret Flesch Reading Ease score."""
        if score >= 90:
            return "Very Easy - 5th grade level"
        elif score >= 80:
            return "Easy - 6th grade level"
        elif score >= 70:
            return "Fairly Easy - 7th grade level"
        elif score >= 60:
            return "Standard - 8th-9th grade level"
        elif score >= 50:
            return "Fairly Difficult - 10th-12th grade level"
        elif score >= 30:
            return "Difficult - College level"
        else:
            return "Very Difficult - Graduate level"
    
    def compare_texts(self, original: str, simplified: str) -> Dict[str, any]:
        """
        Compare readability of original vs simplified text.
        
        Args:
            original: Original text
            simplified: Simplified text
            
        Returns:
            Dictionary with comparison metrics
        """
        original_scores = self.calculate_scores(original)
        simplified_scores = self.calculate_scores(simplified)
        
        # Calculate improvement
        improvement = None
        if original_scores.flesch_kincaid_grade and simplified_scores.flesch_kincaid_grade:
            grade_reduction = original_scores.flesch_kincaid_grade - simplified_scores.flesch_kincaid_grade
            improvement_pct = (grade_reduction / original_scores.flesch_kincaid_grade) * 100
            improvement = {
                "grade_reduction": round(grade_reduction, 1),
                "improvement_percentage": round(improvement_pct, 1)
            }
        
        return {
            "original": original_scores,
            "simplified": simplified_scores,
            "improvement": improvement
        }
    
    def format_scores(self, scores: ReadabilityScore) -> str:
        """Format readability scores as readable text."""
        if not scores.flesch_reading_ease:
            return scores.interpretation
        
        lines = []
        lines.append("Readability Scores:")
        lines.append("-" * 40)
        lines.append(f"Flesch Reading Ease: {scores.flesch_reading_ease}")
        lines.append(f"  → {scores.interpretation}")
        lines.append(f"\nFlesch-Kincaid Grade: {scores.flesch_kincaid_grade}")
        lines.append(f"  → {scores.reading_level}")
        lines.append(f"\nGunning Fog Index: {scores.gunning_fog}")
        lines.append(f"SMOG Index: {scores.smog_index}")
        lines.append(f"Automated Readability Index: {scores.automated_readability_index}")
        lines.append(f"Coleman-Liau Index: {scores.coleman_liau_index}")
        
        return "\n".join(lines)
