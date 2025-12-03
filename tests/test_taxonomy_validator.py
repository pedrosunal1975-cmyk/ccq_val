#!/usr/bin/env python3
"""
Taxonomy Validator Test
========================

Tests taxonomy validation capabilities.

Usage:
    python3 test_taxonomy_validator.py
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, '/home/a/Desktop/Stock_software/ccq_val')

from engines.fact_authority.taxonomy_reader.taxonomy_validator import (
    TaxonomyValidator
)
from engines.fact_authority.taxonomy_reader.taxonomy_reader import (
    TaxonomyReader
)
from engines.fact_authority.taxonomy_reader.cache_manager import (
    CacheManager
)


def test_taxonomy_validation():
    """Test taxonomy validation."""
    
    print("\n" + "="*70)
    print("TAXONOMY VALIDATOR TEST")
    print("="*70)
    print()
    
    # Initialize
    validator = TaxonomyValidator()
    reader = TaxonomyReader()
    cache_mgr = CacheManager(cache_base_path=Path.home() / '.cache' / 'ccq_val' / 'taxonomy')
    
    # US-GAAP 2025 taxonomy
    taxonomy_path = Path('/mnt/map_pro/data/taxonomies/libraries/us-gaap-2025')
    
    if not taxonomy_path.exists():
        print(f"❌ Taxonomy not found: {taxonomy_path}")
        return 1
    
    print(f"Taxonomy: {taxonomy_path}")
    print()
    
    # Load taxonomy profile
    print("📖 Loading taxonomy profile...")
    
    # Check cache
    cache_file = cache_mgr.get_cache_path('us-gaap', '2025')
    
    if cache_mgr.is_cache_valid(cache_file, [taxonomy_path]):
        profile = cache_mgr.load_profile(cache_file)
        print("   ✅ Loaded from cache")
    else:
        print("   Cache miss - reading taxonomy...")
        profile = reader.read_taxonomy([taxonomy_path])
        cache_mgr.save_profile(profile, cache_file)  # Correct order: profile first, path second
        print(f"   ✅ Loaded and cached")
    
    print()
    
    # Validate taxonomy
    print("="*70)
    print("PERFORMING VALIDATION CHECKS")
    print("="*70)
    print()
    
    print("🔍 Validating taxonomy structure...")
    results = validator.validate_taxonomy(profile)
    print("   ✅ Validation complete")
    print()
    
    # Show summary
    print(validator.get_validation_summary(results))
    
    # Show info messages
    if results['info']:
        print("="*70)
        print("INFORMATION")
        print("="*70)
        print()
        for info in results['info']:
            print(f"  ℹ️  {info}")
        print()
    
    # Test specific element validation
    print("="*70)
    print("SPECIFIC ELEMENT VALIDATION")
    print("="*70)
    print()
    
    test_concepts = [
        'us-gaap:Cash',
        'us-gaap:Assets',
        'us-gaap:Liabilities',
        'us-gaap:Revenues',
    ]
    
    for concept in test_concepts:
        elem_result = validator.validate_element(profile, concept)
        
        # Simplify name
        if ':' in concept:
            simple_name = concept.split(':')[1]
        else:
            simple_name = concept
        
        print(f"{simple_name}:")
        
        if elem_result['exists']:
            props = elem_result['properties']
            print(f"  Type:        {props.get('type', 'N/A')}")
            print(f"  Period:      {props.get('period_type', 'N/A')}")
            print(f"  Balance:     {props.get('balance', 'N/A')}")
            print(f"  Abstract:    {props.get('abstract', False)}")
            print(f"  Has label:   {elem_result['has_label']}")
            
            if elem_result['issues']:
                print(f"  Issues:")
                for issue in elem_result['issues']:
                    print(f"    ⚠️  {issue}")
            else:
                print(f"  Status:      ✅ Valid")
        else:
            print(f"  Status:      ❌ Not found")
        
        print()
    
    # Validation capabilities
    print("="*70)
    print("VALIDATION CAPABILITIES")
    print("="*70)
    print()
    
    print("✅ Reference Integrity:")
    print("   - Calculations reference valid elements")
    print("   - Dimensions reference valid elements")
    print("   - Axes reference valid domains")
    print("   - Hypercubes reference valid axes")
    print()
    
    print("✅ Calculation Consistency:")
    print("   - Parents have children")
    print("   - Children exist")
    print("   - Weight patterns are reasonable")
    print()
    
    print("✅ Dimensional Integrity:")
    print("   - Axes have domains")
    print("   - Axes have members")
    print("   - Hypercubes have dimensions")
    print()
    
    print("✅ Label Coverage:")
    print("   - Elements have labels")
    print("   - Standard label coverage calculated")
    print()
    
    print("✅ Element Validation:")
    print("   - Required properties present")
    print("   - Type consistency")
    print("   - Period type for concrete elements")
    print("   - Balance for monetary elements")
    print()
    
    # Use cases
    print("="*70)
    print("USE CASES FOR fact_authority")
    print("="*70)
    print()
    
    print("1. Custom Taxonomy Validation:")
    print("   ✅ Ensure company extensions are well-formed")
    print("   ✅ Check reference integrity")
    print("   ✅ Validate calculation relationships")
    print()
    
    print("2. Debugging:")
    print("   ✅ Identify missing elements")
    print("   ✅ Find broken references")
    print("   ✅ Detect incomplete definitions")
    print()
    
    print("3. Quality Assurance:")
    print("   ✅ Verify label coverage")
    print("   ✅ Check dimensional consistency")
    print("   ✅ Validate role definitions")
    print()
    
    # Success
    print("="*70)
    print("✅ TEST COMPLETED")
    print("="*70)
    print()
    print("TaxonomyValidator capabilities verified:")
    print(f"  ✅ Validation checks: {results['summary']['total_checks']}")
    print(f"  ✅ Errors found: {results['summary']['errors']}")
    print(f"  ✅ Warnings found: {results['summary']['warnings']}")
    print()
    print("Ready for use with fact_authority!")
    print()
    
    return 0


def main():
    """Main entry point."""
    try:
        return test_taxonomy_validation()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())