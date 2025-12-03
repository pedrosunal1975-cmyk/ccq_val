# File: filing_cache_manager.py
# Location: engines/fact_authority/filings_reader/filing_cache_manager.py

"""
Filing Cache Manager
====================

Manages cached filing profiles for fast subsequent access.

Caches FilingProfile objects to avoid repeated file discovery.
Uses data_paths configuration for cache location - NO hardcoded paths.

Cache structure:
    {cache_base}/
        {market}/
            {company}/
                {filing_type}/
                    {filing_id}.json

Features:
- Atomic writes using temp files
- Cache validation
- Automatic cache cleanup
- Version control

Classes:
    FilingCacheManager: Manages filing profile cache
"""

from pathlib import Path
from typing import Optional, Dict
import json
import logging
from datetime import datetime
import tempfile
import shutil

from core import data_paths
from engines.fact_authority.filings_reader.filing_profile import FilingProfile


logger = logging.getLogger(__name__)


class FilingCacheManager:
    """
    Manages cached filing profiles for fast access.
    
    Caches FilingProfile objects to disk to avoid repeated file discovery.
    Cache location comes from data_paths configuration - NO hardcoded paths.
    
    Key features:
    - Atomic writes (temp file + rename)
    - Cache validation
    - Market-organized structure
    - JSON serialization
    """
    
    CACHE_VERSION = '1.0'
    
    def __init__(self):
        """
        Initialize filing cache manager.
        
        Raises:
            ValueError: If data_paths not initialized or cache path not configured
        """
        if not data_paths.ccq_paths:
            raise ValueError(
                "data_paths not initialized. Call initialize_paths() first."
            )
        
        if not data_paths.ccq_paths.filings_cache:
            raise ValueError(
                "Filings cache path not configured in data_paths. "
                "Set CCQ_FILINGS_CACHE_PATH in .env file."
            )
        
        self.cache_base_path = data_paths.ccq_paths.filings_cache
        
        # Ensure cache directory exists
        try:
            self.cache_base_path.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            logger.warning(f"Cannot create cache directory: {self.cache_base_path}")
    
    def get_cache_path(
        self,
        market: str,
        company: str,
        filing_type: str,
        filing_id: str
    ) -> Path:
        """
        Get cache file path for a filing.
        
        Args:
            market: Market identifier (e.g., 'sec')
            company: Company identifier
            filing_type: Filing type (e.g., '10-K')
            filing_id: Unique filing identifier
            
        Returns:
            Path to cache file
        """
        cache_file = (
            self.cache_base_path /
            market.lower() /
            company /
            filing_type /
            f"{filing_id}.json"
        )
        
        return cache_file
    
    def is_cache_valid(self, cache_path: Path) -> bool:
        """
        Check if cached profile is valid.
        
        Args:
            cache_path: Path to cache file
            
        Returns:
            True if cache is valid and readable
        """
        if not cache_path.exists():
            return False
        
        if not cache_path.is_file():
            return False
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check cache version
            if data.get('cache_version') != self.CACHE_VERSION:
                logger.debug(f"Cache version mismatch: {cache_path}")
                return False
            
            # Check format version
            profile_data = data.get('profile', {})
            if not profile_data.get('format_version'):
                logger.debug(f"Missing format version: {cache_path}")
                return False
            
            return True
        
        except Exception as e:
            logger.warning(f"Invalid cache file {cache_path}: {e}")
            return False
    
    def load_profile(
        self,
        market: str,
        company: str,
        filing_type: str,
        filing_id: str
    ) -> Optional[FilingProfile]:
        """
        Load cached filing profile.
        
        Args:
            market: Market identifier
            company: Company identifier
            filing_type: Filing type
            filing_id: Filing identifier
            
        Returns:
            FilingProfile if cached and valid, None otherwise
        """
        cache_path = self.get_cache_path(market, company, filing_type, filing_id)
        
        if not self.is_cache_valid(cache_path):
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            profile_data = data.get('profile', {})
            profile = FilingProfile.from_dict(profile_data)
            
            logger.info(f"Loaded cached profile for {company} {filing_type} {filing_id}")
            return profile
        
        except Exception as e:
            logger.error(f"Error loading cache {cache_path}: {e}")
            return None
    
    def save_profile(
        self,
        profile: FilingProfile,
        market: str,
        company: str,
        filing_type: str,
        filing_id: str
    ) -> bool:
        """
        Save filing profile to cache.
        
        Uses atomic write (temp file + rename) for safety.
        
        Args:
            profile: FilingProfile to cache
            market: Market identifier
            company: Company identifier
            filing_type: Filing type
            filing_id: Filing identifier
            
        Returns:
            True if successfully cached
        """
        cache_path = self.get_cache_path(market, company, filing_type, filing_id)
        
        # Ensure directory exists
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Cannot create cache directory {cache_path.parent}: {e}")
            return False
        
        # Prepare cache data
        cache_data = {
            'cache_version': self.CACHE_VERSION,
            'cached_at': datetime.utcnow().isoformat(),
            'profile': profile.to_dict()
        }
        
        # Atomic write using temp file
        try:
            # Write to temp file first
            with tempfile.NamedTemporaryFile(
                mode='w',
                encoding='utf-8',
                dir=cache_path.parent,
                delete=False,
                suffix='.tmp'
            ) as temp_file:
                json.dump(cache_data, temp_file, indent=2)
                temp_path = Path(temp_file.name)
            
            # Atomic rename
            shutil.move(str(temp_path), str(cache_path))
            
            logger.info(f"Cached profile for {company} {filing_type} {filing_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error caching profile to {cache_path}: {e}")
            
            # Clean up temp file if it exists
            try:
                if 'temp_path' in locals() and temp_path.exists():
                    temp_path.unlink()
            except Exception:
                pass
            
            return False
    
    def clear_cache(
        self,
        market: Optional[str] = None,
        company: Optional[str] = None
    ) -> int:
        """
        Clear cache entries.
        
        Args:
            market: Optional market filter
            company: Optional company filter
            
        Returns:
            Number of entries removed
        """
        removed_count = 0
        
        if market:
            # Clear specific market
            market_path = self.cache_base_path / market.lower()
            if market_path.exists():
                if company:
                    # Clear specific company
                    company_path = market_path / company
                    if company_path.exists():
                        shutil.rmtree(company_path)
                        removed_count = 1
                        logger.info(f"Cleared cache for {market}/{company}")
                else:
                    # Clear entire market
                    shutil.rmtree(market_path)
                    removed_count = 1
                    logger.info(f"Cleared cache for {market}")
        else:
            # Clear entire cache
            if self.cache_base_path.exists():
                for item in self.cache_base_path.iterdir():
                    if item.is_dir():
                        shutil.rmtree(item)
                        removed_count += 1
                logger.info("Cleared entire filing cache")
        
        return removed_count
    
    def get_cache_info(self) -> Dict[str, any]:
        """
        Get information about cache contents.
        
        Returns:
            Dictionary with cache statistics
        """
        info = {
            'cache_path': str(self.cache_base_path),
            'exists': self.cache_base_path.exists(),
            'markets': [],
            'total_profiles': 0,
            'total_size_bytes': 0
        }
        
        if not self.cache_base_path.exists():
            return info
        
        try:
            # Count profiles by market
            for market_dir in self.cache_base_path.iterdir():
                if not market_dir.is_dir():
                    continue
                
                market_info = {
                    'market': market_dir.name,
                    'companies': 0,
                    'profiles': 0
                }
                
                # Count profiles in this market
                for cache_file in market_dir.rglob('*.json'):
                    if cache_file.is_file():
                        market_info['profiles'] += 1
                        info['total_profiles'] += 1
                        
                        try:
                            info['total_size_bytes'] += cache_file.stat().st_size
                        except Exception:
                            pass
                
                # Count companies
                for company_dir in market_dir.iterdir():
                    if company_dir.is_dir():
                        market_info['companies'] += 1
                
                info['markets'].append(market_info)
        
        except Exception as e:
            logger.error(f"Error gathering cache info: {e}")
        
        return info
    
    def invalidate_filing(
        self,
        market: str,
        company: str,
        filing_type: str,
        filing_id: str
    ) -> bool:
        """
        Invalidate (delete) a specific cached filing.
        
        Args:
            market: Market identifier
            company: Company identifier
            filing_type: Filing type
            filing_id: Filing identifier
            
        Returns:
            True if cache entry was removed
        """
        cache_path = self.get_cache_path(market, company, filing_type, filing_id)
        
        if not cache_path.exists():
            return False
        
        try:
            cache_path.unlink()
            logger.info(f"Invalidated cache for {company} {filing_type} {filing_id}")
            return True
        except Exception as e:
            logger.error(f"Error invalidating cache {cache_path}: {e}")
            return False