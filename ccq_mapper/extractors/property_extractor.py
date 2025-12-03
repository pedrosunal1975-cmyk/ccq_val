"""
Property Extractor
==================

Extracts XBRL properties from facts WITHOUT concept matching.

CRITICAL: This module analyzes STRUCTURE, not SEMANTICS.
We extract what the fact IS, not what concept it matches.
"""

from typing import Dict, Any, Optional
from decimal import Decimal


class PropertyExtractor:
    """
    Extract intrinsic XBRL properties from facts.
    
    Properties extracted (NO concept matching):
    - unit: Currency unit (USD, EUR, shares, etc.)
    - decimals: Precision/scale indicator
    - period_type: instant vs duration
    - balance_type: debit vs credit
    - value_type: numeric, text, boolean
    - context_ref: Context identifier
    - label_text: Human-readable label
    - qname: Qualified name (for later validation only)
    """
    
    def extract_properties(self, fact: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract all XBRL properties from a fact.
        
        Args:
            fact: Raw fact dictionary
            
        Returns:
            Dictionary of extracted properties
        """
        return {
            # Monetary properties
            'unit': self._extract_unit(fact),
            'decimals': self._extract_decimals(fact),
            'value': self._extract_value(fact),
            'value_type': self._determine_value_type(fact),
            
            # Temporal properties
            'context_ref': self._extract_context_ref(fact),
            'period_type': self._extract_period_type(fact),
            
            # Accounting properties
            'balance_type': self._extract_balance_type(fact),
            
            # Context properties (CRITICAL FIX for dimensional filtering)
            'is_primary_context': fact.get('is_primary_context', True),  # Default to True
            
            # Semantic properties (for classification, not matching)
            'label': self._extract_label(fact),
            'qname': self._extract_qname(fact),
            
            # Structural properties
            'is_abstract': fact.get('abstract', False),
            'is_nil': self._is_nil(fact)
        }
    
    def _extract_unit(self, fact: Dict[str, Any]) -> Optional[str]:
        """Extract unit with fallback chain."""
        return (
            fact.get('unit') or
            fact.get('unitRef') or
            fact.get('unit_ref') or  # Map Pro format
            fact.get('uom')
        )
    
    def _extract_decimals(self, fact: Dict[str, Any]) -> Optional[int]:
        """Extract and normalize decimals attribute."""
        decimals_raw = fact.get('decimals')
        
        if decimals_raw is None:
            return None
        
        # Handle INF
        if str(decimals_raw).upper() == 'INF':
            return 0
        
        # Convert to int
        try:
            return int(decimals_raw)
        except (ValueError, TypeError):
            return None
    
    def _extract_value(self, fact: Dict[str, Any]) -> Any:
        """Extract value with fallback chain."""
        return (
            fact.get('value') or
            fact.get('fact_value') or
            fact.get('text') or
            fact.get('content')
        )
    
    def _determine_value_type(self, fact: Dict[str, Any]) -> str:
        """
        Determine the type of value.
        
        Returns: 'numeric', 'text', 'boolean', 'date', or 'unknown'
        """
        value = self._extract_value(fact)
        
        if value is None:
            return 'nil'
        
        # Check numeric
        if isinstance(value, (int, float, Decimal)):
            return 'numeric'
        
        if isinstance(value, str):
            # Try to parse as number
            try:
                float(value.replace(',', ''))
                return 'numeric'
            except (ValueError, AttributeError):
                pass
            
            # Check for boolean
            if value.lower() in ['true', 'false']:
                return 'boolean'
            
            # Check for date (simple check)
            if '-' in value and len(value) == 10:
                return 'date'
            
            return 'text'
        
        return 'unknown'
    
    def _extract_context_ref(self, fact: Dict[str, Any]) -> Optional[str]:
        """Extract context reference."""
        return (
            fact.get('contextRef') or
            fact.get('context') or
            fact.get('context_ref')
        )
    
    def _extract_period_type(self, fact: Dict[str, Any]) -> Optional[str]:
        """Extract period type."""
        # Try explicit period_type first
        explicit = fact.get('period_type') or fact.get('periodType')
        if explicit:
            return explicit
        
        # Infer from is_instant/is_duration (Map Pro format)
        if fact.get('is_instant'):
            return 'instant'
        elif fact.get('is_duration'):
            return 'duration'
    
    def _extract_balance_type(self, fact: Dict[str, Any]) -> Optional[str]:
        """
        Extract balance type (debit/credit).
        
        This is a taxonomy attribute, may not be in parsed fact.
        """
        return fact.get('balance') or fact.get('balance_type')
    
    def _extract_label(self, fact: Dict[str, Any]) -> Optional[str]:
        """Extract human-readable label."""
        return (
            fact.get('label') or 
            fact.get('concept_label') or  # Map Pro format
            fact.get('name')
        )

    def _extract_qname(self, fact: Dict[str, Any]) -> Optional[str]:
        """Extract qualified name (namespace:localname)."""
        return (
            fact.get('qname') or 
            fact.get('concept_qname') or  # Map Pro format
            fact.get('concept') or 
            fact.get('name')
        )
    
    def _is_nil(self, fact: Dict[str, Any]) -> bool:
        """Check if fact has nil value."""
        return (
            fact.get('nil') == True or
            fact.get('xsi:nil') == 'true' or
            fact.get('value') is None
        )


__all__ = ['PropertyExtractor']