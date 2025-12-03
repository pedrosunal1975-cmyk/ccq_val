"""
Accounting Classifier
=====================

Classifies facts by their accounting properties (debit/credit nature).

CRITICAL: Classifies by BALANCE TYPE, not concept semantics.
"""

from typing import Dict, Any, Optional


class AccountingClassifier:
    """
    Classify facts by accounting/balance properties.
    
    Categories:
    - DEBIT: Natural debit balance (assets, expenses)
    - CREDIT: Natural credit balance (liabilities, equity, revenue)
    - NEUTRAL: No inherent balance type
    - UNKNOWN: Cannot determine
    
    Note: This uses the XBRL balance attribute when available,
    NOT semantic analysis of the concept name.
    """
    
    # Keywords that might indicate balance type (fallback only)
    DEBIT_KEYWORDS = [
        'asset', 'expense', 'cost', 'loss', 'debit',
        'receivable', 'inventory', 'property', 'equipment'
    ]
    
    CREDIT_KEYWORDS = [
        'liability', 'equity', 'revenue', 'income', 'gain', 'credit',
        'payable', 'debt', 'capital', 'retained', 'sales'
    ]
    
    def classify(self, properties: Dict[str, Any]) -> str:
        """
        Classify fact by accounting balance properties.
        
        Args:
            properties: Extracted properties dictionary
            
        Returns:
            Classification: 'debit', 'credit', 'neutral', 'unknown'
        """
        # Strategy 1: Use explicit balance_type (PRIMARY)
        balance_type = self._extract_balance_type(properties)
        if balance_type:
            return balance_type
        
        # Strategy 2: Infer from value sign and label (SECONDARY)
        inferred_type = self._infer_from_properties(properties)
        if inferred_type != 'unknown':
            return inferred_type
        
        # Strategy 3: Keyword fallback (TERTIARY)
        keyword_type = self._classify_by_keywords(properties)
        if keyword_type != 'unknown':
            return keyword_type
        
        return 'unknown'
    
    def _extract_balance_type(self, properties: Dict[str, Any]) -> Optional[str]:
        """
        Extract explicit balance type from properties.
        
        This is the XBRL balance attribute from taxonomy.
        """
        balance = (properties.get('balance_type') or '').lower()
        
        if balance == 'debit':
            return 'debit'
        elif balance == 'credit':
            return 'credit'
        
        return None
    
    def _infer_from_properties(self, properties: Dict[str, Any]) -> str:
        """
        Infer balance type from combined properties.
        
        Uses:
        - Value sign (negative values might indicate different treatment)
        - Period type (instant vs duration)
        - Monetary type
        
        CRITICAL: Numeric facts without balance_type are NEUTRAL, not UNKNOWN.
        Not all numeric facts have debit/credit nature (e.g., EPS, ratios, counts).
        """
        value_type = properties.get('value_type')
        period_type = (properties.get('period_type') or '').lower()
        
        # Non-numeric facts are neutral
        if value_type in ['text', 'boolean', 'date', 'nil']:
            return 'neutral'
        
        # Numeric facts without explicit balance_type are also neutral
        # Examples: EPS, ratios, percentages, counts, tax rates
        # These don't have debit/credit nature even though they're numeric
        if period_type in ['instant', 'duration']:
            return 'neutral'
        
        return 'neutral'
    
    def _classify_by_keywords(self, properties: Dict[str, Any]) -> str:
        """
        Classify by keyword matching (fallback only).
        
        This is the LAST resort and least reliable.
        """
        label = (properties.get('label') or '').lower()
        qname = (properties.get('qname') or '').lower()
        combined = f"{label} {qname}"
        
        # Count keyword matches
        debit_score = sum(1 for kw in self.DEBIT_KEYWORDS if kw in combined)
        credit_score = sum(1 for kw in self.CREDIT_KEYWORDS if kw in combined)
        
        # Return highest scoring type
        if debit_score > credit_score and debit_score > 0:
            return 'debit'
        elif credit_score > debit_score and credit_score > 0:
            return 'credit'
        
        return 'unknown'
    
    def is_debit_nature(self, properties: Dict[str, Any]) -> bool:
        """Quick check if fact has debit nature."""
        return self.classify(properties) == 'debit'
    
    def is_credit_nature(self, properties: Dict[str, Any]) -> bool:
        """Quick check if fact has credit nature."""
        return self.classify(properties) == 'credit'
    
    def get_expected_sign(self, properties: Dict[str, Any]) -> Optional[str]:
        """
        Get expected sign for the value based on balance type.
        
        Returns:
            'positive', 'negative', or None if unknown
            
        Note: In XBRL, debits are typically positive, credits negative
        (or vice versa depending on statement presentation)
        """
        balance = self.classify(properties)
        
        if balance == 'debit':
            # Debit items typically positive (assets, expenses)
            return 'positive'
        elif balance == 'credit':
            # Credit items typically positive but may appear negative
            # in certain presentations (liabilities, revenue)
            return 'positive'
        
        return None
    
    def analyze_value_consistency(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze if the value sign is consistent with balance type.
        
        Returns:
            Dictionary with consistency analysis
        """
        balance_type = self.classify(properties)
        value = properties.get('value')
        
        if value is None or balance_type == 'unknown':
            return {
                'can_analyze': False,
                'is_consistent': None,
                'reason': 'Insufficient information'
            }
        
        try:
            numeric_value = float(value) if not isinstance(value, (int, float)) else value
        except (ValueError, TypeError):
            return {
                'can_analyze': False,
                'is_consistent': None,
                'reason': 'Value is not numeric'
            }
        
        expected_sign = self.get_expected_sign(properties)
        actual_sign = 'positive' if numeric_value >= 0 else 'negative'
        
        return {
            'can_analyze': True,
            'is_consistent': expected_sign == actual_sign,
            'expected_sign': expected_sign,
            'actual_sign': actual_sign,
            'value': numeric_value,
            'balance_type': balance_type
        }


__all__ = ['AccountingClassifier']