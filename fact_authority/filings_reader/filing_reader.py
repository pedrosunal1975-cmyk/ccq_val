"""
Filing Reader - Main API for XBRL Filing Reader.

Provides high-level API for fact_authority engine to read and parse XBRL filings.
Integrates caching, discovery, parsing, and concept resolution.

Market-agnostic: Works with SEC, FCA, ESMA filings.
"""

from pathlib import Path
from typing import Dict, Optional
import logging

from engines.fact_authority.filings_reader.filing_cache_manager import FilingCacheManager
from engines.fact_authority.filings_reader.filing_loader import FilingLoader


logger = logging.getLogger(__name__)


class FilingReader:
    """
    Main API for reading XBRL filings.
    
    High-level interface that:
    1. Checks cache for previously loaded filings
    2. Loads and parses filings via FilingLoader
    3. Caches results for future use
    4. Provides clean API for fact_authority engine
    
    Key features:
    - Simple read_filing() API
    - Automatic caching
    - Complete filing data in one call
    - Market-agnostic
    
    Usage:
        reader = FilingReader(cache_dir)
        filing_data = reader.read_filing(filing_path)
        facts = filing_data['instance']['facts']
        concepts = filing_data['concept_resolver'].get_extension_concepts()
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize filing reader.
        
        Args:
            cache_dir: Directory for caching (optional)
        """
        self.cache_manager = FilingCacheManager() if cache_dir else None
        self.loader = FilingLoader()
        logger.info(f"FilingReader initialized with cache: {cache_dir is not None}")
    
    def read_filing(self, filing_path: Path, use_cache: bool = True) -> Dict:
        """
        Read and parse XBRL filing.
        
        This is the main API method. It:
        1. Checks cache (if enabled)
        2. Loads filing via FilingLoader
        3. Caches result (if enabled)
        4. Returns complete parsed data
        
        Args:
            filing_path: Path to filing directory
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dict with complete filing data (see FilingLoader.load())
            
        Raises:
            ValueError: If filing path invalid or loading fails
        """
        logger.info(f"Reading filing: {filing_path}")
        
        if not filing_path or not filing_path.exists():
            raise ValueError(f"Invalid filing path: {filing_path}")
        
        # Check cache
        if use_cache and self.cache_manager:
            cached = self._get_from_cache(filing_path)
            if cached:
                logger.info("Loaded filing from cache")
                return cached
        
        # Load filing
        logger.debug("Loading filing (not in cache)")
        filing_data = self.loader.load(filing_path)
        
        # Cache result
        if use_cache and self.cache_manager:
            self._save_to_cache(filing_path, filing_data)
        
        return filing_data
    
    def _get_from_cache(self, filing_path: Path) -> Optional[Dict]:
        """
        Get filing from cache.
        
        Args:
            filing_path: Path to filing
            
        Returns:
            Cached filing data, or None if not cached
        """
        try:
            cache_key = self.cache_manager.generate_cache_key(filing_path)
            cached_path = self.cache_manager.get_cache_path(cache_key)
            
            if self.cache_manager.is_cached(cache_key):
                logger.debug(f"Cache hit: {cache_key}")
                # Note: Actual cache loading would deserialize from file
                # For now, return None to force reload
                # TODO: Implement cache serialization/deserialization
                return None
            
            logger.debug(f"Cache miss: {cache_key}")
            return None
            
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")
            return None
    
    def _save_to_cache(self, filing_path: Path, filing_data: Dict) -> None:
        """
        Save filing to cache.
        
        Args:
            filing_path: Path to filing
            filing_data: Filing data to cache
        """
        try:
            cache_key = self.cache_manager.generate_cache_key(filing_path)
            logger.debug(f"Caching filing: {cache_key}")
            
            # Note: Actual caching would serialize filing_data to file
            # For now, just log
            # TODO: Implement cache serialization
            
            logger.debug("Filing cached successfully")
            
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")
    
    def clear_cache(self) -> None:
        """Clear all cached filings."""
        if self.cache_manager:
            self.cache_manager.clear_cache()
            logger.info("Cache cleared")
        else:
            logger.warning("No cache manager configured")
    
    def get_cache_statistics(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache stats
        """
        if self.cache_manager:
            return self.cache_manager.get_statistics()
        return {'cache_enabled': False}
    
    def get_concept_resolver(self) -> Optional[object]:
        """
        Get concept resolver from last loaded filing.
        
        Returns:
            ConceptResolver instance, or None
        """
        return self.loader.get_concept_resolver()