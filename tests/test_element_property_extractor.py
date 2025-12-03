#!/usr/bin/env python3
"""
Element Property Extractor Test
================================

Tests element property extraction from XBRL schema files.

Usage:
    python3 test_element_property_extractor.py
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, '/home/a/Desktop/Stock_software/ccq_val')

from engines.fact_authority.taxonomy_reader.element_property_extractor import (
    ElementPropertyExtractor
)


def test_single_taxonomy():
    """Test extraction from US-GAAP 2025."""
    
    print("\n" + "="*70)
    print("ELEMENT PROPERTY EXTRACTOR TEST")
    print("="*70)
    print()
    
    # Initialize
    extractor = ElementPropertyExtractor()
    
    # US-GAAP 2025 taxonomy
    taxonomy_path = Path('/mnt/map_pro/data/taxonomies/libraries/us-gaap-2025')
    
    if not taxonomy_path.exists():
        print(f"❌ Taxonomy not found: {taxonomy_path}")
        return 1
    
    print(f"Taxonomy: {taxonomy_path}")
    print()
    
    # Find all schema files
    print("🔍 Finding schema files...")
    schema_files = list(taxonomy_path.rglob('*.xsd'))
    print(f"   Found {len(schema_files)} schema files")
    print()
    
    # Extract from all schemas
    print("📖 Extracting element properties...")
    elements = extractor.extract_from_multiple_schemas(schema_files)
    print(f"   ✅ Extracted {len(elements)} elements")
    print()
    
    # Show statistics
    print("="*70)
    print("STATISTICS")
    print("="*70)
    print()
    
    stats = extractor.get_statistics(elements)
    
    print(f"Total elements:        {stats['total']}")
    print(f"  Abstract:            {stats['abstract']}")
    print(f"  Concrete:            {stats['concrete']}")
    print()
    print(f"Period types:")
    print(f"  Instant:             {stats['instant']}")
    print(f"  Duration:            {stats['duration']}")
    print()
    print(f"Base types:")
    print(f"  Monetary:            {stats['monetary']}")
    print(f"  Shares:              {stats['shares']}")
    print(f"  Numeric:             {stats['numeric']}")
    print(f"  Text:                {stats['text']}")
    print()
    print(f"Balance types:")
    print(f"  Debit:               {stats['debit_balance']}")
    print(f"  Credit:              {stats['credit_balance']}")
    print()
    
    # Show sample elements
    print("="*70)
    print("SAMPLE ELEMENTS")
    print("="*70)
    print()
    
    # Find some well-known concepts
    sample_concepts = [
        'us-gaap:Cash',
        'us-gaap:Assets',
        'us-gaap:Liabilities',
        'us-gaap:StockholdersEquity',
        'us-gaap:Revenues',
        'us-gaap:NetIncomeLoss',
    ]
    
    for concept in sample_concepts:
        if concept in elements:
            props = elements[concept]
            print(f"{concept}:")
            print(f"  Type:         {props.get('type', 'N/A')}")
            print(f"  Base type:    {props.get('base_type', 'N/A')}")
            print(f"  Period:       {props.get('period_type', 'N/A')}")
            print(f"  Balance:      {props.get('balance', 'N/A')}")
            print(f"  Abstract:     {props.get('abstract', False)}")
            print()
        else:
            print(f"{concept}: NOT FOUND")
            print()
    
    # Test filters
    print("="*70)
    print("FILTER TESTS")
    print("="*70)
    print()
    
    # Filter monetary elements
    monetary = extractor.filter_by_type(elements, 'monetary')
    print(f"Monetary elements:     {len(monetary)}")
    
    # Filter abstract elements
    abstract = extractor.filter_abstract(elements, abstract=True)
    print(f"Abstract elements:     {len(abstract)}")
    
    # Filter concrete elements
    concrete = extractor.filter_abstract(elements, abstract=False)
    print(f"Concrete elements:     {len(concrete)}")
    
    # Filter instant elements
    instant = extractor.filter_by_period(elements, 'instant')
    print(f"Instant elements:      {len(instant)}")
    
    # Filter duration elements
    duration = extractor.filter_by_period(elements, 'duration')
    print(f"Duration elements:     {len(duration)}")
    
    print()
    
    # Show some abstract concepts
    print("="*70)
    print("SAMPLE ABSTRACT CONCEPTS (Headers)")
    print("="*70)
    print()
    
    abstract_samples = list(abstract.keys())[:5]
    for concept in abstract_samples:
        props = abstract[concept]
        print(f"{concept}:")
        print(f"  Abstract:     {props.get('abstract')}")
        print(f"  Type:         {props.get('type', 'N/A')}")
        print()
    
    # Validation checks
    print("="*70)
    print("VALIDATION CHECKS")
    print("="*70)
    print()
    
    # Check 1: All monetary should have balance
    monetary_without_balance = [
        qname for qname, props in monetary.items()
        if not props.get('balance')
    ]
    
    if monetary_without_balance:
        print(f"⚠️  Found {len(monetary_without_balance)} monetary concepts without balance")
        print(f"   Examples: {monetary_without_balance[:3]}")
    else:
        print(f"✅ All monetary concepts have balance type")
    
    print()
    
    # Check 2: All concrete should have period_type
    concrete_without_period = [
        qname for qname, props in concrete.items()
        if not props.get('period_type')
    ]
    
    if concrete_without_period:
        print(f"⚠️  Found {len(concrete_without_period)} concrete concepts without period_type")
        print(f"   Examples: {concrete_without_period[:3]}")
    else:
        print(f"✅ All concrete concepts have period_type")
    
    print()
    
    # Success
    print("="*70)
    print("✅ TEST COMPLETED")
    print("="*70)
    print()
    print(f"Successfully extracted {len(elements)} element properties")
    print(f"  Monetary concepts: {len(monetary)}")
    print(f"  Abstract concepts: {len(abstract)}")
    print(f"  Instant concepts: {len(instant)}")
    print(f"  Duration concepts: {len(duration)}")
    print()
    
    return 0


def main():
    """Main entry point."""
    try:
        return test_single_taxonomy()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())