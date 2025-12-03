"""
Statement Classifier
====================

Classifies facts into statement types based on PROPERTIES, not concepts.

CRITICAL DIFFERENCE from Map Pro:
- Map Pro: Match concept â†’ Assign to statement
- CCQ: Analyze properties â†’ Predict statement

This is INDUCTIVE reasoning, not DEDUCTIVE matching.
"""

from typing import Dict, Any


class StatementClassifier:
    """
    Predict which statement a fact belongs to based on its properties.
    
    Uses multi-signal approach:
    1. Temporal signal: instant â†’ Balance Sheet, duration â†’ Income/Cash
    2. Accounting signal: debit/credit patterns
    3. Semantic signal: Keywords in label (fallback only)
    4. Aggregation signal: Totals vs line items
    """
    
    # Keyword patterns (used as TERTIARY signal, not primary)
    BALANCE_SHEET_KEYWORDS = [
        'asset', 'liability', 'equity', 'receivable', 'payable',
        'inventory', 'property', 'debt', 'capital', 'retained'
    ]
    
    INCOME_STATEMENT_KEYWORDS = [
        'revenue', 'income', 'expense', 'cost', 'earnings',
        'profit', 'loss', 'sales', 'operating', 'gross', 'net'
    ]
    
    CASH_FLOW_KEYWORDS = [
        'cash', 'cashflow', 'financing', 'investing',
        'operating activities', 'depreciation', 'amortization'
    ]
    
    def classify(self, properties: Dict[str, Any]) -> str:
        """
        Classify fact into statement type.
        
        CRITICAL: period_type is MANDATORY and cannot be overridden by keywords.
        CRITICAL FIX: Only PRIMARY context facts go to main statements.
        
        Classification Rules:
        1. Check if primary context (dimensions == {})
           - If NOT primary → 'other' (dimensional data goes to notes/schedules)
        2. period_type="instant" + monetary → balance_sheet
        3. period_type="instant" + text → other
        4. period_type="duration" → income_statement OR cash_flow (based on keywords)
        5. No valid period_type → other
        
        Args:
            properties: Extracted properties dictionary
            
        Returns:
            Statement type: 'balance_sheet', 'income_statement',
                           'cash_flow', or 'other'
        """
        period_type = (properties.get('period_type') or '').lower()
        value_type = properties.get('value_type')
        is_primary_context = properties.get('is_primary_context', True)
        
        # CRITICAL FIX: Dimensional contexts go to 'other'
        # Only PRIMARY context facts belong in main financial statements
        if not is_primary_context:
            return 'other'
        
        # MANDATORY CHECK: period_type must be valid
        if period_type not in ['instant', 'duration']:
            # No valid period_type → send to 'other'
            # This includes: missing, empty, or invalid period_type
            return 'other'
        
        # INSTANT items: Balance Sheet OR Other (based on value type)
        if period_type == 'instant':
            # Monetary/numeric instant items → Balance Sheet
            if value_type in ['numeric', 'nil']:
                return 'balance_sheet'
            # Text/non-monetary instant items → Other
            else:
                return 'other'
        
        # DURATION items: Income Statement OR Cash Flow
        if period_type == 'duration':
            # Analyze duration facts to distinguish income vs cash flow
            return self._classify_duration_fact(properties)
        
        # Should never reach here (defensive programming)
        return 'other'
    
    def _classify_duration_fact(self, properties: Dict[str, Any]) -> str:
        """
        Classify a duration fact into Income Statement or Cash Flow.
        
        Uses label keywords and balance type as secondary signals.
        All duration facts MUST go to either income_statement or cash_flow.
        
        Args:
            properties: Extracted properties with period_type='duration'
            
        Returns:
            'income_statement' or 'cash_flow'
        """
        label = (properties.get('label') or '').lower()
        qname = (properties.get('qname') or '').lower()
        balance_type = (properties.get('balance_type') or '').lower()
        
        # Combine label and qname for better keyword matching
        combined_text = f"{label} {qname}"
        
        # Strong cash flow indicators (prioritize these)
        strong_cash_keywords = [
            'cash', 'cashflow', 'cash flow', 'financing', 'investing',
            'operating activities', 'operating cash', 'financing activities',
            'investing activities', 'payment', 'proceeds', 'acquisition'
        ]
        
        if any(kw in combined_text for kw in strong_cash_keywords):
            return 'cash_flow'
        
        # Weak cash flow indicators (check qname namespace)
        if 'cashflow' in qname or 'cash_flow' in qname:
            return 'cash_flow'
        
        # Everything else defaults to income statement
        # This includes: revenue, expenses, gains, losses, tax, etc.
        return 'income_statement'


__all__ = ['StatementClassifier']