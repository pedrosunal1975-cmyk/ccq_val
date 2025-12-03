# File: core/__init__.py
# Path: core/__init__.py

"""
CCQ Validator Core Module
==========================

Provides foundational components for the Content Consistency and Quality engine.
All core functionality that other modules depend on resides here.

Main Components:
    - ConfigLoader: Configuration management
    - SystemLogger: Logging infrastructure
    - CCQPaths: Path management (main API)
    - CCQCoordinator: Main validation orchestrator (lazy loaded)
    - DatabaseCoordinator: Database operations
    
Helper Components for CCQPaths (used internally):
    - PathBuilders: Constructs standardized paths
    - FileDiscoverer: Finds files with fuzzy matching
    - NameNormalizer: Generates entity name variations

Helper Components for CCQCoordinator (used internally):
    - FilingMetadataParser: Parses filing metadata from paths
    - StatementFileLoader: Loads JSON statement files
    - TaxonomyBuilder: Builds taxonomy accessors
    - ValidationPersister: Saves validation results
"""

# Core imports that are always safe (no heavy dependencies)
from core.config_loader import ConfigLoader
from core.system_logger import SystemLogger
from core.data_paths import CCQPaths, initialize_paths
from core.database_coordinator import DatabaseCoordinator

# Helper components for CCQPaths
from core.path_builders import PathBuilders
from core.file_discoverer import FileDiscoverer
from core.name_normalizer import NameNormalizer

# Helper components for CCQCoordinator
from core.filing_metadata_parser import FilingMetadataParser
from core.statement_file_loader import StatementFileLoader
from core.taxonomy_builder import TaxonomyBuilder
from core.validation_persister import ValidationPersister

# Alias for backward compatibility
DataPathManager = CCQPaths


# Lazy import for CCQCoordinator (only loads when actually used)
def __getattr__(name):
    """
    Lazy load CCQCoordinator to avoid importing validation engines
    unless they're actually needed.
    
    This allows fact_authority and other engines to import core utilities
    without triggering the full CCQ validation stack.
    """
    if name == 'CCQCoordinator':
        from core.ccq_coordinator import CCQCoordinator
        return CCQCoordinator
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    # Main public API
    'ConfigLoader',
    'SystemLogger',
    'CCQPaths',
    'DataPathManager',
    'CCQCoordinator',  # Available via lazy loading
    'DatabaseCoordinator',
    'initialize_paths',
    
    # Helper components for CCQPaths
    'PathBuilders',
    'FileDiscoverer',
    'NameNormalizer',
    
    # Helper components for CCQCoordinator
    'FilingMetadataParser',
    'StatementFileLoader',
    'TaxonomyBuilder',
    'ValidationPersister',
]