"""
CCQ Mapper Concept Filter
==========================

Filters facts to determine which should be mapped to financial statements
and which are metadata/non-mappable fields.

This module now supports market-agnostic filtering by accepting a market
parameter to configure market-specific namespace and pattern exclusions.

Excludes:
    - Market-specific metadata (DEI for SEC, FRC for UK, etc.)
    - Statement reference fields (ExtensibleList/Enumeration)
    - Universal metadata (country/currency/exchange codes)
    - Other non-financial metadata

Based on Map Pro's: engines/mapper/resolvers/fact_filter.py
"""

from typing import Dict, Any, Optional

# Import market configuration system with fallback for both relative and absolute imports
try:
    from .market_config import MarketConfig, get_namespace_from_qname
    MARKET_CONFIG_AVAILABLE = True
except ImportError:
    try:
        from market_config import MarketConfig, get_namespace_from_qname
        MARKET_CONFIG_AVAILABLE = True
    except ImportError:
        # Fallback for backward compatibility
        try:
            from .filter_constants import (
                NON_MAPPABLE_NAMESPACES,
                NON_MAPPABLE_PATTERNS,
                get_namespace_from_qname
            )
        except ImportError:
            from filter_constants import (
                NON_MAPPABLE_NAMESPACES,
                NON_MAPPABLE_PATTERNS,
                get_namespace_from_qname
            )
        MARKET_CONFIG_AVAILABLE = False
        MarketConfig = None


