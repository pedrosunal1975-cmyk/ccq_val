# File: engines/fact_authority/process/taxonomy_detector.py
# Path: engines/fact_authority/process/taxonomy_detector.py

"""
Taxonomy Detector
=================

Detects and identifies taxonomies from XBRL concept namespaces.

Responsibilities:
    - Extract namespaces from concept names
    - Determine primary financial taxonomy
    - Handle multi-taxonomy scenarios
"""

from typing import Set, List
from core.system_logger import get_logger

logger = get_logger(__name__)


class TaxonomyDetector:
    """
    Detects taxonomies from XBRL concepts.
    
    Identifies which financial reporting taxonomy is primary based on
    concept namespace prefixes (us-gaap, ifrs-full, etc.).
    """
    
    # Financial statement taxonomies in order of precedence
    FINANCIAL_TAXONOMIES = [
        'us-gaap',
        'ifrs-full',
        'ifrs',
        'uk-gaap',
        'esef'
    ]
    
    def extract_namespaces(self, concepts: List[str]) -> Set[str]:
        """
        Extract unique namespace prefixes from concept names.
        
        Args:
            concepts: List of concept names (e.g., ['us-gaap:Assets', 'dei:EntityRegistrantName'])
            
        Returns:
            Set of namespace prefixes (e.g., {'us-gaap', 'dei'})
        """
        namespaces = set()
        
        for concept in concepts:
            if ':' in concept:
                ns = concept.split(':')[0]
                namespaces.add(ns)
        
        logger.debug(f"Extracted {len(namespaces)} namespaces from {len(concepts)} concepts")
        return namespaces
    
    def determine_primary_taxonomy(self, namespaces: Set[str]) -> str:
        """
        Determine primary financial taxonomy from namespace set.
        
        Args:
            namespaces: Set of namespace prefixes
            
        Returns:
            Primary namespace ('us-gaap', 'ifrs-full', 'uk-gaap', etc.)
        """
        # Check for financial taxonomies in priority order
        for taxonomy in self.FINANCIAL_TAXONOMIES:
            if taxonomy in namespaces:
                logger.info(f"Primary taxonomy detected: {taxonomy}")
                return taxonomy
        
        # Default to us-gaap if no financial taxonomy found
        logger.warning(
            f"No standard financial taxonomy in {namespaces}, defaulting to us-gaap"
        )
        return 'us-gaap'
    
    def is_extension_namespace(self, namespace: str) -> bool:
        """
        Check if a namespace is likely a company extension.
        
        Args:
            namespace: Namespace prefix
            
        Returns:
            True if likely an extension namespace
        """
        # Standard taxonomies are NOT extensions
        standard_namespaces = set(self.FINANCIAL_TAXONOMIES) | {
            'dei', 'country', 'currency', 'exch', 'naics', 'sic', 'stpr'
        }
        
        return namespace not in standard_namespaces


__all__ = ['TaxonomyDetector']