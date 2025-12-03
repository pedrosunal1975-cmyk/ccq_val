"""
Monetary Classifier
===================

Classifies facts by their monetary/unit properties.

CRITICAL: Classifies by UNIT type, not concept semantics.
"""

from typing import Dict, Any, Optional


class MonetaryClassifier:
    """
    Classify facts by their monetary/unit properties.
    
    Categories:
    - CURRENCY: Monetary values (USD, EUR, etc.)
    - SHARES: Share-based values
    - PURE: Pure numbers (ratios, percentages)
    - TEXT: Non-numeric
    - OTHER: Unknown or mixed
    """
    
    # Known currency indicators
    CURRENCY_INDICATORS = [
        'usd', 'eur', 'gbp', 'jpy', 'cny', 'cad', 'aud',
        'currency', 'iso4217', 'monetary'
    ]
    
    # Known share indicators
    SHARE_INDICATORS = [
        'shares', 'share', 'stock', 'equity'
    ]
    
    # Pure number indicators
    PURE_INDICATORS = [
        'pure', 'number', 'xbrli:pure', 'ratio'
    ]
    
    def classify(self, properties: Dict[str, Any]) -> str:
        """
        Classify fact by monetary/unit properties.
        
        Args:
            properties: Extracted properties dictionary
            
        Returns:
            Classification: 'currency', 'shares', 'pure', 'text', 'other'
        """
        value_type = (properties.get('value_type') or '').lower()
        unit = (properties.get('unit') or '').lower()
        
        # Text values
        if value_type in ['text', 'boolean', 'date']:
            return 'text'
        
        # Nil values
        if value_type == 'nil' or properties.get('is_nil'):
            return 'nil'
        
        # Numeric values - classify by unit
        if value_type == 'numeric':
            return self._classify_by_unit(unit)
        
        return 'other'
    
    def _classify_by_unit(self, unit: str) -> str:
        """
        Classify by unit string.
        
        Strategy:
        1. Check currency indicators
        2. Check share indicators
        3. Check pure number indicators
        4. Default to other
        """
        if not unit:
            return 'unknown_numeric'
        
        unit_lower = unit.lower()
        
        # Currency check
        if any(indicator in unit_lower for indicator in self.CURRENCY_INDICATORS):
            return 'currency'
        
        # Share check
        if any(indicator in unit_lower for indicator in self.SHARE_INDICATORS):
            return 'shares'
        
        # Pure number check
        if any(indicator in unit_lower for indicator in self.PURE_INDICATORS):
            return 'pure'
        
        # Default
        return 'other_numeric'
    
    def get_scale_factor(self, properties: Dict[str, Any]) -> Optional[int]:
        """
        Determine scale factor from decimals attribute.
        
        Returns:
            Scale factor (e.g., -3 means thousands, -6 means millions)
        """
        decimals = properties.get('decimals')
        
        if decimals is None:
            return None
        
        if isinstance(decimals, int):
            return decimals
        
        # Handle string decimals
        try:
            return int(decimals)
        except (ValueError, TypeError):
            return None
    
    def is_monetary(self, properties: Dict[str, Any]) -> bool:
        """Quick check if fact is monetary."""
        classification = self.classify(properties)
        return classification == 'currency'
    
    def is_share_based(self, properties: Dict[str, Any]) -> bool:
        """Quick check if fact is share-based."""
        classification = self.classify(properties)
        return classification == 'shares'


__all__ = ['MonetaryClassifier']