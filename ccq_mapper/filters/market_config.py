"""
CCQ Mapper Market Configuration
================================

Defines market-specific filtering rules for different regulatory jurisdictions.

This module supports market-agnostic operation by providing configurable
namespace and pattern filtering based on the target market.

Supported Markets:
- SEC (United States - Securities and Exchange Commission)
- FCA (United Kingdom - Financial Conduct Authority)
- ESMA (European Union - European Securities and Markets Authority)

Location: engines/ccq_mapper/filters/market_config.py
"""

from typing import Set, Dict, List
from enum import Enum


class Market(str, Enum):
    """Supported regulatory markets."""
    SEC = 'sec'      # United States
    FCA = 'fca'      # United Kingdom
    ESMA = 'esma'    # European Union
    UNKNOWN = 'unknown'  # Default/fallback


# ============================================================================
# UNIVERSAL (MARKET-AGNOSTIC) EXCLUSIONS
# ============================================================================

# These namespaces are metadata/codes that should be filtered regardless of market
UNIVERSAL_NON_MAPPABLE_NAMESPACES: Set[str] = {
    'country',   # Country codes (ISO 3166) - universal
    'currency',  # Currency codes (ISO 4217) - universal
    'exch',      # Exchange codes (stock exchanges) - universal
    'naics',     # North American Industry Classification System - universal
    'sic',       # Standard Industry Classification codes - universal
    'stpr',      # State/Province codes - universal
}


# ============================================================================
# MARKET-SPECIFIC METADATA NAMESPACES
# ============================================================================

# SEC-specific metadata namespaces (United States)
SEC_METADATA_NAMESPACES: Set[str] = {
    'dei',       # Document and Entity Information (SEC-specific)
    'ecd',       # Executive Compensation Disclosure (SEC-specific)
    'srt',       # SEC Reporting Taxonomy (mostly labels/references)
}

# FCA-specific metadata namespaces (United Kingdom)
FCA_METADATA_NAMESPACES: Set[str] = {
    'bus',       # UK Business namespace (company info)
    'core',      # UK Core metadata
    'frc',       # Financial Reporting Council references (when used for metadata)
}

# ESMA-specific metadata namespaces (European Union)
ESMA_METADATA_NAMESPACES: Set[str] = {
    'esef_cor',  # ESEF Core metadata
    'esef_all',  # ESEF All metadata (when used for document info)
}


# ============================================================================
# MARKET-SPECIFIC DOCUMENT PATTERNS
# ============================================================================

# SEC-specific document metadata patterns
SEC_DOCUMENT_PATTERNS: List[str] = [
    'EntityCentralIndexKey',
    'DocumentType',
    'DocumentPeriodEndDate',
    'CurrentFiscalYearEndDate',
    'DocumentFiscalPeriodFocus',
    'DocumentFiscalYearFocus',
    'AmendmentFlag',
    'DocumentTransitionReport',
    'EntityFileNumber',
    'EntityRegistrantName',
    'EntityIncorporationState',
]

# FCA-specific document metadata patterns
FCA_DOCUMENT_PATTERNS: List[str] = [
    'EntityRegistrationNumber',
    'EntityTradingStatus',
    'EntitySICCode',
    'EntityCurrentLegalName',
]

# ESMA-specific document metadata patterns
ESMA_DOCUMENT_PATTERNS: List[str] = [
    'EntityLegalFormCode',
    'EntityRegisteredOffice',
    'EntityPublicationDate',
]


# ============================================================================
# UNIVERSAL PATTERNS (MARKET-AGNOSTIC)
# ============================================================================

# These patterns apply to all markets
UNIVERSAL_NON_MAPPABLE_PATTERNS: List[str] = [
    # Extensible list/enumeration patterns (universal)
    'StatementOfFinancialPositionExtensibleList',
    'ExtensibleEnumeration',
    'ExtensibleList',
]


# ============================================================================
# MAPPABLE NAMESPACES (FOR REFERENCE)
# ============================================================================

# Standard taxonomy namespaces that contain financial data
STANDARD_FINANCIAL_NAMESPACES: Set[str] = {
    'us-gaap',   # US GAAP taxonomy
    'ifrs',      # IFRS taxonomy (basic)
    'ifrs-full', # Full IFRS taxonomy
    'uk-gaap',   # UK GAAP
    'frc',       # UK Financial Reporting Council (when used for financial concepts)
    'esef',      # European Single Electronic Format (financial concepts)
}


# ============================================================================
# MARKET CONFIGURATION BUILDER
# ============================================================================

