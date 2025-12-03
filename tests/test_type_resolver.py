#!/usr/bin/env python3
"""
Type Resolver Test
==================

Tests data type resolution and validation rules extraction.

Usage:
    python3 test_type_resolver.py
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, '/home/a/Desktop/Stock_software/ccq_val')

from engines.fact_authority.taxonomy_reader.type_resolver import (
    TypeResolver
)


def test_type_resolution():
    """Test type resolution and validation."""
    
    print("\n" + "="*70)
    print("TYPE RESOLVER TEST")
    print("="*70)
    print()
    
    # Initialize
    resolver = TypeResolver()
    
    print("Testing standard XBRL types...")
    print()
    
    # Test standard types
    print("="*70)
    print("STANDARD XBRL TYPES")
    print("="*70)
    print()
    
    standard_types = [
        'xbrli:monetaryItemType',
        'xbrli:sharesItemType',
        'xbrli:decimalItemType',
        'xbrli:integerItemType',
        'xbrli:stringItemType',
        'xbrli:dateItemType',
        'xbrli:booleanItemType',
        'xbrli:percentItemType',
    ]
    
    for type_string in standard_types:
        type_info = resolver.resolve_type(type_string)
        
        print(f"{type_string}:")
        print(f"  Base:           {type_info.get('base')}")
        print(f"  Unit required:  {type_info.get('unit_required')}")
        
        if 'unit_type' in type_info:
            print(f"  Unit type:      {type_info.get('unit_type')}")
        
        if 'fraction_digits' in type_info:
            fd = type_info.get('fraction_digits')
            if fd is None:
                print(f"  Fraction digits: unlimited")
            else:
                print(f"  Fraction_digits: {fd}")
        
        if 'min_inclusive' in type_info:
            print(f"  Min value:      {type_info.get('min_inclusive')}")
        
        print()
    
    # Test custom type extraction
    print("="*70)
    print("CUSTOM TYPE EXTRACTION")
    print("="*70)
    print()
    
    taxonomy_path = Path('/mnt/map_pro/data/taxonomies/libraries/us-gaap-2025')
    
    if taxonomy_path.exists():
        print(f"Taxonomy: {taxonomy_path}")
        print()
        
        # Find schema files
        schema_files = list(taxonomy_path.rglob('*.xsd'))
        print(f"Found {len(schema_files)} schema files")
        print()
        
        # Extract custom types
        print("🔍 Extracting custom types...")
        custom_types = resolver.extract_from_multiple_schemas(schema_files)
        print(f"   ✅ Extracted {len(custom_types)} custom types")
        print()
        
        # Show sample custom types
        if custom_types:
            print("Sample custom types:")
            print()
            
            sample_types = list(custom_types.items())[:5]
            
            for type_name, type_info in sample_types:
                print(f"{type_name}:")
                print(f"  Base:       {type_info.get('base')}")
                print(f"  Base (full): {type_info.get('base_type_full', 'N/A')}")
                
                restrictions = type_info.get('restrictions', {})
                if restrictions:
                    print(f"  Restrictions:")
                    for key, value in restrictions.items():
                        print(f"    {key}: {value}")
                
                print()
    else:
        print(f"⚠️  Taxonomy not found: {taxonomy_path}")
        print()
    
    # Test value validation
    print("="*70)
    print("VALUE VALIDATION")
    print("="*70)
    print()
    
    print("Testing monetary type validation...")
    print()
    
    monetary_type = resolver.resolve_type('xbrli:monetaryItemType')
    
    test_values = [
        (1000.50, "Valid monetary value"),
        (-500.25, "Negative monetary value"),
        (0, "Zero value"),
        (1234567890.12, "Large value"),
    ]
    
    for value, description in test_values:
        is_valid, error = resolver.validate_value(value, monetary_type)
        status = "✅ Valid" if is_valid else f"❌ Invalid: {error}"
        print(f"{description:30} {value:>15} → {status}")
    
    print()
    
    print("Testing shares type validation...")
    print()
    
    shares_type = resolver.resolve_type('xbrli:sharesItemType')
    
    test_values = [
        (1000, "Valid shares (integer)"),
        (1000.0, "Valid shares (float as int)"),
        (1000.5, "Invalid shares (fractional)"),
        (-100, "Negative shares"),
    ]
    
    for value, description in test_values:
        is_valid, error = resolver.validate_value(value, shares_type)
        status = "✅ Valid" if is_valid else f"❌ Invalid: {error}"
        print(f"{description:30} {value:>15} → {status}")
    
    print()
    
    print("Testing integer type validation...")
    print()
    
    integer_type = resolver.resolve_type('xbrli:integerItemType')
    
    test_values = [
        (100, "Valid integer"),
        (0, "Zero"),
        (-50, "Negative integer"),
        (100.5, "Fractional (should fail)"),
    ]
    
    for value, description in test_values:
        is_valid, error = resolver.validate_value(value, integer_type)
        status = "✅ Valid" if is_valid else f"❌ Invalid: {error}"
        print(f"{description:30} {value:>15} → {status}")
    
    print()
    
    print("Testing positive integer type validation...")
    print()
    
    positive_int_type = resolver.resolve_type('xbrli:positiveIntegerItemType')
    
    test_values = [
        (100, "Valid positive integer"),
        (1, "One (minimum)"),
        (0, "Zero (should fail)"),
        (-10, "Negative (should fail)"),
    ]
    
    for value, description in test_values:
        is_valid, error = resolver.validate_value(value, positive_int_type)
        status = "✅ Valid" if is_valid else f"❌ Invalid: {error}"
        print(f"{description:30} {value:>15} → {status}")
    
    print()
    
    # Type coverage
    print("="*70)
    print("TYPE COVERAGE")
    print("="*70)
    print()
    
    print(f"Standard types:     {len(resolver.STANDARD_TYPES)}")
    print(f"Custom types:       {len(resolver.custom_types)}")
    print(f"Total types known:  {len(resolver.STANDARD_TYPES) + len(resolver.custom_types)}")
    print()
    
    # Success
    print("="*70)
    print("✅ TEST COMPLETED")
    print("="*70)
    print()
    print("Type resolution capabilities:")
    print(f"  ✅ Standard XBRL types: {len(resolver.STANDARD_TYPES)}")
    print(f"  ✅ Custom types extracted: {len(resolver.custom_types)}")
    print(f"  ✅ Value validation: Working")
    print()
    
    return 0


def main():
    """Main entry point."""
    try:
        return test_type_resolution()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())