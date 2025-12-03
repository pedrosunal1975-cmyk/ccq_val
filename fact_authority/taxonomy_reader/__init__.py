"""
Taxonomy Reader Sub-Engine
===========================

Universal taxonomy understanding engine for fact_authority.

This sub-engine reads and understands ANY XBRL taxonomy by analyzing
its self-documenting files (catalogs, schemas, linkbases). It's the
"learn the language before reading the book" component.

Core Philosophy:
    Read the taxonomy's structure FIRST, then use that knowledge
    to process company filings. Market-agnostic and taxonomy-agnostic.

Components:
    TaxonomyProfile: Data structure for taxonomy understanding
    CatalogParser: Parses catalog.xml namespace mappings
    SchemaAnalyzer: Analyzes .xsd schema files
    RoleExtractor: Extracts statement role definitions
    TaxonomyReader: Main orchestrator
    CacheManager: Optional performance caching
    
    Type Resolution Components:
    TypeResolver: Main type resolution interface
    validate_value: Standalone value validation function
    classify_base_type: Standalone type classification function

Usage:
    from engines.fact_authority.taxonomy_reader import TaxonomyReader
    
    reader = TaxonomyReader()
    profile = reader.read_taxonomy(Path('/taxonomies/libraries/us-gaap-2025'))
    
    # Now we understand this taxonomy
    print(f"Taxonomy: {profile.metadata['name']}")
    print(f"Statement types: {reader.get_statement_types(profile)}")
    print(f"Roles: {len(profile.roles)}")
    
    # With caching (optional)
    from engines.fact_authority.taxonomy_reader import CacheManager
    from core.data_paths import ccq_paths
    
    cache_mgr = CacheManager(ccq_paths.taxonomy_cache)
    cache_file = cache_mgr.get_cache_path('us-gaap', '2025')
    
    if cache_mgr.is_cache_valid(cache_file, taxonomy_path):
        profile = cache_mgr.load_profile(cache_file)
    else:
        profile = reader.read_taxonomy(taxonomy_path)
        cache_mgr.save_profile(profile, cache_file)
"""

from engines.fact_authority.taxonomy_reader.taxonomy_profile import (
    TaxonomyProfile
)
from engines.fact_authority.taxonomy_reader.catalog_parser import (
    CatalogParser
)
from engines.fact_authority.taxonomy_reader.schema_analyzer import (
    SchemaAnalyzer
)
from engines.fact_authority.taxonomy_reader.role_extractor import (
    RoleExtractor
)
from engines.fact_authority.taxonomy_reader.element_property_extractor import (
    ElementPropertyExtractor
)
from engines.fact_authority.taxonomy_reader.calculation_parser import (
    CalculationParser
)
from engines.fact_authority.taxonomy_reader.definition_parser import (
    DefinitionParser
)
from engines.fact_authority.taxonomy_reader.label_parser import (
    LabelParser
)
from engines.fact_authority.taxonomy_reader.type_resolver import (
    TypeResolver
)
from engines.fact_authority.taxonomy_reader.type_validator import (
    validate_value
)
from engines.fact_authority.taxonomy_reader.type_classifier import (
    classify_base_type
)
from engines.fact_authority.taxonomy_reader.taxonomy_validator import (
    TaxonomyValidator
)
from engines.fact_authority.taxonomy_reader.taxonomy_reader import (
    TaxonomyReader
)
from engines.fact_authority.taxonomy_reader.cache_manager import (
    CacheManager
)


__all__ = [
    'TaxonomyProfile',
    'CatalogParser',
    'SchemaAnalyzer',
    'RoleExtractor',
    'ElementPropertyExtractor',
    'CalculationParser',
    'DefinitionParser',
    'LabelParser',
    'TypeResolver',
    'validate_value',
    'classify_base_type',
    'TaxonomyValidator',
    'TaxonomyReader',
    'CacheManager',
]