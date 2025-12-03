# File: core/file_discoverer.py
# Path: core/file_discoverer.py

"""
File Discoverer
===============

Intelligently finds files in directory structures with fuzzy matching.

Uses multiple strategies:
1. Standard expected path
2. Entity name variations
3. Deep directory scanning with fuzzy matching

Handles both traditional XBRL (*.xml) and inline XBRL (*.htm).
"""

from pathlib import Path
from typing import Optional
import json

from core.name_normalizer import NameNormalizer


class FileDiscoverer:
    """
    Discovers files using intelligent search strategies.
    
    Handles variations in directory naming, file naming,
    and directory structure.
    """
    
    def __init__(self, base_paths: dict, path_builders):
        """
        Initialize file discoverer.
        
        Args:
            base_paths: Dict containing base directory paths
            path_builders: PathBuilders instance for constructing expected paths
        """
        self.input_mapped = base_paths.get('input_mapped')
        self.parsed_facts = base_paths.get('parsed_facts')
        self.mapper_xbrl = base_paths.get('mapper_xbrl')
        self.mapper_output = base_paths.get('mapper_output')
        self.path_builders = path_builders
        self.name_normalizer = NameNormalizer()
    
    # ========================================================================
    # MAPPED STATEMENTS DISCOVERY
    # ========================================================================
    
    def find_mapped_statements(self, filing_id: str) -> Optional[Path]:
        """
        Find Map Pro's mapped statements directory for a filing.
        
        Strategy: Scan filesystem for filing_id in statement metadata.
        
        Args:
            filing_id: Filing UUID
        
        Returns:
            Path to mapped statements directory or None
        """
        if not self.input_mapped:
            return None
        
        # Scan all markets
        for market_dir in self.input_mapped.iterdir():
            if not market_dir.is_dir():
                continue
            
            result = self._scan_for_filing(market_dir, filing_id)
            if result:
                return result
        
        return None
    
    def _scan_for_filing(self, directory: Path, filing_id: str) -> Optional[Path]:
        """Recursively scan for filing ID in metadata."""
        for json_file in directory.rglob('*.json'):
            if 'ccq_' in json_file.name:
                continue  # Skip CCQ files
            
            try:
                with open(json_file) as f:
                    data = json.load(f)
                
                # Check if this statement belongs to our filing
                if data.get('metadata', {}).get('filing_id') == filing_id:
                    return json_file.parent
            except Exception:
                continue
        
        return None
    
    # ========================================================================
    # XBRL FILING DISCOVERY
    # ========================================================================
    
    def find_xbrl_filing(
        self,
        market: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Optional[Path]:
        """
        Find XBRL filing using intelligent search strategies.
        
        Tries multiple strategies:
        1. Standard expected path
        2. Entity name variations
        3. Deep directory scan with fuzzy matching
        
        Returns:
            Path to XBRL instance document or None
        """
        if not self.mapper_xbrl:
            return None
        
        # Strategy 1: Try standard expected path
        xbrl_dir = self.path_builders.get_xbrl_filing_path(
            market, entity_name, filing_type, filing_date
        )
        if xbrl_dir:
            result = self._find_xbrl_in_directory(xbrl_dir)
            if result:
                return result
        
        # Strategy 2: Try entity name variations
        name_variations = self.name_normalizer.generate_variations(entity_name)
        
        for variation in name_variations:
            xbrl_dir = self.mapper_xbrl / market / variation / filing_type / filing_date
            result = self._find_xbrl_in_directory(xbrl_dir)
            if result:
                return result
        
        # Strategy 3: Deep scan with fuzzy matching
        market_dir = self.mapper_xbrl / market
        if market_dir.exists():
            result = self._deep_scan_for_xbrl(
                market_dir, entity_name, filing_type, filing_date
            )
            if result:
                return result
        
        return None
    
    def _find_xbrl_in_directory(self, xbrl_dir: Path) -> Optional[Path]:
        """
        Find XBRL instance document in directory.
        
        Handles both traditional XBRL (*.xml) and inline XBRL (*.htm).
        """
        if not xbrl_dir.exists():
            return None
        
        # Check for extracted subdirectory first
        extracted_dir = xbrl_dir / "extracted"
        if extracted_dir.exists():
            xbrl_dir = extracted_dir
        
        # Common XBRL instance patterns (in order of preference)
        patterns = [
            '*-*.xml',      # Traditional: ticker-date.xml
            '*_*.xml',      # Alternative: ticker_date.xml
            '*.xml',        # Any XML file
            '*x10k.htm',    # Inline XBRL for 10-K
            '*x10q.htm'     # Inline XBRL for 10-Q
        ]
        
        for pattern in patterns:
            files = list(xbrl_dir.glob(pattern))
            if files:
                # Filter out linkbase files
                instance_files = [
                    f for f in files
                    if not any(lb in f.name.lower()
                             for lb in ['_lab', '_pre', '_def', '_cal', '_ref', '_linkbase'])
                ]
                if instance_files:
                    return instance_files[0]
        
        return None
    
    def _deep_scan_for_xbrl(
        self,
        market_dir: Path,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Optional[Path]:
        """
        Deep scan market directory for XBRL filing with fuzzy entity matching.
        
        Handles both structures:
        - entities/sec/COMPANY/filings/10-K/ACCESSION/
        - xbrl/sec/COMPANY/10-K/DATE/
        """
        for entity_dir in market_dir.iterdir():
            if not entity_dir.is_dir():
                continue
            
            # Fuzzy match entity name
            if not self.name_normalizer.fuzzy_match(entity_name, entity_dir.name):
                continue
            
            # Check for entities structure: COMPANY/filings/10-K/ACCESSION/
            filings_dir = entity_dir / "filings" / filing_type
            if filings_dir.exists():
                for accession_dir in filings_dir.iterdir():
                    if accession_dir.is_dir():
                        result = self._find_xbrl_in_directory(accession_dir)
                        if result:
                            return result
            
            # Check for date-based structure: COMPANY/10-K/DATE/
            filing_dir = entity_dir / filing_type / filing_date
            result = self._find_xbrl_in_directory(filing_dir)
            if result:
                return result
        
        return None
    
    # ========================================================================
    # PARSED FACTS DISCOVERY
    # ========================================================================
    
    def find_parsed_facts_filing(
        self,
        market: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Optional[Path]:
        """
        Find parsed facts using intelligent search strategies.
        
        Returns:
            Path to parsed facts JSON file or None
        """
        if not self.parsed_facts:
            return None
        
        # Strategy 1: Try standard expected path
        facts_dir = self.path_builders.get_parsed_facts_path(
            market, entity_name, filing_type, filing_date
        )
        result = self._find_json_in_directory(facts_dir)
        if result:
            return result
        
        # Strategy 2: Try entity name variations
        name_variations = self.name_normalizer.generate_variations(entity_name)
        
        for variation in name_variations:
            facts_dir = self.parsed_facts / market / variation / filing_type / filing_date
            result = self._find_json_in_directory(facts_dir)
            if result:
                return result
        
        # Strategy 3: Deep scan
        market_dir = self.parsed_facts / market
        if market_dir.exists():
            result = self._deep_scan_for_parsed_facts(
                market_dir, entity_name, filing_type, filing_date
            )
            if result:
                return result
        
        return None
    
    def _deep_scan_for_parsed_facts(
        self,
        market_dir: Path,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Optional[Path]:
        """Deep scan for parsed facts with fuzzy entity matching."""
        for entity_dir in market_dir.iterdir():
            if not entity_dir.is_dir():
                continue
            
            # Fuzzy match entity name
            if not self.name_normalizer.fuzzy_match(entity_name, entity_dir.name):
                continue
            
            filing_dir = entity_dir / filing_type / filing_date
            result = self._find_json_in_directory(filing_dir)
            if result:
                return result
        
        return None
    
    def _find_json_in_directory(self, directory: Path) -> Optional[Path]:
        """
        Find JSON file in directory.
        
        Searches current directory and one level deep.
        """
        if not directory.exists():
            return None
        
        patterns = [
            'parsed_facts*.json',
            'facts*.json',
            '*.json'
        ]
        
        for pattern in patterns:
            # Current directory
            json_files = list(directory.glob(pattern))
            if json_files:
                return json_files[0]
            
            # One level deep
            json_files = list(directory.glob(f'*/{pattern}'))
            if json_files:
                return json_files[0]
        
        return None
    
    # ========================================================================
    # NULL QUALITY DISCOVERY
    # ========================================================================
    
    def find_mapper_null_quality(
        self,
        market: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Optional[Path]:
        """
        Find null_quality.json using intelligent search strategies.
        
        Returns:
            Path to null_quality.json or None
        """
        if not self.mapper_output:
            return None
        
        # Strategy 1: Try standard expected path
        null_quality_path = self.path_builders.get_mapper_null_quality_path(
            market, entity_name, filing_type, filing_date
        )
        if null_quality_path and null_quality_path.exists():
            return null_quality_path
        
        # Strategy 2: Try entity name variations
        name_variations = self.name_normalizer.generate_variations(entity_name)
        
        for variation in name_variations:
            null_quality_dir = (
                self.mapper_output / market / variation / filing_type / filing_date
            )
            null_quality_file = null_quality_dir / 'null_quality.json'
            
            if null_quality_file.exists():
                return null_quality_file
        
        # Strategy 3: Deep scan
        market_dir = self.mapper_output / market
        if market_dir.exists():
            result = self._deep_scan_for_null_quality(
                market_dir, entity_name, filing_type, filing_date
            )
            if result:
                return result
        
        return None
    
    def _deep_scan_for_null_quality(
        self,
        market_dir: Path,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Optional[Path]:
        """Deep scan for null_quality.json with fuzzy entity matching."""
        for entity_dir in market_dir.iterdir():
            if not entity_dir.is_dir():
                continue
            
            # Fuzzy match entity name
            if not self.name_normalizer.fuzzy_match(entity_name, entity_dir.name):
                continue
            
            filing_dir = entity_dir / filing_type / filing_date
            null_quality_file = filing_dir / 'null_quality.json'
            
            if null_quality_file.exists():
                return null_quality_file
        
        return None


__all__ = ['FileDiscoverer']