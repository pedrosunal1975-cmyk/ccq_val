# File: engines/ccq_mapper/orchestration/data_loader.py

"""
Data Loader
===========

Handles all data loading operations for the mapper.

Responsibility:
- Load XBRL files
- Load parsed facts
- Load taxonomies
- Coordinate loader components
"""

from typing import Dict, Any, List, Tuple
from pathlib import Path

from core.system_logger import get_logger
from ..loaders.xbrl_loader import XBRLLoader
from ..loaders.parsed_facts_loader import ParsedFactsLoader
from ..loaders.taxonomy_loader import TaxonomyLoader

logger = get_logger(__name__)


class DataLoader:
    """Coordinates all data loading operations."""
    
    def __init__(self):
        """Initialize data loader with all required loaders."""
        self.xbrl_loader = XBRLLoader()
        self.parsed_loader = ParsedFactsLoader()
        self.taxonomy_loader = TaxonomyLoader()
        self.logger = logger
    
    def load_all_inputs(
        self,
        xbrl_path: Path,
        parsed_facts_path: Path,
        taxonomy_paths: List[Path]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any], Dict[str, Any]]:
        """
        Load all required inputs.
        
        Args:
            xbrl_path: Path to raw XBRL filing
            parsed_facts_path: Path to parsed facts JSON
            taxonomy_paths: Paths to taxonomy files
            
        Returns:
            (facts, contexts, metadata) tuple
        """
        self.logger.info("Loading inputs...")
        
        # Load parsed facts (same as Map Pro uses)
        facts, metadata = self.parsed_loader.load_parsed_facts(parsed_facts_path)
        
        # Load XBRL for context analysis
        contexts = self.xbrl_loader.load_contexts(xbrl_path)
        
        # Load taxonomies (for validation, not matching)
        taxonomies = self.taxonomy_loader.load_taxonomies(taxonomy_paths)
        
        self.logger.info(
            f"Loaded {len(facts)} facts, {len(contexts)} contexts, "
            f"{len(taxonomies)} taxonomies"
        )
        
        return facts, contexts, metadata


__all__ = ['DataLoader']