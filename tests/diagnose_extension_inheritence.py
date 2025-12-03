#!/usr/bin/env python3
"""
Diagnostic: Why are extension concepts not mapping to base concepts?
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from engines.fact_authority.taxonomy_reader.taxonomy_reader import TaxonomyReader
from engines.fact_authority.filings_reader.filing_reader import FilingReader
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

print("="*80)
print("EXTENSION INHERITANCE DIAGNOSTIC")
print("="*80)

# Load XBRL filing to get extension concepts
print("\n1. Loading XBRL filing...")
filing_file = ccq_paths.find_xbrl_filing('sec', 'PLUG_POWER_INC', '10-K', '2025-03-03')
if not filing_file:
    print("ERROR: Filing not found!")
    sys.exit(1)

filing_dir = filing_file.parent
filing_reader = FilingReader(ccq_paths)
filing_data = filing_reader.read_filing(filing_dir)

extension_schema = filing_data.get('extension_schema', {})
elements = extension_schema.get('elements', [])

print(f"   Found {len(elements)} extension elements")

# Show first 5 extension concepts with their substitutionGroup
print("\n2. Sample extension concepts (first 5):")
count = 0
for elem in elements:
    if count >= 5:
        break
    name = elem.get('name', 'N/A')
    sub_group = elem.get('substitutionGroup', 'N/A')
    period_type = elem.get('periodType', 'N/A')
    
    if sub_group and sub_group != 'N/A':
        print(f"\n   {name}")
        print(f"      substitutionGroup: {sub_group}")
        print(f"      periodType: {period_type}")
        count += 1

# Load taxonomy
print("\n3. Loading taxonomy...")
taxonomy_paths = ccq_paths.get_taxonomy_paths_for_filing(market='sec', taxonomy_name='us-gaap')
taxonomy_reader = TaxonomyReader()
taxonomy_profile = taxonomy_reader.read_taxonomy(taxonomy_paths)

# Check if substitutionGroups exist in taxonomy
print("\n4. Checking if substitutionGroups exist in taxonomy elements...")
taxonomy_dict = taxonomy_profile.to_dict()
taxonomy_elements = taxonomy_dict.get('elements', {})

print(f"   Taxonomy has {len(taxonomy_elements)} elements")

# Sample taxonomy element names
print("\n5. Sample taxonomy element names (first 10):")
for i, elem_name in enumerate(list(taxonomy_elements.keys())[:10]):
    print(f"      {elem_name}")

# Check if any extension substitutionGroups match taxonomy elements
print("\n6. Checking matches...")
matches = 0
non_matches = 0
sample_non_matches = []

for elem in elements[:100]:  # Check first 100
    sub_group = elem.get('substitutionGroup')
    if sub_group:
        if sub_group in taxonomy_elements:
            matches += 1
        else:
            non_matches += 1
            if len(sample_non_matches) < 5:
                sample_non_matches.append({
                    'name': elem.get('name'),
                    'substitutionGroup': sub_group
                })

print(f"   Matches: {matches}")
print(f"   Non-matches: {non_matches}")

if sample_non_matches:
    print("\n7. Sample non-matching substitutionGroups:")
    for item in sample_non_matches:
        print(f"\n   Extension: {item['name']}")
        print(f"      Looking for: {item['substitutionGroup']}")
        
        # Try to find similar names
        sub_parts = item['substitutionGroup'].split(':')
        if len(sub_parts) == 2:
            search_name = sub_parts[1]
            # Look for this name in taxonomy
            similar = [k for k in list(taxonomy_elements.keys())[:100] if search_name.lower() in k.lower()]
            if similar:
                print(f"      Similar in taxonomy: {similar[:3]}")

print(f"\n{'='*80}")
print("DIAGNOSTIC COMPLETE")
print(f"{'='*80}")