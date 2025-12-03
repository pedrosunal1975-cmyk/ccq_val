# Taxonomy Reader Sub-Engine

## Overview

The **Taxonomy Reader** is a universal taxonomy understanding engine that reads and comprehends ANY XBRL taxonomy by analyzing its self-documenting files.

### Core Philosophy

> "You need to know the English language before reading any book written in English."

Just as you must understand grammar rules before reading a book, the system must understand a taxonomy's structure before processing filings that use it.

## Architecture

```
taxonomy_reader/
├── taxonomy_profile.py       # Data structure for taxonomy understanding
├── catalog_parser.py          # Parse catalog.xml namespace mappings
├── schema_analyzer.py         # Analyze .xsd schema files
├── role_extractor.py          # Extract statement role definitions
├── taxonomy_reader.py         # Main orchestrator
└── cache_manager.py           # Optional performance caching
```

## Key Concepts

### 1. Self-Documentation

XBRL taxonomies are self-documenting:

- **catalog.xml**: Maps namespace URIs to file locations
- **Schema files (.xsd)**: Define structure, roles, and linkbase references
- **Linkbase files (.xml)**: Contain hierarchies and relationships

### 2. TaxonomyProfile

Complete understanding of a taxonomy:

```python
TaxonomyProfile {
    'metadata': {
        'name': 'us-gaap',
        'version': '2025',
        'namespace': 'http://fasb.org/us-gaap/2025'
    },
    'structure': {
        'schema_files': [...],
        'linkbases': {
            'presentation': [...],
            'calculation': [...]
        }
    },
    'roles': {
        'http://fasb.org/.../StatementOfFinancialPosition': {
            'type': 'balance_sheet',
            'definition': 'Statement of Financial Position'
        }
    }
}
```

### 3. Market Agnostic

Works with ANY taxonomy:
- SEC (US-GAAP, DEI)
- ESMA (IFRS, ESEF)
- FCA (UK-GAAP, IFRS)
- Custom company extensions

## Usage

### Basic Usage

```python
from engines.fact_authority.taxonomy_reader import TaxonomyReader
from pathlib import Path

# Initialize reader
reader = TaxonomyReader()

# Read and understand a taxonomy
taxonomy_path = Path('/mnt/map_pro/data/taxonomies/libraries/us-gaap-2025')
profile = reader.read_taxonomy(taxonomy_path)

# Access taxonomy understanding
print(f"Taxonomy: {profile.metadata['name']}")
print(f"Version: {profile.metadata['version']}")
print(f"Statement roles: {len(profile.roles)}")

# Get statement types
statement_types = reader.get_statement_types(profile)
print(f"Statements: {statement_types}")
# Output: ['balance_sheet', 'income_statement', 'cash_flow', 'equity']

# Get roles for a specific statement
bs_roles = reader.get_roles_for_statement(profile, 'balance_sheet')
print(f"Balance sheet roles: {len(bs_roles)}")
```

### With Caching (Recommended)

```python
from engines.fact_authority.taxonomy_reader import TaxonomyReader, CacheManager
from core.data_paths import ccq_paths
from pathlib import Path

# Initialize
reader = TaxonomyReader()
cache_mgr = CacheManager(ccq_paths.taxonomy_cache)

taxonomy_path = Path('/mnt/map_pro/data/taxonomies/libraries/us-gaap-2025')
cache_file = cache_mgr.get_cache_path('us-gaap', '2025')

# Check cache first
if cache_mgr.is_cache_valid(cache_file, taxonomy_path):
    # Use cached profile (fast)
    profile = cache_mgr.load_profile(cache_file)
    print("Loaded from cache")
else:
    # Read from taxonomy files (slower first time)
    profile = reader.read_taxonomy(taxonomy_path)
    cache_mgr.save_profile(profile, cache_file)
    print("Generated new profile")

# Use profile
print(f"Roles: {len(profile.roles)}")
```

### Integration with fact_authority

```python
from engines.fact_authority.taxonomy_reader import TaxonomyReader
from engines.fact_authority import TaxonomyInterface

# Step 1: Understand the taxonomy
reader = TaxonomyReader()
profile = reader.read_taxonomy(taxonomy_path)

# Step 2: Use that understanding
interface = TaxonomyInterface()
hierarchy = interface.load_taxonomy_hierarchy(
    tuple([taxonomy_path])
)

# Step 3: Query with context
for role_uri, role_info in profile.roles.items():
    if role_info['type'] == 'balance_sheet':
        # Now we know this role is for balance sheet
        authority = interface.get_concept_authority('us-gaap:Cash', hierarchy)
```

## Components

### TaxonomyProfile

Data structure storing complete taxonomy understanding.

**Methods:**
- `to_json(filepath)` - Save to JSON
- `from_json(filepath)` - Load from JSON
- `get_statement_roles()` - Get role URI → statement type mapping
- `get_presentation_linkbases()` - Get all presentation files

### CatalogParser

Parses `catalog.xml` files for namespace resolution.

**Methods:**
- `parse(catalog_path)` - Parse catalog, return mappings
- `find_catalog_file(taxonomy_path)` - Locate catalog.xml
- `resolve_uri(uri, mappings, base_path)` - Resolve URI to file

### SchemaAnalyzer

Analyzes `.xsd` schema files to extract structure.

**Methods:**
- `analyze(schema_path)` - Analyze single schema
- `analyze_multiple(schema_paths)` - Analyze multiple schemas
- `find_entry_point_schema(taxonomy_path)` - Find main schema

