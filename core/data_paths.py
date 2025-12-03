# File: core/data_paths.py
# Path: core/data_paths.py

"""
CCQ Data Paths
==============

Path management for CCQ validator and mapper.
Manages directory trees - ALL paths come from configuration, NO hardcoded paths.

REFACTORED: This class now acts as a thin orchestrator, delegating to:
- PathBuilders: Constructs standard paths
- FileDiscoverer: Finds files with fuzzy matching
- NameNormalizer: Generates entity name variations
"""

from pathlib import Path
from typing import Optional, Dict

from core.path_builders import PathBuilders
from core.file_discoverer import FileDiscoverer
from core.name_normalizer import NameNormalizer


class CCQPaths:
    """
    Path manager for CCQ validator and mapper - configuration-driven only.
    
    This is the main public API for path management across the CCQ system.
    All methods delegate to specialized helper classes.
    """
    
    def __init__(
        self,
        data_root: str,
        input_path: str,
        output_path: str,
        taxonomy_path: str,
        parsed_facts_path: str,
        mapper_xbrl_path: Optional[str] = None,
        mapper_output_path: Optional[str] = None,
        ccq_logs_path: Optional[str] = None,
        mapper_logs_path: Optional[str] = None,
        unified_output_path: Optional[str] = None,
        taxonomy_cache_path: Optional[str] = None,
        filings_cache_path: Optional[str] = None
    ):
        """
        Initialize path manager.
        
        Args:
            data_root: Root data directory
            input_path: Map Pro mapped statements (read-only)
            output_path: CCQ Validator output directory (write)
            taxonomy_path: Taxonomy library (read-only)
            parsed_facts_path: Map Pro parsed facts (read-only)
            mapper_xbrl_path: Raw XBRL filings (read-only, for CCQ Mapper)
            mapper_output_path: CCQ Mapper output directory (write)
            ccq_logs_path: CCQ validator logs directory
            mapper_logs_path: CCQ mapper logs directory
            unified_output_path: Unified mapper output (fact_authority engine)
            taxonomy_cache_path: Taxonomy cache directory (generated profiles)
            filings_cache_path: Filings cache directory (filing profiles)
        """
        # Store base paths
        self.data_root = Path(data_root)
        self.input_mapped = Path(input_path)
        self.output_validated = Path(output_path)
        self.taxonomies = Path(taxonomy_path)
        self.parsed_facts = Path(parsed_facts_path)
        
        # Optional paths
        self.mapper_xbrl = Path(mapper_xbrl_path) if mapper_xbrl_path else None
        self.mapper_output = Path(mapper_output_path) if mapper_output_path else None
        self.ccq_logs = Path(ccq_logs_path) if ccq_logs_path else None
        self.mapper_logs = Path(mapper_logs_path) if mapper_logs_path else None
        
        # Unified output
        if unified_output_path:
            self.unified_mapped = Path(unified_output_path)
            self.unified_mapped.mkdir(parents=True, exist_ok=True)
        else:
            self.unified_mapped = None
        
        # Cache directories
        if taxonomy_cache_path:
            self.taxonomy_cache = Path(taxonomy_cache_path)
        else:
            self.taxonomy_cache = self.taxonomies / '.cache'
        
        if filings_cache_path:
            self.filings_cache = Path(filings_cache_path)
        else:
            self.filings_cache = self.mapper_xbrl / '.cache' if self.mapper_xbrl else None
        
        # Initialize helper components
        base_paths_dict = {
            'input_mapped': self.input_mapped,
            'output_validated': self.output_validated,
            'parsed_facts': self.parsed_facts,
            'taxonomies': self.taxonomies,
            'mapper_xbrl': self.mapper_xbrl,
            'mapper_output': self.mapper_output,
            'unified_mapped': self.unified_mapped
        }
        
        self._path_builders = PathBuilders(base_paths_dict)
        self._file_discoverer = FileDiscoverer(base_paths_dict, self._path_builders)
        self._name_normalizer = NameNormalizer()
        
        # Ensure directories exist (only if paths are configured)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directories on initialization."""
        directories_to_create = [
            self.output_validated,
            self.mapper_output,
            self.ccq_logs,
            self.mapper_logs,
            self.taxonomy_cache,
            self.filings_cache
        ]
        
        for directory in directories_to_create:
            if directory:
                try:
                    directory.mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    pass  # Will try to create on first use
    
    @classmethod
    def from_config(cls, config):
        """
        Create CCQPaths instance from a ConfigLoader object.
        
        Args:
            config: ConfigLoader instance or dict containing path configuration
        
        Returns:
            CCQPaths instance
        """
        # Handle both ConfigLoader objects and plain dicts
        if hasattr(config, 'get'):
            get_func = config.get
        else:
            get_func = lambda key, default=None: getattr(config, key, default)
        
        return cls(
            data_root=get_func('data_root'),
            input_path=get_func('input_path'),
            output_path=get_func('output_path'),
            taxonomy_path=get_func('taxonomy_path'),
            parsed_facts_path=get_func('parsed_facts_path'),
            mapper_xbrl_path=get_func('mapper_xbrl_path'),
            mapper_output_path=get_func('mapper_output_path'),
            ccq_logs_path=get_func('ccq_logs_path'),
            mapper_logs_path=get_func('mapper_logs_path'),
            unified_output_path=get_func('unified_output_path'),
            taxonomy_cache_path=get_func('taxonomy_cache_path'),
            filings_cache_path=get_func('filings_cache_path')
        )
    
    # ========================================================================
    # PUBLIC API - INPUT PATHS (delegated to PathBuilders)
    # ========================================================================
    
    def get_parsed_facts_path(
        self,
        market: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Path:
        """Get path to parsed facts directory for a filing."""
        return self._path_builders.get_parsed_facts_path(
            market, entity_name, filing_type, filing_date
        )
    
    def get_xbrl_filing_path(
        self,
        market: str,
        entity_name: str,
        filing_type: str,
        filing_date: str,
        filename: Optional[str] = None
    ) -> Optional[Path]:
        """Get path to raw XBRL filing."""
        return self._path_builders.get_xbrl_filing_path(
            market, entity_name, filing_type, filing_date, filename
        )
    
    # ========================================================================
    # PUBLIC API - CCQ VALIDATOR OUTPUT PATHS (delegated to PathBuilders)
    # ========================================================================
    
    def get_output_directory(
        self,
        market_type: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Path:
        """Get CCQ Validator output directory."""
        return self._path_builders.get_output_directory(
            market_type, entity_name, filing_type, filing_date
        )
    
    def get_normalized_statement_path(
        self,
        market_type: str,
        entity_name: str,
        filing_type: str,
        filing_date: str,
        statement_type: str
    ) -> Path:
        """Get path for normalized statement output."""
        return self._path_builders.get_normalized_statement_path(
            market_type, entity_name, filing_type, filing_date, statement_type
        )
    
    def get_validation_report_path(
        self,
        market_type: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Path:
        """Get path for CCQ validation report."""
        return self._path_builders.get_validation_report_path(
            market_type, entity_name, filing_type, filing_date
        )
    
    # ========================================================================
    # PUBLIC API - CCQ MAPPER OUTPUT PATHS (delegated to PathBuilders)
    # ========================================================================
    
    def get_mapper_output_directory(
        self,
        market_type: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Optional[Path]:
        """Get CCQ Mapper output directory."""
        return self._path_builders.get_mapper_output_directory(
            market_type, entity_name, filing_type, filing_date
        )
    
    def get_mapped_statement_path(
        self,
        market_type: str,
        entity_name: str,
        filing_type: str,
        filing_date: str,
        statement_type: str
    ) -> Optional[Path]:
        """Get path for CCQ Mapper mapped statement output."""
        return self._path_builders.get_mapped_statement_path(
            market_type, entity_name, filing_type, filing_date, statement_type
        )
    
    def get_mapper_validation_report_path(
        self,
        market_type: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Optional[Path]:
        """Get path for CCQ Mapper taxonomy validation report."""
        return self._path_builders.get_mapper_validation_report_path(
            market_type, entity_name, filing_type, filing_date
        )
    
    def get_mapper_comparison_report_path(
        self,
        market_type: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Optional[Path]:
        """Get path for CCQ Mapper vs Map Pro comparison report."""
        return self._path_builders.get_mapper_comparison_report_path(
            market_type, entity_name, filing_type, filing_date
        )
    
    def get_mapper_metadata_path(
        self,
        market_type: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Optional[Path]:
        """Get path for CCQ Mapper metadata file."""
        return self._path_builders.get_mapper_metadata_path(
            market_type, entity_name, filing_type, filing_date
        )
    
    def get_mapper_null_quality_path(
        self,
        market_type: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Optional[Path]:
        """Get path for CCQ Mapper null quality report."""
        return self._path_builders.get_mapper_null_quality_path(
            market_type, entity_name, filing_type, filing_date
        )
    
    # ========================================================================
    # PUBLIC API - TAXONOMY PATHS (delegated to PathBuilders)
    # ========================================================================
    
    def get_taxonomy_paths_for_filing(
        self,
        market: str,
        taxonomy_name: Optional[str] = None,
        taxonomy_version: Optional[str] = None
    ) -> list[Path]:
        """Get list of taxonomy paths for a filing."""
        return self._path_builders.get_taxonomy_paths_for_filing(
            market, taxonomy_name, taxonomy_version
        )
    
    # ========================================================================
    # PUBLIC API - FILE DISCOVERY (delegated to FileDiscoverer)
    # ========================================================================
    
    def find_mapped_statements(self, filing_id: str) -> Optional[Path]:
        """Find Map Pro's mapped statements directory for a filing."""
        return self._file_discoverer.find_mapped_statements(filing_id)
    
    def find_xbrl_filing(
        self,
        market: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Optional[Path]:
        """Find XBRL filing using intelligent search strategies."""
        return self._file_discoverer.find_xbrl_filing(
            market, entity_name, filing_type, filing_date
        )
    
    def find_parsed_facts_filing(
        self,
        market: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Optional[Path]:
        """Find parsed facts using intelligent search strategies."""
        return self._file_discoverer.find_parsed_facts_filing(
            market, entity_name, filing_type, filing_date
        )
    
    def find_mapper_null_quality(
        self,
        market: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Optional[Path]:
        """Find null_quality.json using intelligent search strategies."""
        return self._file_discoverer.find_mapper_null_quality(
            market, entity_name, filing_type, filing_date
        )
    
    # ========================================================================
    # PUBLIC API - NAME UTILITIES (delegated to NameNormalizer)
    # ========================================================================
    
    def _generate_name_variations(self, entity_name: str) -> list[str]:
        """
        Generate common variations of entity name.
        
        Note: This is kept for backward compatibility but delegates to NameNormalizer.
        New code should use NameNormalizer directly.
        """
        return self._name_normalizer.generate_variations(entity_name)


# ========================================================================
# GLOBAL INSTANCE (for backward compatibility)
# ========================================================================

ccq_paths: Optional[CCQPaths] = None


def initialize_paths(config: Dict) -> CCQPaths:
    """Initialize global paths instance from configuration."""
    global ccq_paths
    ccq_paths = CCQPaths(
        data_root=config['data_root'],
        input_path=config['input_path'],
        output_path=config['output_path'],
        taxonomy_path=config['taxonomy_path'],
        parsed_facts_path=config['parsed_facts_path'],
        mapper_xbrl_path=config.get('mapper_xbrl_path'),
        mapper_output_path=config.get('mapper_output_path'),
        ccq_logs_path=config.get('ccq_logs_path'),
        mapper_logs_path=config.get('mapper_logs_path'),
        unified_output_path=config.get('unified_output_path'),
        taxonomy_cache_path=config.get('taxonomy_cache_path'),
        filings_cache_path=config.get('filings_cache_path')
    )
    return ccq_paths