"""
CCQ Mapper Filters
==================

Market-agnostic concept filtering for CCQ mapper.
Supports SEC, FCA, ESMA, and unknown markets.

Components:
- ConceptFilter: Main filtering class (now market-aware)
- MarketConfig: Market-specific configuration system
- filter_constants: Legacy namespace/pattern definitions (backward compatible)

Usage (New - Market-Aware):
    from engines.ccq_mapper.filters import ConceptFilter, MarketConfig
    
    # Explicit market specification
    filter = ConceptFilter('fca')  # UK FCA filtering
    if filter.is_mappable_fact(fact):
        # Process fact
        pass
    
    # Get market configuration
    config = MarketConfig('esma')  # EU ESMA configuration
    namespaces = config.get_non_mappable_namespaces()

Usage (Legacy - Backward Compatible):
    from engines.ccq_mapper.filters import ConceptFilter
    
    # No parameters = SEC default (backward compatible)
    filter = ConceptFilter()
    if filter.is_mappable_fact(fact):
        # Process fact
        pass
"""

# New market-aware components
from .market_config import (
    MarketConfig,
    Market,
    create_market_config,
    get_namespace_from_qname,
    UNIVERSAL_NON_MAPPABLE_NAMESPACES,
    SEC_METADATA_NAMESPACES,
    FCA_METADATA_NAMESPACES,
    ESMA_METADATA_NAMESPACES,
    STANDARD_FINANCIAL_NAMESPACES,
)

# Core filtering
from .concept_filter import ConceptFilter

# Legacy exports (backward compatibility)
from .filter_constants import (
    NON_MAPPABLE_NAMESPACES,
    NON_MAPPABLE_PATTERNS,
    MAPPABLE_NAMESPACES,
    is_standard_taxonomy_namespace,
)

__all__ = [
    # Core filtering
    'ConceptFilter',
    
    # Market configuration (NEW)
    'MarketConfig',
    'Market',
    'create_market_config',
    
    # Market-specific namespaces (NEW)
    'UNIVERSAL_NON_MAPPABLE_NAMESPACES',
    'SEC_METADATA_NAMESPACES',
    'FCA_METADATA_NAMESPACES',
    'ESMA_METADATA_NAMESPACES',
    'STANDARD_FINANCIAL_NAMESPACES',
    
    # Utility functions
    'get_namespace_from_qname',
    'is_standard_taxonomy_namespace',
    
    # Legacy exports (DEPRECATED - use MarketConfig instead)
    'NON_MAPPABLE_NAMESPACES',
    'NON_MAPPABLE_PATTERNS',
    'MAPPABLE_NAMESPACES',
]