"""Text utility functions for preprocessing and validation."""

import re
from typing import Optional


def preprocess_text(text: str) -> str:
    """
    Preprocess text by normalizing whitespace and line breaks.
    
    Args:
        text: Raw text to preprocess.
        
    Returns:
        Preprocessed text with normalized whitespace.
    """
    if not text:
        return ""
    
    # Normalize line breaks (convert \r\n and \r to \n)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove excessive blank lines (more than 2 consecutive newlines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Trim leading and trailing whitespace
    text = text.strip()
    
    return text


def validate_text_length(text: str, min_length: int = 10, max_length: int = 100000) -> tuple[bool, Optional[str]]:
    """
    Validate that text meets length requirements.
    
    Args:
        text: Text to validate.
        min_length: Minimum acceptable length in characters.
        max_length: Maximum acceptable length in characters.
        
    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.
    """
    if not text or len(text.strip()) == 0:
        return False, "Text cannot be empty"
    
    text_length = len(text.strip())
    
    if text_length < min_length:
        return False, f"Text is too short. Minimum length is {min_length} characters, got {text_length}"
    
    if text_length > max_length:
        return False, f"Text is too long. Maximum length is {max_length} characters, got {text_length}"
    
    return True, None


def is_whitespace_only(text: str) -> bool:
    """
    Check if text contains only whitespace characters.
    
    Args:
        text: Text to check.
        
    Returns:
        True if text is empty or contains only whitespace, False otherwise.
    """
    return not text or len(text.strip()) == 0


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length, adding suffix if truncated.
    
    Args:
        text: Text to truncate.
        max_length: Maximum length including suffix.
        suffix: Suffix to add if text is truncated.
        
    Returns:
        Truncated text.
    """
    if len(text) <= max_length:
        return text
    
    # Account for suffix length
    truncate_at = max_length - len(suffix)
    if truncate_at < 0:
        truncate_at = 0
    
    return text[:truncate_at] + suffix


def count_words(text: str) -> int:
    """
    Count the number of words in text.
    
    Args:
        text: Text to count words in.
        
    Returns:
        Number of words.
    """
    if not text:
        return 0
    
    # Split on whitespace and filter out empty strings
    words = [word for word in text.split() if word]
    return len(words)


def format_currency(amount: float, currency_symbol: str = "$") -> str:
    """
    Format a number as currency with thousands separators.
    
    Args:
        amount: Amount to format.
        currency_symbol: Currency symbol to use.
        
    Returns:
        Formatted currency string.
    """
    return f"{currency_symbol}{amount:,.2f}"


def extract_numbers(text: str) -> list[float]:
    """
    Extract all numerical values from text.
    
    Args:
        text: Text to extract numbers from.
        
    Returns:
        List of extracted numbers.
    """
    # Pattern matches integers and decimals, with optional commas
    pattern = r'\d+(?:,\d{3})*(?:\.\d+)?'
    matches = re.findall(pattern, text)
    
    numbers = []
    for match in matches:
        try:
            # Remove commas and convert to float
            clean_number = match.replace(',', '')
            numbers.append(float(clean_number))
        except ValueError:
            continue
    
    return numbers


def clean_whitespace(text: str) -> str:
    """
    Clean excessive whitespace from text while preserving structure.
    
    Args:
        text: Text to clean.
        
    Returns:
        Text with cleaned whitespace.
    """
    if not text:
        return ""
    
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    
    # Replace tabs with spaces
    text = text.replace('\t', ' ')
    
    # Trim whitespace from each line
    lines = [line.strip() for line in text.split('\n')]
    
    # Join lines back together
    return '\n'.join(lines)