class ConceptFilter:
    """
    Determines if facts should be mapped to financial statements.
    
    Now supports market-aware filtering by accepting a market parameter
    in the constructor. If no market is specified, defaults to SEC.
    
    Uses namespace and pattern matching to identify metadata facts
    that should be excluded from mapping operations.
    
    Responsibilities:
    - Filter by namespace (market-specific: dei/ecd/srt for SEC, bus/core for FCA, etc.)
    - Filter by universal namespaces (country, currency, exch, etc.)
    - Filter by pattern (EntityCentralIndexKey, DocumentType, etc.)
    - Filter extensible references (lists/enumerations)
    
    Does NOT handle:
    - Dimensional context filtering (parsed_facts_loader handles this)
    - Value type filtering (property_extractor handles this)
    """
    
    def __init__(self, market: Optional[str] = None):
        """
        Initialize concept filter with optional market specification.
        
        Args:
            market: Market identifier (sec, fca, esma, or None for default 'sec')
                   If None, defaults to SEC for backward compatibility
        
        Examples:
            >>> filter = ConceptFilter()              # Defaults to SEC
            >>> filter = ConceptFilter('sec')         # Explicit SEC
            >>> filter = ConceptFilter('fca')         # UK FCA filtering
            >>> filter = ConceptFilter('esma')        # EU ESMA filtering
        """
        # Default to SEC market if not specified (backward compatibility)
        if market is None:
            market = 'sec'
        
        self.market = market
        
        # Initialize market configuration
        if MARKET_CONFIG_AVAILABLE:
            self.market_config = MarketConfig(market)
            self.non_mappable_namespaces = self.market_config.get_non_mappable_namespaces()
            self.non_mappable_patterns = self.market_config.get_non_mappable_patterns()
        else:
            # Fallback to legacy constants (SEC defaults)
            self.market_config = None
            self.non_mappable_namespaces = NON_MAPPABLE_NAMESPACES
            self.non_mappable_patterns = NON_MAPPABLE_PATTERNS
    
    def is_mappable_fact(self, fact: Dict[str, Any]) -> bool:
        """
        Determine if a fact should be mapped to financial statements.
        
        Applies multiple filters to identify non-mappable facts:
        1. Namespace filter (market-specific + universal metadata)
        2. Pattern filter (EntityCentralIndexKey, DocumentType, etc.)
        3. Extensible list/enumeration filter
        
        Args:
            fact: Fact dictionary to evaluate
            
        Returns:
            True if fact should be mapped, False if it's metadata
        """
        concept = self._extract_concept_qname(fact)
        
        if not concept:
            # No concept identifier - cannot map
            return False
        
        # Check namespace exclusions
        if self._is_non_mappable_namespace(concept):
            return False
        
        # Check pattern exclusions
        if self._matches_non_mappable_pattern(concept):
            return False
        
        # Check for extensible list/enumeration references
        if self._is_extensible_reference(concept):
            return False
        
        return True
    
    def _extract_concept_qname(self, fact: Dict[str, Any]) -> str:
        """
        Extract concept qname from fact with fallback chain.
        
        Args:
            fact: Fact dictionary
            
        Returns:
            Concept qname or empty string
        """
        return (
            fact.get('concept_qname') or
            fact.get('qname') or
            fact.get('concept') or
            fact.get('concept_local_name') or
            ''
        )
    
    def _is_non_mappable_namespace(self, concept: str) -> bool:
        """
        Check if concept belongs to a non-mappable namespace.
        
        Uses market-aware configuration to determine which namespaces
        are metadata vs. financial data.
        
        Args:
            concept: Concept name to check
            
        Returns:
            True if namespace should not be mapped
        """
        namespace = get_namespace_from_qname(concept)
        
        if not namespace:
            # No namespace prefix - treat as mappable
            # (could be company extension without prefix)
            return False
        
        return namespace in self.non_mappable_namespaces
    
    def _matches_non_mappable_pattern(self, concept: str) -> bool:
        """
        Check if concept matches non-mappable patterns.
        
        Uses market-aware configuration to determine which patterns
        represent document/entity metadata vs. financial data.
        
        Args:
            concept: Concept name to check
            
        Returns:
            True if matches a non-mappable pattern
        """
        concept_lower = concept.lower()
        
        for pattern in self.non_mappable_patterns:
            if pattern.lower() in concept_lower:
                return True
        
        return False
    
    def _is_extensible_reference(self, concept: str) -> bool:
        """
        Check if concept is an extensible list/enumeration reference.
        
        These are pointers to data, not the data itself.
        
        Args:
            concept: Concept name to check
            
        Returns:
            True if concept is an extensible reference
        """
        concept_lower = concept.lower()
        return (
            'extensiblelist' in concept_lower or
            'extensibleenumeration' in concept_lower
        )
    
    def get_filter_reason(self, fact: Dict[str, Any]) -> str:
        """
        Get the reason why a fact was filtered (for logging/debugging).
        
        Args:
            fact: Fact dictionary
            
        Returns:
            Reason string (e.g., "Non-mappable namespace: dei")
        """
        concept = self._extract_concept_qname(fact)
        
        if not concept:
            return "No concept identifier"
        
        # Check namespace
        namespace = get_namespace_from_qname(concept)
        if namespace and namespace in self.non_mappable_namespaces:
            return f"Non-mappable namespace: {namespace}"
        
        # Check patterns
        concept_lower = concept.lower()
        for pattern in self.non_mappable_patterns:
            if pattern.lower() in concept_lower:
                return f"Non-mappable pattern: {pattern}"
        
        # Check extensible
        if 'extensiblelist' in concept_lower or 'extensibleenumeration' in concept_lower:
            return "Extensible reference"
        
        return "Unknown reason"
    
    def get_market_info(self) -> Dict[str, Any]:
        """
        Get information about the current market configuration.
        
        Returns:
            Dictionary with market configuration details
        """
        if self.market_config:
            return {
                'market': self.market,
                'market_name': self.market_config.get_market_name(),
                'non_mappable_namespace_count': len(self.non_mappable_namespaces),
                'non_mappable_pattern_count': len(self.non_mappable_patterns),
                'namespaces': sorted(self.non_mappable_namespaces)
            }
        else:
            return {
                'market': self.market,
                'market_name': 'SEC (legacy mode)',
                'non_mappable_namespace_count': len(self.non_mappable_namespaces),
                'non_mappable_pattern_count': len(self.non_mappable_patterns),
                'namespaces': sorted(self.non_mappable_namespaces)
            }


__all__ = ['ConceptFilter']