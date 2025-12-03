# File: market_structure_detector.py
# Location: engines/fact_authority/filings_reader/market_structure_detector.py

"""
Market Structure Detector
=========================

Detects regulatory market (SEC, FCA, ESMA) from filing directory structure.

Identifies market-specific patterns:
- SEC: Has 'extracted' subfolder, CIK-based filing IDs
- FCA: Different structure, no 'extracted' folder
- ESMA: Different structure, no 'extracted' folder

Provides market-specific configuration for file discovery.

Classes:
    MarketStructureDetector: Detects and analyzes market structures
"""

from pathlib import Path
from typing import Optional, Dict, List
import re
import logging


logger = logging.getLogger(__name__)


class MarketStructureDetector:
    """
    Detects regulatory market and filing structure patterns.
    
    Analyzes directory structure to identify:
    - Regulatory market (SEC, FCA, ESMA)
    - Market-specific folder patterns
    - Presence of 'extracted' subfolder
    - Depth of filing directory structure
    
    This enables market-agnostic file discovery.
    """
    
    # Market identifiers in paths
    MARKET_IDENTIFIERS = {
        'SEC': ['SEC', 'sec', 'edgar', 'cik'],
        'FCA': ['FCA', 'fca', 'uk'],
        'ESMA': ['ESMA', 'esma', 'esef'],
    }
    
    # SEC-specific patterns
    SEC_CIK_PATTERN = r'\d{10}-\d{2}-\d{6}'
    SEC_EXTRACTED_FOLDER = 'extracted'
    
    def __init__(self):
        """Initialize market structure detector."""
        pass
    
    def detect_market(self, filing_path: Path) -> str:
        """
        Detect regulatory market from path.
        
        Args:
            filing_path: Path to filing directory
            
        Returns:
            Market identifier: 'SEC', 'FCA', 'ESMA', or 'UNKNOWN'
        """
        path_str = str(filing_path)
        path_parts = filing_path.parts
        
        # Check path components for market identifiers
        for market, identifiers in self.MARKET_IDENTIFIERS.items():
            for identifier in identifiers:
                if identifier in path_parts or identifier in path_str:
                    logger.debug(f"Detected {market} market from path: {filing_path}")
                    return market
        
        # Try to infer from structure
        if self._has_sec_structure(filing_path):
            return 'SEC'
        
        return 'UNKNOWN'
    
    def _has_sec_structure(self, filing_path: Path) -> bool:
        """
        Check if path has SEC-specific structure.
        
        Args:
            filing_path: Path to check
            
        Returns:
            True if SEC structure detected
        """
        # Check for extracted folder
        if self._has_extracted_folder(filing_path):
            return True
        
        # Check for CIK pattern in path
        for part in filing_path.parts:
            if re.match(self.SEC_CIK_PATTERN, part):
                return True
        
        return False
    
    def _has_extracted_folder(self, filing_path: Path) -> bool:
        """
        Check if filing has SEC 'extracted' subfolder.
        
        Args:
            filing_path: Path to filing directory
            
        Returns:
            True if extracted folder exists
        """
        if not filing_path.is_dir():
            return False
        
        # Check direct children
        for child in filing_path.iterdir():
            if child.is_dir() and child.name.lower() == self.SEC_EXTRACTED_FOLDER:
                return True
        
        return False
    
    def get_search_paths(self, filing_path: Path, market: str) -> List[Path]:
        """
        Get list of paths to search for XBRL files.
        
        Different markets have different structures:
        - SEC: Search in 'extracted' subfolder
        - Others: Search in main filing directory
        
        Args:
            filing_path: Base filing path
            market: Detected market
            
        Returns:
            List of paths to search
        """
        search_paths = []
        
        if market == 'SEC':
            # Check for extracted folder
            extracted_path = filing_path / self.SEC_EXTRACTED_FOLDER
            if extracted_path.exists() and extracted_path.is_dir():
                search_paths.append(extracted_path)
            else:
                # Fallback to main directory
                search_paths.append(filing_path)
        else:
            # For FCA, ESMA, and others, search main directory
            search_paths.append(filing_path)
        
        return search_paths
    
    def analyze_structure(self, filing_path: Path) -> Dict[str, any]:
        """
        Analyze filing directory structure.
        
        Args:
            filing_path: Path to filing directory
            
        Returns:
            Dictionary with structure information:
            {
                'market': 'SEC',
                'has_extracted': True,
                'depth': 5,
                'search_paths': [Path(...)]
            }
        """
        if not filing_path.exists():
            return {
                'market': 'UNKNOWN',
                'has_extracted': False,
                'depth': 0,
                'search_paths': [],
                'error': 'Path does not exist'
            }
        
        # Detect market
        market = self.detect_market(filing_path)
        
        # Check for extracted folder
        has_extracted = self._has_extracted_folder(filing_path)
        
        # Calculate depth from base entities directory
        depth = self._calculate_depth(filing_path)
        
        # Get search paths
        search_paths = self.get_search_paths(filing_path, market)
        
        return {
            'market': market,
            'has_extracted': has_extracted,
            'depth': depth,
            'search_paths': search_paths
        }
    
    def _calculate_depth(self, filing_path: Path) -> int:
        """
        Calculate directory depth from entities base.
        
        Args:
            filing_path: Path to filing directory
            
        Returns:
            Depth level
        """
        path_str = str(filing_path)
        
        # Find 'entities' in path
        if 'entities' in path_str.lower():
            parts_after_entities = []
            found_entities = False
            
            for part in filing_path.parts:
                if found_entities:
                    parts_after_entities.append(part)
                elif 'entities' in part.lower():
                    found_entities = True
            
            return len(parts_after_entities)
        
        # If 'entities' not found, count from root
        return len(filing_path.parts)
    
    def get_market_config(self, market: str) -> Dict[str, any]:
        """
        Get market-specific configuration.
        
        Args:
            market: Market identifier
            
        Returns:
            Configuration dictionary
        """
        configs = {
            'SEC': {
                'has_extracted_folder': True,
                'typical_depth': 5,
                'filing_id_pattern': self.SEC_CIK_PATTERN,
                'instance_format': 'xml',
            },
            'FCA': {
                'has_extracted_folder': False,
                'typical_depth': 4,
                'filing_id_pattern': None,
                'instance_format': 'xhtml',
            },
            'ESMA': {
                'has_extracted_folder': False,
                'typical_depth': 4,
                'filing_id_pattern': None,
                'instance_format': 'xhtml',
            },
        }
        
        return configs.get(market, {
            'has_extracted_folder': False,
            'typical_depth': 5,
            'filing_id_pattern': None,
            'instance_format': 'xml',
        })