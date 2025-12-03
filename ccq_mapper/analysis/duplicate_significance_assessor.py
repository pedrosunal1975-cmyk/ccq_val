# File: engines/ccq_mapper/analysis/duplicate_significance_assessor.py

"""
Duplicate Significance Assessor
================================

Assesses financial significance of duplicate facts.

Responsibility:
- Determine significance level (HIGH/MEDIUM/LOW)
- Identify core financial concepts
- Classify financial vs non-financial duplicates

Financial Significance Levels:
- HIGH: Core financial statement line items (totals, key metrics)
- MEDIUM: Financial data and detail line items
- LOW: Non-financial disclosures (cyber security, footnotes)
"""

from typing import Dict, Any


# Financial significance categories
SIGNIFICANCE_HIGH = 'HIGH'
SIGNIFICANCE_MEDIUM = 'MEDIUM'
SIGNIFICANCE_LOW = 'LOW'


class DuplicateSignificanceAssessor:
    """Assesses financial significance of duplicates."""
    
    # Non-financial keywords (cyber security, etc.)
    NON_FINANCIAL_KEYWORDS = [
        'cyber', 'security breach', 'data breach', 'hacking',
        'ransomware', 'phishing', 'malware'
    ]
    
    # Core financial concepts
    CORE_FINANCIAL_KEYWORDS = [
        'assets', 'liabilities', 'equity', 'revenue', 'income', 'expense',
        'cash', 'earnings', 'profit', 'loss', 'debt', 'capital'
    ]
    
    # Main financial statements
    MAIN_STATEMENTS = ['balance_sheet', 'income_statement', 'cash_flow']
    
    @staticmethod
    def assess_significance(
        concept: str,
        statement_type: str,
        monetary_type: str,
        aggregation_type: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess financial significance of a duplicate.
        
        Everything is financially significant except cyber security and
        similar non-financial disclosures.
        
        Args:
            concept: Concept identifier
            statement_type: Classified statement type
            monetary_type: Classified monetary type
            aggregation_type: Classified aggregation type
            properties: Fact properties
            
        Returns:
            Significance assessment dictionary with:
            - level: SIGNIFICANCE_HIGH/MEDIUM/LOW
            - reason: Explanation of significance level
            - is_core_financial: Whether this is core financial data
        """
        concept_lower = concept.lower()
        label_lower = properties.get('label', '').lower()
        
        # Check for non-financial concepts
        if DuplicateSignificanceAssessor._is_non_financial(concept_lower, label_lower):
            return {
                'level': SIGNIFICANCE_LOW,
                'reason': 'Non-financial disclosure (cyber security, etc.)',
                'is_core_financial': False
            }
        
        # Check if core financial concept
        is_core = DuplicateSignificanceAssessor._is_core_financial(concept_lower)
        
        # Main financial statements = HIGH or MEDIUM significance
        if statement_type in DuplicateSignificanceAssessor.MAIN_STATEMENTS:
            if aggregation_type == 'total' or is_core:
                return {
                    'level': SIGNIFICANCE_HIGH,
                    'reason': f'Core {statement_type} line item',
                    'is_core_financial': True
                }
            else:
                return {
                    'level': SIGNIFICANCE_MEDIUM,
                    'reason': f'{statement_type} detail line item',
                    'is_core_financial': True
                }
        
        # Text/footnotes = LOW significance (unless core concept)
        if monetary_type in ['text', 'nil']:
            if is_core:
                return {
                    'level': SIGNIFICANCE_MEDIUM,
                    'reason': 'Text disclosure of core concept',
                    'is_core_financial': True
                }
            else:
                return {
                    'level': SIGNIFICANCE_LOW,
                    'reason': 'Text disclosure or footnote',
                    'is_core_financial': False
                }
        
        # Everything else = MEDIUM (financially significant by default)
        return {
            'level': SIGNIFICANCE_MEDIUM,
            'reason': 'Financial data (not core statement)',
            'is_core_financial': True
        }
    
    @staticmethod
    def _is_non_financial(concept_lower: str, label_lower: str) -> bool:
        """Check if concept is non-financial."""
        return any(
            keyword in concept_lower or keyword in label_lower
            for keyword in DuplicateSignificanceAssessor.NON_FINANCIAL_KEYWORDS
        )
    
    @staticmethod
    def _is_core_financial(concept_lower: str) -> bool:
        """Check if concept is core financial."""
        return any(
            keyword in concept_lower
            for keyword in DuplicateSignificanceAssessor.CORE_FINANCIAL_KEYWORDS
        )


__all__ = [
    'DuplicateSignificanceAssessor',
    'SIGNIFICANCE_HIGH',
    'SIGNIFICANCE_MEDIUM',
    'SIGNIFICANCE_LOW'
]