#!/usr/bin/env python3
"""Find elements that actually have periodType."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from engines.fact_authority.taxonomy_reader.taxonomy_reader import TaxonomyReader
from core.config_loader import ConfigLoader
from core.data_paths import CCQPaths

config = ConfigLoader()
ccq_paths = CCQPaths(
    data_root=config.get('data_root'),
    input_path=config.get('input_path'),
    output_path=config.get('output_path'),
    taxonomy_path=config.get('taxonomy_path'),
    parsed_facts_path=config.get('parsed_facts_path'),
    mapper_xbrl_path=config.get('mapper_xbrl_path'),
    mapper_output_path=config.get('mapper_output_path'),
    unified_output_path=config.get('unified_output_path'),
    taxonomy_cache_path=config.get('taxonomy_cache_path'),
    filings_cache_path=config.get('filings_cache_path')
)

taxonomy_reader = TaxonomyReader()
taxonomy_paths = ccq_paths.get_taxonomy_paths_for_filing(market='sec', taxonomy_name='us-gaap')
taxonomy_profile = taxonomy_reader.read_taxonomy(taxonomy_paths)

print("="*80)
print("SEARCHING FOR ELEMENTS WITH periodType")
print("="*80)

elements = taxonomy_profile.elements
financial_concepts = []

for concept_qname, props in elements.items():
    period_type = props.get('periodType')
    if period_type and period_type.lower() in ['instant', 'duration']:
        financial_concepts.append((concept_qname, props))
        if len(financial_concepts) <= 10:
            print(f"\n{concept_qname}:")
            print(f"  periodType: {props.get('periodType')}")
            print(f"  balance: {props.get('balance')}")
            print(f"  abstract: {props.get('abstract')}")
            print(f"  type: {props.get('type')}")

print(f"\n{'='*80}")
print(f"RESULTS:")
print(f"  Total elements: {len(elements)}")
print(f"  With periodType: {len(financial_concepts)}")
print(f"  Instant: {sum(1 for c, p in financial_concepts if p.get('periodType', '').lower() == 'instant')}")
print(f"  Duration: {sum(1 for c, p in financial_concepts if p.get('periodType', '').lower() == 'duration')}")
print(f"={'='*80}")