class MarketConfig:
    """
    Configuration for market-specific filtering rules.
    
    Provides methods to get non-mappable namespaces and patterns
    for a specific regulatory market.
    """
    
    def __init__(self, market: str = 'sec'):
        """
        Initialize market configuration.
        
        Args:
            market: Market identifier (sec, fca, esma, or unknown)
        """
        # Normalize market string
        market_lower = market.lower() if market else 'unknown'
        
        # Validate market
        try:
            self.market = Market(market_lower)
        except ValueError:
            # Unknown market - use UNKNOWN default
            self.market = Market.UNKNOWN
    
    def get_non_mappable_namespaces(self) -> Set[str]:
        """
        Get complete set of non-mappable namespaces for this market.
        
        Returns:
            Set of namespace prefixes to exclude from mapping
        """
        # Start with universal namespaces (always excluded)
        namespaces = UNIVERSAL_NON_MAPPABLE_NAMESPACES.copy()
        
        # Add market-specific metadata namespaces
        if self.market == Market.SEC:
            namespaces.update(SEC_METADATA_NAMESPACES)
        elif self.market == Market.FCA:
            namespaces.update(FCA_METADATA_NAMESPACES)
        elif self.market == Market.ESMA:
            namespaces.update(ESMA_METADATA_NAMESPACES)
        elif self.market == Market.UNKNOWN:
            # For unknown markets, include all known metadata namespaces
            # to be conservative and avoid mapping metadata
            namespaces.update(SEC_METADATA_NAMESPACES)
            namespaces.update(FCA_METADATA_NAMESPACES)
            namespaces.update(ESMA_METADATA_NAMESPACES)
        
        return namespaces
    
    def get_non_mappable_patterns(self) -> List[str]:
        """
        Get complete list of non-mappable patterns for this market.
        
        Returns:
            List of concept patterns to exclude from mapping
        """
        # Start with universal patterns (always excluded)
        patterns = UNIVERSAL_NON_MAPPABLE_PATTERNS.copy()
        
        # Add market-specific document patterns
        if self.market == Market.SEC:
            patterns.extend(SEC_DOCUMENT_PATTERNS)
        elif self.market == Market.FCA:
            patterns.extend(FCA_DOCUMENT_PATTERNS)
        elif self.market == Market.ESMA:
            patterns.extend(ESMA_DOCUMENT_PATTERNS)
        elif self.market == Market.UNKNOWN:
            # For unknown markets, include all known patterns
            patterns.extend(SEC_DOCUMENT_PATTERNS)
            patterns.extend(FCA_DOCUMENT_PATTERNS)
            patterns.extend(ESMA_DOCUMENT_PATTERNS)
        
        return patterns
    
    def is_standard_taxonomy_namespace(self, namespace: str) -> bool:
        """
        Check if namespace is a standard financial taxonomy.
        
        Args:
            namespace: Namespace prefix (e.g., 'us-gaap', 'ifrs')
            
        Returns:
            True if standard taxonomy, False if company extension
        """
        return namespace.lower() in STANDARD_FINANCIAL_NAMESPACES
    
    def get_market_name(self) -> str:
        """Get human-readable market name."""
        market_names = {
            Market.SEC: 'SEC (United States)',
            Market.FCA: 'FCA (United Kingdom)',
            Market.ESMA: 'ESMA (European Union)',
            Market.UNKNOWN: 'Unknown/Multiple Markets'
        }
        return market_names.get(self.market, 'Unknown')


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_namespace_from_qname(qname: str) -> str:
    """
    Extract namespace prefix from qualified name.
    
    Args:
        qname: Qualified name (e.g., 'us-gaap:Assets')
        
    Returns:
        Namespace prefix or empty string
    """
    if ':' in qname:
        return qname.split(':', 1)[0].lower()
    return ''


def create_market_config(market: str = 'sec') -> MarketConfig:
    """
    Factory function to create market configuration.
    
    Args:
        market: Market identifier (sec, fca, esma)
        
    Returns:
        MarketConfig instance
    """
    return MarketConfig(market)


__all__ = [
    'Market',
    'MarketConfig',
    'UNIVERSAL_NON_MAPPABLE_NAMESPACES',
    'SEC_METADATA_NAMESPACES',
    'FCA_METADATA_NAMESPACES',
    'ESMA_METADATA_NAMESPACES',
    'STANDARD_FINANCIAL_NAMESPACES',
    'get_namespace_from_qname',
    'create_market_config',
]