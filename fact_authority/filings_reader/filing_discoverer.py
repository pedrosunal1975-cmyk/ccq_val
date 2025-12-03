# File: filing_discoverer.py
# Location: engines/fact_authority/filings_reader/filing_discoverer.py

"""
Filing Discoverer
=================

Deep recursive file discovery for company XBRL filings.

Discovers all files in filing directories with:
- Deep recursion (up to 10 levels)
- Intelligent filtering using FileTypeClassifier
- Market-aware search paths
- Safety limits (size, depth, symlinks)

Works across SEC, FCA, ESMA filing structures.

Classes:
    FilingDiscoverer: Main file discovery engine
"""

from pathlib import Path
from typing import List, Dict, Optional, Set
import logging

from engines.fact_authority.filings_reader.file_type_classifier import FileTypeClassifier
from engines.fact_authority.filings_reader.market_structure_detector import MarketStructureDetector


logger = logging.getLogger(__name__)


class FilingDiscoverer:
    """
    Discovers all XBRL files in company filings with deep recursion.
    
    Key features:
    - Recursive search (up to MAX_DEPTH levels)
    - Intelligent file classification
    - Market-aware search strategy
    - Safety protections (symlinks, size limits)
    - Useless file detection and logging
    
    Works universally across SEC, FCA, ESMA markets.
    """
    
    MAX_DEPTH = 10
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB limit
    
    def __init__(self):
        """Initialize filing discoverer."""
        self.classifier = FileTypeClassifier()
        self.market_detector = MarketStructureDetector()
    
    def discover(
        self,
        filing_path: Path,
        hints: Optional[Dict[str, any]] = None
    ) -> Dict[str, List[Path]]:
        """
        Discover all XBRL files in a filing directory.
        
        Args:
            filing_path: Path to filing directory
            hints: Optional hints from parsed_facts.json
            
        Returns:
            Dictionary organizing files by type:
            {
                'extension_schema': [Path(...)],
                'presentation': [Path(...)],
                'calculation': [Path(...)],
                'definition': [Path(...)],
                'label': [Path(...)],
                'instance': [Path(...)],
                'useless': [Path(...)]
            }
        """
        if not filing_path.exists():
            raise FileNotFoundError(f"Filing path not found: {filing_path}")
        
        if not filing_path.is_dir():
            raise ValueError(f"Filing path must be a directory: {filing_path}")
        
        logger.info(f"Discovering files in: {filing_path}")
        
        # Set hints for classifier
        if hints:
            self.classifier.set_hints(hints)
        
        # Analyze market structure
        structure = self.market_detector.analyze_structure(filing_path)
        market = structure['market']
        search_paths = structure['search_paths']
        
        logger.debug(f"Detected market: {market}")
        logger.debug(f"Search paths: {search_paths}")
        
        # Discover files
        discovered = {
            'extension_schema': [],
            'presentation': [],
            'calculation': [],
            'definition': [],
            'label': [],
            'instance': [],
            'useless': []
        }
        
        # Search each path recursively
        for search_path in search_paths:
            files = self._recursive_discover(search_path, current_depth=0)
            
            # Classify and organize
            for file_path in files:
                classification = self.classifier.classify(file_path)
                
                if classification == 'extension_schema':
                    discovered['extension_schema'].append(file_path)
                
                elif classification == 'presentation':
                    discovered['presentation'].append(file_path)
                
                elif classification == 'calculation':
                    discovered['calculation'].append(file_path)
                
                elif classification == 'definition':
                    discovered['definition'].append(file_path)
                
                elif classification == 'label':
                    discovered['label'].append(file_path)
                
                elif classification in ['instance_xml', 'instance_ixbrl']:
                    discovered['instance'].append(file_path)
                
                elif classification == 'useless':
                    discovered['useless'].append(file_path)
                    logger.debug(f"Ignoring useless file: {file_path.name}")
        
        # Log summary
        logger.info(
            f"Discovered: {len(discovered['extension_schema'])} extension schemas, "
            f"{len(discovered['presentation'])} presentation linkbases, "
            f"{len(discovered['instance'])} instance documents, "
            f"{len(discovered['useless'])} useless files (ignored)"
        )
        
        return discovered
    
    def _recursive_discover(
        self,
        directory: Path,
        current_depth: int
    ) -> List[Path]:
        """
        Recursively discover files with safety limits.
        
        Args:
            directory: Directory to search
            current_depth: Current recursion depth
            
        Returns:
            List of discovered file paths
        """
        if current_depth > self.MAX_DEPTH:
            logger.warning(f"Max depth {self.MAX_DEPTH} reached at: {directory}")
            return []
        
        discovered_files = []
        
        try:
            for item in directory.iterdir():
                # Skip symlinks (prevent loops)
                if item.is_symlink():
                    logger.debug(f"Skipping symlink: {item}")
                    continue
                
                if item.is_dir():
                    # Recurse into subdirectory
                    discovered_files.extend(
                        self._recursive_discover(item, current_depth + 1)
                    )
                
                elif item.is_file():
                    # Check file size
                    if self._is_file_too_large(item):
                        logger.warning(f"Skipping large file: {item.name}")
                        continue
                    
                    # Add file
                    discovered_files.append(item)
        
        except PermissionError:
            logger.warning(f"Permission denied: {directory}")
        
        except Exception as e:
            logger.error(f"Error discovering in {directory}: {e}")
        
        return discovered_files
    
    def _is_file_too_large(self, file_path: Path) -> bool:
        """
        Check if file exceeds size limit.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file is too large
        """
        try:
            size = file_path.stat().st_size
            return size > self.MAX_FILE_SIZE
        except Exception:
            return False
    
    def discover_with_filter(
        self,
        filing_path: Path,
        hints: Optional[Dict[str, any]] = None,
        include_useless: bool = False
    ) -> Dict[str, List[Path]]:
        """
        Discover files with optional useless file exclusion.
        
        Args:
            filing_path: Path to filing directory
            hints: Optional hints from parsed_facts.json
            include_useless: If True, include useless files in results
            
        Returns:
            Dictionary of discovered files
        """
        discovered = self.discover(filing_path, hints)
        
        if not include_useless:
            # Remove useless files from results
            discovered.pop('useless', None)
        
        return discovered
    
    def quick_check(self, filing_path: Path) -> bool:
        """
        Quick check if directory contains XBRL files.
        
        Checks only immediate directory without recursion.
        Useful for validating filing paths before full discovery.
        
        Args:
            filing_path: Path to filing directory
            
        Returns:
            True if XBRL files detected
        """
        if not filing_path.exists() or not filing_path.is_dir():
            return False
        
        try:
            for item in filing_path.iterdir():
                if item.is_file():
                    suffix = item.suffix.lower()
                    if suffix in ['.xsd', '.xml', '.xhtml']:
                        return True
        except Exception:
            return False
        
        return False
    
    def get_discovery_statistics(
        self,
        discovered: Dict[str, List[Path]]
    ) -> Dict[str, int]:
        """
        Get statistics about discovered files.
        
        Args:
            discovered: Dictionary from discover()
            
        Returns:
            Statistics dictionary
        """
        stats = {
            'total_xbrl_files': 0,
            'extension_schemas': len(discovered.get('extension_schema', [])),
            'presentation_linkbases': len(discovered.get('presentation', [])),
            'calculation_linkbases': len(discovered.get('calculation', [])),
            'definition_linkbases': len(discovered.get('definition', [])),
            'label_linkbases': len(discovered.get('label', [])),
            'instance_documents': len(discovered.get('instance', [])),
            'useless_files': len(discovered.get('useless', [])),
        }
        
        # Calculate total XBRL files (excluding useless)
        stats['total_xbrl_files'] = sum([
            stats['extension_schemas'],
            stats['presentation_linkbases'],
            stats['calculation_linkbases'],
            stats['definition_linkbases'],
            stats['label_linkbases'],
            stats['instance_documents'],
        ])
        
        return stats