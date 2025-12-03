#!/usr/bin/env python3
"""
Diagnostic script to understand taxonomy concept extraction failure.
Run this from ccq_val directory: python3 diagnose_taxonomy_extraction.py
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from engines.fact_authority.taxonomy_reader.taxonomy_reader import TaxonomyReader
from core.config_loader import ConfigLoader
from core.data_paths import CCQPaths
import json

def main():
    print("="*80)
    print("TAXONOMY CONCEPT EXTRACTION DIAGNOSTIC")
    print("="*80)
    
    # Load configuration
    print("\n1. Loading configuration...")
    config = ConfigLoader()
    
    # Initialize paths from config
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
    print("   ✓ Paths initialized")
    
    # Load taxonomy
    print("\n1. Loading taxonomy...")
    taxonomy_reader = TaxonomyReader()
    
    # Get us-gaap taxonomy path
    taxonomy_paths = ccq_paths.get_taxonomy_paths_for_filing(
        market='sec',
        taxonomy_name='us-gaap'
    )
    
    if not taxonomy_paths:
        print("ERROR: No taxonomy paths found!")
        return
    
    print(f"   Taxonomy path: {taxonomy_paths[0]}")
    
    # Load taxonomy
    taxonomy_profile = taxonomy_reader.read_taxonomy(taxonomy_paths)
    
    print(f"\n2. TaxonomyProfile Contents:")
    print(f"   Type: {type(taxonomy_profile)}")
    print(f"   Roles: {len(taxonomy_profile.roles)}")
    print(f"   Elements: {len(taxonomy_profile.elements)}")
    print(f"   Calculations: {len(taxonomy_profile.calculations)}")
    
    # Convert to dict
    taxonomy_dict = taxonomy_profile.to_dict()
    
    print(f"\n3. After to_dict():")
    print(f"   Type: {type(taxonomy_dict)}")
    print(f"   Keys: {list(taxonomy_dict.keys())}")
    print(f"   Roles: {len(taxonomy_dict.get('roles', {}))}")
    print(f"   Elements: {len(taxonomy_dict.get('elements', {}))}")
    print(f"   Calculations: {len(taxonomy_dict.get('calculations', {}))}")
    
    # Sample elements
    elements = taxonomy_dict.get('elements', {})
    if elements:
        print(f"\n4. Sample Elements (first 5):")
        for i, (concept, props) in enumerate(list(elements.items())[:5]):
            print(f"   {concept}:")
            print(f"      periodType: {props.get('periodType')}")
            print(f"      balance: {props.get('balance')}")
            print(f"      abstract: {props.get('abstract')}")
    
    # Sample roles
    roles = taxonomy_dict.get('roles', {})
    if roles:
        print(f"\n5. Sample Roles (first 5):")
        for i, (role_uri, role_info) in enumerate(list(roles.items())[:5]):
            print(f"   {role_uri[:80]}...")
            print(f"      definition: {role_info.get('definition', 'N/A')[:60]}")
    
    # Now test extraction logic
    print(f"\n6. Testing Element-Based Classification:")
    
    instant_count = 0
    duration_count = 0
    no_period_count = 0
    abstract_count = 0
    
    for concept, props in elements.items():
        if props.get('abstract'):
            abstract_count += 1
            continue
        
        period_type = props.get('periodType', '').lower()
        if period_type == 'instant':
            instant_count += 1
        elif period_type == 'duration':
            duration_count += 1
        else:
            no_period_count += 1
    
    print(f"   Instant concepts (balance_sheet): {instant_count}")
    print(f"   Duration concepts (income/cash): {duration_count}")
    print(f"   Abstract (skipped): {abstract_count}")
    print(f"   No period type: {no_period_count}")
    print(f"   EXPECTED TOTAL: {instant_count + duration_count}")
    
    # Test actual extraction
    print(f"\n7. Testing Actual _extract_taxonomy_concepts():")
    from engines.fact_authority.process.statement_reconciler import StatementReconciler
    
    reconciler = StatementReconciler(taxonomy_profile, ccq_paths)
    
    print(f"   Extracted concepts: {len(reconciler.taxonomy_concepts)}")
    
    if reconciler.taxonomy_concepts:
        print(f"\n   Sample extracted concepts (first 10):")
        for concept, stmt_type in list(reconciler.taxonomy_concepts.items())[:10]:
            print(f"      {concept} -> {stmt_type}")
    else:
        print("\n   ❌ NO CONCEPTS EXTRACTED!")
        print("\n   Debugging why:")
        
        # Check if taxonomy_data is accessible
        print(f"      Has taxonomy_data: {hasattr(reconciler, 'taxonomy_data')}")
        print(f"      taxonomy_data type: {type(reconciler.taxonomy_data)}")
        
        # Check if to_dict worked
        if hasattr(reconciler.taxonomy_data, 'to_dict'):
            test_dict = reconciler.taxonomy_data.to_dict()
            print(f"      to_dict() returns: {type(test_dict)}")
            print(f"      Keys in dict: {list(test_dict.keys())}")
            print(f"      Elements in dict: {len(test_dict.get('elements', {}))}")
    
    print("\n" + "="*80)
    print("DIAGNOSTIC COMPLETE")
    print("="*80)

if __name__ == '__main__':
    main()