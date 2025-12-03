# File: engines/fact_authority/__init__.py
# Path: engines/fact_authority/__init__.py

"""
Fact Authority Engine
=====================

Independent validation engine that reconciles mapper outputs against
taxonomy authority.

Architecture:
    TAXONOMY (via taxonomy_reader/)
            |
      SOURCE OF TRUTH
            |
    +-------+-------+
    |               |
Map Pro           CCQ
    |               |
Compare to    Compare to
 TAXONOMY      TAXONOMY

Main Components:
    - fact_authority.py: Main orchestrator
    - input/: Statement loading and CLI
    - process/: Reconciliation and analysis
    - output/: Report generation and file writing
    
    - taxonomy_reader/: Parse XBRL taxonomies
    - filings_reader/: Parse XBRL filings
    - facts_reader/: Load parsed facts

Usage:
    from engines.fact_authority import FactAuthority
    from core.data_paths import CCQPaths
    
    ccq_paths = CCQPaths.from_config(config)
    fact_authority = FactAuthority(ccq_paths)
    
    result = fact_authority.validate_filing(
        market='sec',
        entity_name='Albertsons_Companies__Inc_',
        filing_type='10-K',
        filing_date='2025-04-21'
    )
"""

# Main orchestrator
from engines.fact_authority.fact_authority import FactAuthority

# Sub-engines (already exist)
from engines.fact_authority.taxonomy_reader import TaxonomyReader
from engines.fact_authority.filings_reader import FilingReader
from engines.fact_authority.facts_reader import ParsedFactsLoader

__version__ = '2.0.0'

__all__ = [
    'FactAuthority',
    'TaxonomyReader',
    'FilingReader',
    'ParsedFactsLoader',
]