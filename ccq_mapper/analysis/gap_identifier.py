# File: engines/ccq_mapper/analysis/gap_identifier.py

"""
Gap Identifier
==============

Identifies facts with classification gaps or issues.

Responsibility:
- Identify missing classifications
- Detect incomplete classifications
- Find low-confidence classifications
- Detect ambiguous classifications

Gap Types:
- missing_classification: No classification performed
- incomplete_classification: Missing required fields
- low_confidence: Classification confidence < 0.5
- ambiguous: Multiple possible classifications
"""

from typing import Dict, Any, List
from core.system_logger import get_logger

logger = get_logger(__name__)


class GapIdentifier:
    """Identifies classification gaps in facts."""
    
    # Low confidence threshold
    LOW_CONFIDENCE_THRESHOLD = 0.5
    
    # Required classification fields
    REQUIRED_FIELDS = [
        'monetary_type',
        'temporal_type',
        'accounting_type',
        'predicted_statement'
    ]
    
    # Field display names
    FIELD_NAMES = {
        'monetary_type': 'monetary classification',
        'temporal_type': 'temporal classification',
        'accounting_type': 'accounting classification',
        'predicted_statement': 'statement classification'
    }
    
    @staticmethod
    def identify_gap_facts(
        classified_facts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identify facts with classification gaps.
        
        Args:
            classified_facts: List of classified facts
            
        Returns:
            List of facts with classification issues, each containing:
            - fact: The original fact dictionary
            - gap_type: Type of gap (missing/incomplete/low_confidence/ambiguous)
            - reason: Explanation of the gap
        """
        gap_facts = []
        
        for fact in classified_facts:
            classification = fact.get('classification', {})
            
            # Check for missing classifications
            if not classification:
                gap_facts.append({
                    'fact': fact,
                    'gap_type': 'missing_classification',
                    'reason': 'No classification performed'
                })
                continue
            
            # Check for incomplete classifications
            if GapIdentifier._is_incomplete_classification(classification):
                gap_facts.append({
                    'fact': fact,
                    'gap_type': 'incomplete_classification',
                    'reason': GapIdentifier._get_incomplete_reason(classification)
                })
                continue
            
            # Check for low confidence
            confidence = classification.get('confidence_score', 1.0)
            if confidence < GapIdentifier.LOW_CONFIDENCE_THRESHOLD:
                gap_facts.append({
                    'fact': fact,
                    'gap_type': 'low_confidence',
                    'reason': f'Low confidence: {confidence:.2f}'
                })
                continue
            
            # Check for ambiguous classification
            if classification.get('is_ambiguous', False):
                gap_facts.append({
                    'fact': fact,
                    'gap_type': 'ambiguous',
                    'reason': 'Multiple possible classifications'
                })
        
        return gap_facts
    
    @staticmethod
    def _is_incomplete_classification(
        classification: Dict[str, Any]
    ) -> bool:
        """
        Check if classification is incomplete.
        
        Text facts with 'neutral' accounting_type are considered complete.
        
        Args:
            classification: Classification dictionary
            
        Returns:
            True if incomplete, False otherwise
        """
        for field in GapIdentifier.REQUIRED_FIELDS:
            value = classification.get(field)
            
            # Special case: 'neutral' is valid for accounting_type (text facts)
            if field == 'accounting_type' and value == 'neutral':
                continue
            
            # Check if missing or invalid
            if not value or value in ['unknown', 'unclassified']:
                return True
        
        return False
    
    @staticmethod
    def _get_incomplete_reason(
        classification: Dict[str, Any]
    ) -> str:
        """
        Get reason for incomplete classification.
        
        Args:
            classification: Classification dictionary
            
        Returns:
            Reason string describing missing fields
        """
        missing_fields = []
        
        for field in GapIdentifier.REQUIRED_FIELDS:
            value = classification.get(field)
            
            # Special case: 'neutral' is valid for accounting_type
            if field == 'accounting_type' and value == 'neutral':
                continue
            
            if not value or value in ['unknown', 'unclassified']:
                field_name = GapIdentifier.FIELD_NAMES.get(field, field)
                missing_fields.append(field_name)
        
        if missing_fields:
            return f"Missing: {', '.join(missing_fields)}"
        return "Incomplete classification"


__all__ = ['GapIdentifier']