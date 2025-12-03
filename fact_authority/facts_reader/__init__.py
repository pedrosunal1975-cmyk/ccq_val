# File: __init__.py
# Location: engines/fact_authority/facts_reader/__init__.py

"""
Facts Reader - Parsed Facts Loader for Fact Authority Engine
=============================================================

Lightweight loader for Map Pro parsed_facts.json files.

Components:
    - ParsedFactsLoader: Main loader using CCQPaths infrastructure
    - FactsValidator: Validates structure and content quality

This is a focused loader (not a full parsing engine) since the data
is already pre-processed JSON from Map Pro.

Key Features:
- Integrates with existing CCQPaths for file discovery
- Loads and validates parsed_facts.json
- Provides clean accessors (get_facts, get_metadata, etc.)
- No caching (JSON is ready to load)
- Detailed validation and error reporting

Usage:
    from core.data_paths import ccq_paths
    from engines.fact_authority.facts_reader import ParsedFactsLoader, FactsValidator
    
    # Load facts
    loader = ParsedFactsLoader(ccq_paths)
    facts_data = loader.load_by_filing_info('sec', 'Apple_Inc', '10-K', '20231231')
    
    # Validate
    validator = FactsValidator()
    validation = validator.validate(facts_data)
    
    # Access data
    facts = loader.get_facts(facts_data)
    company_info = loader.get_company_info(facts_data)

Version: 1.0.0
"""

from engines.fact_authority.facts_reader.parsed_facts_loader import ParsedFactsLoader
from engines.fact_authority.facts_reader.facts_validator import FactsValidator


__version__ = '1.0.0'

__all__ = [
    'ParsedFactsLoader',
    'FactsValidator',
]