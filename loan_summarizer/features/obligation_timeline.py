"""Obligation Timeline Generator - Creates payment schedules and timelines."""

from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
import re


class TimelineEvent(BaseModel):
    """A single event in the loan timeline."""
    date: str
    event_type: str  # payment, fee, milestone
    amount: Optional[str] = None
    description: str


class LoanTimeline(BaseModel):
    """Complete timeline of loan obligations."""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    events: List[TimelineEvent] = []
    total_payments: int = 0
    payment_frequency: Optional[str] = None


class ObligationTimeline:
    """Generates payment timelines from loan agreements."""
    
    def __init__(self):
        """Initialize the timeline generator."""
        pass
    
    def generate_timeline(self, contract_text: str) -> LoanTimeline:
        """
        Generate a complete timeline of loan obligations.
        
        Args:
            contract_text: The loan agreement text
            
        Returns:
            LoanTimeline with all events
        """
        # Extract key information
        start_date = self._extract_start_date(contract_text)
        payment_amount = self._extract_payment_amount(contract_text)
        num_payments = self._extract_number_of_payments(contract_text)
        frequency = self._extract_payment_frequency(contract_text)
        
        # Generate payment events
        events = []
        
        if start_date and payment_amount and num_payments and frequency:
            events = self._generate_payment_events(
                start_date, payment_amount, num_payments, frequency
            )
        
        # Add other obligations (fees, insurance, etc.)
        additional_events = self._extract_additional_obligations(contract_text)
        events.extend(additional_events)
        
        # Sort events by date
        events.sort(key=lambda e: e.date)
        
        # Determine end date
        end_date = events[-1].date if events else None
        
        return LoanTimeline(
            start_date=start_date,
            end_date=end_date,
            events=events,
            total_payments=num_payments or 0,
            payment_frequency=frequency
        )
    
    def _extract_start_date(self, text: str) -> Optional[str]:
        """Extract loan start date."""
        patterns = [
            r'(?:commencing|starting|beginning)\s+on\s+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
            r'(?:dated|date:?)\s+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
            r'as of\s+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                try:
                    # Parse and format date
                    date_obj = datetime.strptime(date_str, "%B %d, %Y")
                    return date_obj.strftime("%Y-%m-%d")
                except:
                    try:
                        date_obj = datetime.strptime(date_str, "%B %d %Y")
                        return date_obj.strftime("%Y-%m-%d")
                    except:
                        continue
        
        # Default to today if not found
        return datetime.now().strftime("%Y-%m-%d")
    
    def _extract_payment_amount(self, text: str) -> Optional[str]:
        """Extract monthly payment amount."""
        patterns = [
            r'(?:monthly\s+)?(?:payment|installment)s?\s+of\s+\$?([\d,]+(?:\.\d{2})?)',
            r'\$?([\d,]+(?:\.\d{2})?)\s+(?:per month|monthly)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"${match.group(1)}"
        
        return None
    
    def _extract_number_of_payments(self, text: str) -> Optional[int]:
        """Extract total number of payments."""
        patterns = [
            r'(\d+)\s+(?:equal\s+)?(?:monthly\s+)?(?:payment|installment)s',
            r'(?:over|for)\s+(\d+)\s+months',
            r'(\d+)[-\s]month\s+term',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return None
    
    def _extract_payment_frequency(self, text: str) -> Optional[str]:
        """Extract payment frequency."""
        if re.search(r'\bmonthly\b', text, re.IGNORECASE):
            return "monthly"
        elif re.search(r'\bweekly\b', text, re.IGNORECASE):
            return "weekly"
        elif re.search(r'\bquarterly\b', text, re.IGNORECASE):
            return "quarterly"
        elif re.search(r'\bannual(?:ly)?\b', text, re.IGNORECASE):
            return "annually"
        
        return "monthly"  # Default
    
    def _generate_payment_events(
        self,
        start_date: str,
        payment_amount: str,
        num_payments: int,
        frequency: str
    ) -> List[TimelineEvent]:
        """Generate payment events based on schedule."""
        events = []
        
        try:
            current_date = datetime.strptime(start_date, "%Y-%m-%d")
        except:
            current_date = datetime.now()
        
        # Determine interval
        if frequency == "monthly":
            interval_days = 30
        elif frequency == "weekly":
            interval_days = 7
        elif frequency == "quarterly":
            interval_days = 90
        elif frequency == "annually":
            interval_days = 365
        else:
            interval_days = 30
        
        for i in range(1, num_payments + 1):
            # Calculate payment date
            payment_date = current_date + timedelta(days=interval_days * i)
            
            # Create event
            event = TimelineEvent(
                date=payment_date.strftime("%Y-%m-%d"),
                event_type="payment",
                amount=payment_amount,
                description=f"Payment #{i} of {num_payments}"
            )
            events.append(event)
        
        return events
    
    def _extract_additional_obligations(self, text: str) -> List[TimelineEvent]:
        """Extract additional obligations like insurance, fees, etc."""
        events = []
        
        # Look for insurance premiums
        insurance_pattern = r'insurance\s+premium.*?\$?([\d,]+(?:\.\d{2})?)'
        matches = re.finditer(insurance_pattern, text, re.IGNORECASE)
        
        for match in matches:
            amount = f"${match.group(1)}"
            # Try to find when it's due
            context = text[max(0, match.start()-100):min(len(text), match.end()+100)]
            
            # Look for timing keywords
            if "annual" in context.lower():
                event = TimelineEvent(
                    date="",  # Would need more context
                    event_type="fee",
                    amount=amount,
                    description="Annual insurance premium"
                )
                events.append(event)
        
        return events
    
    def format_timeline(self, timeline: LoanTimeline) -> str:
        """Format timeline as readable text."""
        lines = []
        lines.append("=" * 60)
        lines.append("LOAN OBLIGATION TIMELINE")
        lines.append("=" * 60)
        
        if timeline.start_date:
            lines.append(f"\nStart Date: {timeline.start_date}")
        if timeline.end_date:
            lines.append(f"End Date: {timeline.end_date}")
        if timeline.payment_frequency:
            lines.append(f"Payment Frequency: {timeline.payment_frequency.title()}")
        if timeline.total_payments:
            lines.append(f"Total Payments: {timeline.total_payments}")
        
        if timeline.events:
            lines.append("\n" + "-" * 60)
            lines.append("SCHEDULE:")
            lines.append("-" * 60)
            
            for event in timeline.events[:12]:  # Show first 12 events
                date_formatted = datetime.strptime(event.date, "%Y-%m-%d").strftime("%b %d, %Y")
                amount_str = f" - {event.amount}" if event.amount else ""
                lines.append(f"{date_formatted}: {event.description}{amount_str}")
            
            if len(timeline.events) > 12:
                lines.append(f"... and {len(timeline.events) - 12} more payments")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def export_to_ics(self, timeline: LoanTimeline) -> str:
        """
        Export timeline to iCalendar format.
        
        Args:
            timeline: The loan timeline
            
        Returns:
            iCalendar formatted string
        """
        lines = []
        lines.append("BEGIN:VCALENDAR")
        lines.append("VERSION:2.0")
        lines.append("PRODID:-//Loan Summarizer//EN")
        lines.append("CALSCALE:GREGORIAN")
        lines.append("METHOD:PUBLISH")
        lines.append("X-WR-CALNAME:Loan Payment Schedule")
        lines.append("X-WR-TIMEZONE:UTC")
        
        for event in timeline.events:
            lines.append("BEGIN:VEVENT")
            
            # Format date for iCal (YYYYMMDD)
            date_obj = datetime.strptime(event.date, "%Y-%m-%d")
            date_ical = date_obj.strftime("%Y%m%d")
            
            lines.append(f"DTSTART;VALUE=DATE:{date_ical}")
            lines.append(f"DTEND;VALUE=DATE:{date_ical}")
            lines.append(f"SUMMARY:{event.description}")
            
            if event.amount:
                lines.append(f"DESCRIPTION:Amount due: {event.amount}")
            
            # Generate unique ID
            uid = f"{date_ical}-{event.event_type}@loansummarizer.com"
            lines.append(f"UID:{uid}")
            
            lines.append("STATUS:CONFIRMED")
            lines.append("SEQUENCE:0")
            lines.append("END:VEVENT")
        
        lines.append("END:VCALENDAR")
        
        return "\n".join(lines)
