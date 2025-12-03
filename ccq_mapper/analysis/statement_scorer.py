# File: engines/ccq_mapper/analysis/statement_scorer.py

"""
Statement Scorer
================

Calculates statement construction success metrics.

Responsibility:
- Analyze statement completeness
- Count statement types
- Evaluate statement quality
"""

from typing import Dict, Any, List


class StatementScorer:
    """Scores statement construction effectiveness."""
    
    @staticmethod
    def calculate_statement_success(
        constructed_statements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate statement construction success metrics.
        
        Args:
            constructed_statements: List of constructed statements
            
        Returns:
            Statement success dictionary with:
            - statement_count: Total number of statements
            - statement_types: Dict of statement types and counts
            - total_line_items: Total line items across all statements
            - has_balance_sheet: Whether balance sheet exists
            - has_income_statement: Whether income statement exists
            - has_cash_flow: Whether cash flow statement exists
            - completeness_percentage: Percentage of main statements present
        """
        statement_count = len(constructed_statements)
        
        # Count by statement type
        statement_types = {}
        total_line_items = 0
        
        for statement in constructed_statements:
            stmt_type = statement.get('statement_type', 'unknown')
            statement_types[stmt_type] = statement_types.get(stmt_type, 0) + 1
            
            line_items = statement.get('line_items', [])
            total_line_items += len(line_items)
        
        # Check for main statements
        has_balance_sheet = 'balance_sheet' in statement_types
        has_income_statement = 'income_statement' in statement_types
        has_cash_flow = (
            'cash_flow' in statement_types or 
            'cash_flow_statement' in statement_types
        )
        
        # Calculate completeness (3 main statements)
        completeness = sum([
            has_balance_sheet,
            has_income_statement,
            has_cash_flow
        ])
        completeness_percentage = completeness / 3 * 100
        
        return {
            'statement_count': statement_count,
            'statement_types': statement_types,
            'total_line_items': total_line_items,
            'has_balance_sheet': has_balance_sheet,
            'has_income_statement': has_income_statement,
            'has_cash_flow': has_cash_flow,
            'completeness_percentage': round(completeness_percentage, 2)
        }


__all__ = ['StatementScorer']