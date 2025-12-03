# File: engines/fact_authority/process/role_classifier.py
# Path: engines/fact_authority/process/role_classifier.py

"""
Role Classifier
===============

Classifies XBRL role URIs to financial statement types.

Market agnostic - uses role URI patterns and definitions that work
across SEC, FCA, ESMA, and all other markets.
"""

from typing import Dict, Any, Optional
from core.system_logger import get_logger

logger = get_logger(__name__)


class RoleClassifier:
    """
    Classifies XBRL role URIs to statement types.
    
    Uses market-agnostic patterns in role URIs and definitions
    to determine which financial statement a role represents.
    """
    
    # Market agnostic patterns for each statement type
    BALANCE_PATTERNS = [
        'balance', 'position', 'financial position',
        'balancesheet', 'statement of financial position',
        'consolidated balance sheet', 'condensed balance sheet'
    ]
    
    INCOME_PATTERNS = [
        'income', 'operations', 'earnings', 'profit', 'loss',
        'statement of operations', 'statement of income',
        'statement of comprehensive income', 'statement of earnings',
        'profit or loss', 'profit and loss', 'p&l'
    ]
    
    CASH_PATTERNS = [
        'cash flow', 'cashflow', 'statement of cash flows',
        'cash flows', 'consolidated cash flow'
    ]
    
    EQUITY_PATTERNS = [
        'equity', 'stockholders', 'shareholders', 'changes in equity'
    ]
    
    def __init__(self):
        """Initialize role classifier."""
        self.logger = logger
    
    def classify_role(
        self,
        role_uri: str,
        role_info: Dict[str, Any]
    ) -> Optional[str]:
        """
        Classify a role URI to a statement type.
        
        Market agnostic - uses role URI patterns and definitions that work
        across SEC, FCA, ESMA, and all other markets.
        
        Args:
            role_uri: Role URI (e.g., http://fasb.org/.../StatementOfFinancialPosition)
            role_info: Role metadata (definition, used_on, etc.)
            
        Returns:
            Statement type ('balance_sheet', 'income_statement', 'cash_flow', 'other')
            or None if not a financial statement role
        """
        # Get role definition and URI in lowercase for matching
        definition = role_info.get('definition', '').lower()
        uri_lower = role_uri.lower()
        
        # Combine for pattern matching
        text_to_check = f"{definition} {uri_lower}"
        
        # Check each statement type
        if self._matches_patterns(text_to_check, self.BALANCE_PATTERNS):
            return 'balance_sheet'
        
        if self._matches_patterns(text_to_check, self.INCOME_PATTERNS):
            # Exclude comprehensive income from regular income (often separate)
            if 'comprehensive' not in text_to_check or 'other comprehensive' in text_to_check:
                return 'income_statement'
        
        if self._matches_patterns(text_to_check, self.CASH_PATTERNS):
            return 'cash_flow'
        
        # Check for equity/stockholders' equity (classify as 'other')
        if self._matches_patterns(text_to_check, self.EQUITY_PATTERNS):
            return 'other'
        
        # If it's a presentation role but no clear match, classify as 'other'
        used_on = role_info.get('used_on', [])
        if 'presentationLink' in used_on or 'presentation' in uri_lower:
            return 'other'
        
        # Not a statement role
        return None
    
    @staticmethod
    def _matches_patterns(text: str, patterns: list) -> bool:
        """
        Check if text matches any of the patterns.
        
        Args:
            text: Text to check
            patterns: List of patterns to match
            
        Returns:
            True if any pattern matches
        """
        return any(pattern in text for pattern in patterns)


__all__ = ['RoleClassifier']