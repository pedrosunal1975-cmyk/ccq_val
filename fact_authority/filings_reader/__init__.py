# File: __init__.py
# Location: engines/fact_authority/filings_reader/__init__.py

"""
Filings Reader - Complete XBRL Filing Reader
=============================================

Universal XBRL filing reader for fact_authority engine.

Phase 1 Components (Discovery and Access):
    - FilingProfile: Data structure for filing metadata
    - FileTypeClassifier: Intelligent file classification
    - MarketStructureDetector: Market-specific structure detection
    - FilingDiscoverer: Deep recursive file discovery
    - FilingValidator: Completeness and accessibility validation
    - FilingCacheManager: Profile caching for fast access

Phase 2 Batch 1 Components (Core Parsers):
    - ExtensionSchemaParser: Parse company extension XSD schemas
    - LinkbaseReader: Parse all four linkbase types
    - ContextExtractor: Extract contexts and units from instances
    - FactExtractor: Extract facts from instances
    - InstanceParser: Main coordinator for instance parsing

Phase 2 Batch 2 Components (Integration Layer):
    - ConceptResolver: Resolve concepts between extension and standard taxonomies
    - FilingLoader: Coordinate complete filing loading (Phase 1 + Phase 2)
    - FilingReader: Main API entry point for fact_authority engine

Works universally across SEC, FCA, and ESMA markets without hardcoded logic.

Version: 1.0.0-phase2-complete
"""

# Phase 1: Discovery and Access
from engines.fact_authority.filings_reader.filing_profile import FilingProfile
from engines.fact_authority.filings_reader.file_type_classifier import FileTypeClassifier
from engines.fact_authority.filings_reader.market_structure_detector import MarketStructureDetector
from engines.fact_authority.filings_reader.filing_discoverer import FilingDiscoverer
from engines.fact_authority.filings_reader.filing_validator import FilingValidator
from engines.fact_authority.filings_reader.filing_cache_manager import FilingCacheManager

# Phase 2 Batch 1: Core Parsers
from engines.fact_authority.filings_reader.extension_schema_parser import ExtensionSchemaParser
from engines.fact_authority.filings_reader.linkbase_reader import LinkbaseReader
from engines.fact_authority.filings_reader.context_extractor import ContextExtractor
from engines.fact_authority.filings_reader.fact_extractor import FactExtractor
from engines.fact_authority.filings_reader.instance_parser import InstanceParser

# Phase 2 Batch 2: Integration Layer
from engines.fact_authority.filings_reader.concept_resolver import ConceptResolver
from engines.fact_authority.filings_reader.filing_loader import FilingLoader
from engines.fact_authority.filings_reader.filing_reader import FilingReader


__version__ = '1.0.0-phase2-complete'

__all__ = [
    # Phase 1
    'FilingProfile',
    'FileTypeClassifier',
    'MarketStructureDetector',
    'FilingDiscoverer',
    'FilingValidator',
    'FilingCacheManager',
    # Phase 2 Batch 1
    'ExtensionSchemaParser',
    'LinkbaseReader',
    'ContextExtractor',
    'FactExtractor',
    'InstanceParser',
    # Phase 2 Batch 2
    'ConceptResolver',
    'FilingLoader',
    'FilingReader',
]