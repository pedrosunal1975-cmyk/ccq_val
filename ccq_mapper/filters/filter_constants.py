"""
CCQ Mapper Filter Constants
============================

DEPRECATED: This module is maintained for backward compatibility only.
New code should use market_config.py for market-agnostic filtering.

Defines which facts should be excluded from financial statement mapping.
These constants default to SEC market configuration.

Based on Map Pro's: engines/mapper/resolvers/constants.py

Migration Note:
- Use market_config.MarketConfig for market-specific filtering
- Use market_config.create_market_config(market) to get configuration
- This module will be removed in a future version
"""

from typing import Set, List
import warnings

# Import from new market configuration system with fallback
try:
    from .market_config import (
        MarketConfig,
        UNIVERSAL_NON_MAPPABLE_NAMESPACES,
        SEC_METADATA_NAMESPACES,
        STANDARD_FINANCIAL_NAMESPACES,
        get_namespace_from_qname as _get_namespace_from_qname
    )
    _default_config = MarketConfig('sec')
except ImportError:
    try:
        from market_config import (
            MarketConfig,
            UNIVERSAL_NON_MAPPABLE_NAMESPACES,
            SEC_METADATA_NAMESPACES,
            STANDARD_FINANCIAL_NAMESPACES,
            get_namespace_from_qname as _get_namespace_from_qname
        )
        _default_config = MarketConfig('sec')
    except ImportError:
        # Fallback if market_config not available (should not happen)
        warnings.warn(
            "market_config module not available, using hardcoded SEC defaults",
            ImportWarning
        )
        
        UNIVERSAL_NON_MAPPABLE_NAMESPACES = {
            'country', 'currency', 'exch', 'naics', 'sic', 'stpr'
        }
        
        SEC_METADATA_NAMESPACES = {
            'dei', 'ecd', 'srt'
        }
        
        STANDARD_FINANCIAL_NAMESPACES = {
            'us-gaap', 'ifrs', 'ifrs-full', 'uk-gaap', 'frc', 'esef'
        }
        
        def _get_namespace_from_qname(qname: str) -> str:
            if ':' in qname:
                return qname.split(':', 1)[0].lower()
            return ''
        
        class MarketConfig:
            def __init__(self, market='sec'):
                self.market = market
            
            def get_non_mappable_namespaces(self):
                return UNIVERSAL_NON_MAPPABLE_NAMESPACES | SEC_METADATA_NAMESPACES
            
            def get_non_mappable_patterns(self):
                return [
                    'EntityCentralIndexKey', 'DocumentType', 'DocumentPeriodEndDate',
                    'CurrentFiscalYearEndDate', 'DocumentFiscalPeriodFocus',
                    'DocumentFiscalYearFocus', 'AmendmentFlag', 'DocumentTransitionReport',
                    'EntityFileNumber', 'EntityRegistrantName', 'EntityIncorporationState',
                    'StatementOfFinancialPositionExtensibleList',
                    'ExtensibleEnumeration', 'ExtensibleList',
                ]
        
        _default_config = MarketConfig('sec')


# ============================================================================
# BACKWARD COMPATIBILITY CONSTANTS (SEC DEFAULTS)
# ============================================================================

# DEPRECATED: Use MarketConfig.get_non_mappable_namespaces() instead
NON_MAPPABLE_NAMESPACES: Set[str] = _default_config.get_non_mappable_namespaces()

# DEPRECATED: Use MarketConfig.get_non_mappable_namespaces() instead
NON_MAPPABLE_NAMESPACES_EXTENDED: Set[str] = NON_MAPPABLE_NAMESPACES.copy()

# DEPRECATED: Use MarketConfig.get_non_mappable_patterns() instead
NON_MAPPABLE_PATTERNS: List[str] = _default_config.get_non_mappable_patterns()

# DEPRECATED: Use market_config.STANDARD_FINANCIAL_NAMESPACES instead
MAPPABLE_NAMESPACES: Set[str] = STANDARD_FINANCIAL_NAMESPACES.copy()


# ============================================================================
# HELPER FUNCTIONS (BACKWARD COMPATIBILITY)
# ============================================================================

def is_standard_taxonomy_namespace(namespace: str) -> bool:
    """
    Check if namespace is a standard taxonomy.
    
    DEPRECATED: Use MarketConfig.is_standard_taxonomy_namespace() instead
    
    Args:
        namespace: Namespace prefix (e.g., 'us-gaap', 'ifrs')
        
    Returns:
        True if standard taxonomy, False if company extension
    """
    return _default_config.is_standard_taxonomy_namespace(namespace)


def get_namespace_from_qname(qname: str) -> str:
    """
    Extract namespace prefix from qualified name.
    
    DEPRECATED: Use market_config.get_namespace_from_qname() instead
    
    Args:
        qname: Qualified name (e.g., 'us-gaap:Assets')
        
    Returns:
        Namespace prefix or empty string
    """
    return _get_namespace_from_qname(qname)


__all__ = [
    'NON_MAPPABLE_NAMESPACES',
    'NON_MAPPABLE_NAMESPACES_EXTENDED',
    'NON_MAPPABLE_PATTERNS',
    'MAPPABLE_NAMESPACES',
    'is_standard_taxonomy_namespace',
    'get_namespace_from_qname',
    'MarketConfig',  # Export new class for migration
]