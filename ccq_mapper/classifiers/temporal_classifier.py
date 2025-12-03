"""
Temporal Classifier
===================

Classifies facts by their temporal properties.

CRITICAL: Classifies by PERIOD TYPE, not concept semantics.
"""

from typing import Dict, Any, Optional


class TemporalClassifier:
    """
    Classify facts by temporal properties.
    
    Categories:
    - INSTANT: Point-in-time values (balance sheet items)
    - DURATION: Period values (income statement, cash flow)
    - UNKNOWN: Cannot determine
    
    Also provides period analysis:
    - Quarter, annual, YTD detection
    - Period length calculation
    """
    
    def classify(self, properties: Dict[str, Any]) -> str:
        """
        Classify fact by temporal properties.
        
        Args:
            properties: Extracted properties dictionary
            
        Returns:
            Classification: 'instant', 'duration', 'unknown'
        """
        period_type = (properties.get('period_type') or '').lower()
        
        # Direct period type
        if period_type == 'instant':
            return 'instant'
        elif period_type == 'duration':
            return 'duration'
        
        # Try to infer from context_info if available
        context_info = properties.get('context_info', {})
        if context_info:
            period_info = context_info.get('period', {})
            inferred_type = (period_info.get('type') or '').lower()
            
            if inferred_type in ['instant', 'duration']:
                return inferred_type
        
        return 'unknown'
    
    def get_period_length(self, properties: Dict[str, Any]) -> Optional[int]:
        """
        Get period length in days for duration facts.
        
        Returns:
            Number of days, or None if not applicable
        """
        temporal_type = self.classify(properties)
        
        if temporal_type != 'duration':
            return None
        
        context_info = properties.get('context_info', {})
        if not context_info:
            return None
        
        period_info = context_info.get('period', {})
        return period_info.get('duration_days')
    
    def detect_period_category(self, properties: Dict[str, Any]) -> str:
        """
        Detect period category (quarterly, annual, YTD, etc.).
        
        Returns:
            'quarterly', 'annual', 'ytd', 'monthly', 'other', 'instant'
        """
        temporal_type = self.classify(properties)
        
        if temporal_type == 'instant':
            return 'instant'
        
        period_days = self.get_period_length(properties)
        
        if not period_days:
            return 'unknown'
        
        # Quarterly: ~90 days (85-95 range)
        if 85 <= period_days <= 95:
            return 'quarterly'
        
        # Annual: ~365 days (360-370 range)
        if 360 <= period_days <= 370:
            return 'annual'
        
        # Monthly: ~30 days (28-32 range)
        if 28 <= period_days <= 32:
            return 'monthly'
        
        # YTD: Varies, but look for patterns
        # YTD typically 90-270 days depending on quarter
        if 90 < period_days < 360:
            return 'ytd_or_other'
        
        return 'other'
    
    def is_balance_sheet_period(self, properties: Dict[str, Any]) -> bool:
        """
        Check if this is a balance sheet period type.
        
        Balance sheet = instant
        """
        return self.classify(properties) == 'instant'
    
    def is_flow_statement_period(self, properties: Dict[str, Any]) -> bool:
        """
        Check if this is a flow statement period type.
        
        Flow statements (income, cash flow) = duration
        """
        return self.classify(properties) == 'duration'
    
    def get_period_dates(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract period dates.
        
        Returns:
            Dictionary with 'instant', 'start', 'end' dates
        """
        context_info = properties.get('context_info', {})
        if not context_info:
            return {
                'instant': None,
                'start': None,
                'end': None
            }
        
        period_info = context_info.get('period', {})
        return {
            'instant': period_info.get('instant'),
            'start': period_info.get('start'),
            'end': period_info.get('end')
        }
    
    def compare_periods(
        self,
        props1: Dict[str, Any],
        props2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare two facts' periods.
        
        Used for clustering and relationship detection.
        """
        type1 = self.classify(props1)
        type2 = self.classify(props2)
        
        dates1 = self.get_period_dates(props1)
        dates2 = self.get_period_dates(props2)
        
        return {
            'same_type': type1 == type2,
            'same_period': (
                dates1.get('instant') == dates2.get('instant') or
                (dates1.get('start') == dates2.get('start') and
                 dates1.get('end') == dates2.get('end'))
            ),
            'overlapping': self._check_overlap(dates1, dates2)
        }
    
    def _check_overlap(self, dates1: Dict[str, Any], dates2: Dict[str, Any]) -> bool:
        """Check if two periods overlap."""
        # Instant dates
        if dates1.get('instant') and dates2.get('instant'):
            return dates1['instant'] == dates2['instant']
        
        # Duration overlap
        start1 = dates1.get('start')
        end1 = dates1.get('end')
        start2 = dates2.get('start')
        end2 = dates2.get('end')
        
        if not all([start1, end1, start2, end2]):
            return False
        
        # Check overlap: periods overlap if start1 <= end2 and start2 <= end1
        return start1 <= end2 and start2 <= end1


__all__ = ['TemporalClassifier']