### RoleExtractor

Extracts `roleType` definitions from schemas.

**Methods:**
- `extract_from_file(schema_path)` - Extract roles from schema
- `extract_from_multiple_files(schema_paths)` - Extract from multiple
- `filter_presentation_roles(roles)` - Filter to presentation roles

### TaxonomyReader

Main orchestrator - uses all components.

**Methods:**
- `read_taxonomy(taxonomy_path)` - Read and understand taxonomy
- `get_statement_types(profile)` - Get all statement types
- `get_roles_for_statement(profile, type)` - Get roles for statement

### CacheManager

Optional caching for performance.

**Methods:**
- `is_cache_valid(cache_file, source_path)` - Check validity
- `load_profile(cache_file)` - Load cached profile
- `save_profile(profile, cache_file)` - Save to cache
- `clear_cache()` - Delete all cache
- `get_cache_info()` - Get cache statistics

## Cache Architecture

### Location

```
/mnt/map_pro/data/taxonomies/
├── libraries/           # PRISTINE (read-only, never touched)
│   ├── us-gaap-2025/
│   ├── us-gaap-2024/
│   └── ifrs-2024/
│
└── .cache/             # GENERATED (ephemeral, can delete anytime)
    ├── profiles/
    │   ├── us-gaap-2025.profile.json
    │   ├── us-gaap-2024.profile.json
    │   └── ifrs-2024.profile.json
    └── README.txt
```

### Cache Invalidation

Cache is invalid if:
1. Any `.xsd` file modified since cache created
2. `catalog.xml` modified
3. Format version mismatch

### Safety

- **NEVER** writes to `libraries/`
- Cache can be deleted anytime: `cache_mgr.clear_cache()`
- System regenerates as needed
- `.gitignore` excludes `.cache/`

## Performance

### Without Cache

```
Process 100 companies:
  Read taxonomy: 5 seconds × 100 = 500 seconds
  Total: ~8 minutes
```

### With Cache

```
First run:
  Read taxonomy: 5 seconds
  Save cache: 0.1 seconds
  
Subsequent runs (99 companies):
  Load cache: 0.1 seconds × 99 = 9.9 seconds
  
Total: 5s + 9.9s = ~15 seconds (33x faster!)
```

## File Sizes

Each file respects the **400-line limit**:

| File | Lines | Purpose |
|------|-------|---------|
| taxonomy_profile.py | 220 | Data structure |
| catalog_parser.py | 180 | Parse catalog.xml |
| schema_analyzer.py | 290 | Parse .xsd files |
| role_extractor.py | 200 | Extract roles |
| taxonomy_reader.py | 260 | Main orchestrator |
| cache_manager.py | 210 | Cache management |

**Total: ~1,360 lines** across 6 focused files.

## Testing

```python
# Test basic reading
reader = TaxonomyReader()
profile = reader.read_taxonomy(Path('/taxonomies/us-gaap-2025'))
assert profile.metadata['name'] == 'us-gaap'
assert len(profile.roles) > 0

# Test caching
cache_mgr = CacheManager(Path('/taxonomies/.cache'))
cache_file = cache_mgr.get_cache_path('us-gaap', '2025')
cache_mgr.save_profile(profile, cache_file)
assert cache_file.exists()

loaded = cache_mgr.load_profile(cache_file)
assert loaded.metadata == profile.metadata
```

## Design Principles

1. ✅ **Single Responsibility**: Each file has ONE job
2. ✅ **Market Agnostic**: Works with any taxonomy
3. ✅ **Taxonomy Agnostic**: Reads any taxonomy structure
4. ✅ **Optional Caching**: Works without cache
5. ✅ **Safe Operations**: Never touches `libraries/`
6. ✅ **Comprehensive Logging**: Clear progress tracking
7. ✅ **Type Hints**: Full type annotations
8. ✅ **Documentation**: Extensive docstrings

## Future Enhancements

### Phase 2: Advanced Features
- Dimension parsing (axes, domains, members)
- Calculation validation
- Label extraction (multiple languages)
- Reference linkbase parsing

### Phase 3: Intelligence
- Concept similarity detection
- Cross-taxonomy mapping
- Extension concept classification

## Integration Points

### Current Integration
- `TaxonomyFileDiscoverer` - Uses for file discovery
- `TaxonomyInterface` - Can use profiles for queries
- `fact_reconciler` - Can use role information

### Future Integration
- `StatementReconciler` - Use role knowledge
- `PresentationLinkbaseParser` - Use discovered files
- `ExtensionInheritanceTracer` - Use namespace info

## Maintenance

### Adding Support for New Linkbase Types

Edit `schema_analyzer.py`:

```python
LINKBASE_TYPES = {
    'presentationLinkbaseRef': 'presentation',
    'calculationLinkbaseRef': 'calculation',
    'newTypeLinkbaseRef': 'new_type',  # Add here
}
```

### Adding New Statement Keywords

Edit `role_extractor.py`:

```python
STATEMENT_KEYWORDS = {
    'balance': 'balance_sheet',
    'new statement': 'new_type',  # Add here
}
```

## Contact & Support

For questions or issues with the taxonomy_reader sub-engine:
- Check logs: `logger` statements throughout
- Inspect profiles: `profile.to_json(Path('/tmp/debug.json'))`
- Clear cache: `cache_mgr.clear_cache()` if issues suspected