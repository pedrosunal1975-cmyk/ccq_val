#!/usr/bin/env python3
"""
Label Parser Test
=================

Tests label extraction from XBRL label linkbases.

Usage:
    python3 test_label_parser.py
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, '/home/a/Desktop/Stock_software/ccq_val')

from engines.fact_authority.taxonomy_reader.label_parser import (
    LabelParser
)
from engines.fact_authority.taxonomy_file_discoverer import (
    TaxonomyFileDiscoverer
)


def test_label_parsing():
    """Test label parsing from US-GAAP 2025."""
    
    print("\n" + "="*70)
    print("LABEL PARSER TEST")
    print("="*70)
    print()
    
    # Initialize
    parser = LabelParser()
    discoverer = TaxonomyFileDiscoverer()
    
    # US-GAAP 2025 taxonomy
    taxonomy_path = Path('/mnt/map_pro/data/taxonomies/libraries/us-gaap-2025')
    
    if not taxonomy_path.exists():
        print(f"❌ Taxonomy not found: {taxonomy_path}")
        return 1
    
    print(f"Taxonomy: {taxonomy_path}")
    print()
    
    # Find label linkbases
    print("🔍 Finding label linkbases...")
    label_files = discoverer.find_label_linkbases([taxonomy_path])
    print(f"   Found {len(label_files)} label linkbases")
    print()
    
    # Parse all label linkbases
    print("📖 Parsing labels...")
    labels = parser.parse_multiple(label_files)
    print(f"   ✅ Parsed labels for {len(labels)} concepts")
    print()
    
    # Show statistics
    print("="*70)
    print("STATISTICS")
    print("="*70)
    print()
    
    stats = parser.get_statistics(labels)
    
    print(f"Total concepts:              {stats['total_concepts']}")
    print(f"Total labels:                {stats['total_labels']}")
    print(f"Unique languages:            {stats['unique_languages']}")
    print()
    print(f"Concepts with labels:")
    print(f"  Standard:                  {stats['concepts_with_standard']}")
    print(f"  Terse:                     {stats['concepts_with_terse']}")
    print(f"  Verbose:                   {stats['concepts_with_verbose']}")
    print(f"  Documentation:             {stats['concepts_with_documentation']}")
    print()
    
    # Show sample labels
    print("="*70)
    print("SAMPLE LABELS")
    print("="*70)
    print()
    
    # Well-known concepts
    sample_concepts = [
        'us-gaap:Cash',
        'us-gaap:Assets',
        'us-gaap:Liabilities',
        'us-gaap:StockholdersEquity',
        'us-gaap:Revenues',
        'us-gaap:NetIncomeLoss',
    ]
    
    for concept in sample_concepts:
        if concept in labels:
            concept_labels = labels[concept]
            
            print(f"{concept}:")
            
            # Show standard label
            standard = parser.get_label(labels, concept, 'standard', 'en-US')
            if standard:
                print(f"  Standard:      {standard}")
            
            # Show terse label
            terse = parser.get_label(labels, concept, 'terse', 'en-US')
            if terse:
                print(f"  Terse:         {terse}")
            
            # Show verbose label
            verbose = parser.get_label(labels, concept, 'verbose', 'en-US')
            if verbose:
                print(f"  Verbose:       {verbose}")
            
            # Show documentation (truncated)
            doc = parser.get_label(labels, concept, 'documentation', 'en-US')
            if doc:
                doc_preview = doc[:80] + '...' if len(doc) > 80 else doc
                print(f"  Documentation: {doc_preview}")
            
            print()
        else:
            print(f"{concept}: NO LABELS FOUND")
            print()
    
    # Show label type comparison
    print("="*70)
    print("LABEL TYPE COMPARISON")
    print("="*70)
    print()
    
    print("Example: us-gaap:AccountsReceivableNet")
    print()
    
    if 'us-gaap:AccountsReceivableNet' in labels:
        ar_labels = labels['us-gaap:AccountsReceivableNet']
        
        for label_type in ['standard', 'terse', 'verbose']:
            if label_type in ar_labels:
                lang_labels = ar_labels[label_type]
                if 'en-US' in lang_labels:
                    print(f"{label_type.capitalize():12} {lang_labels['en-US']}")
        print()
    else:
        print("⚠️  Concept not found")
        print()
    
    # Show concepts with documentation
    print("="*70)
    print("SAMPLE DOCUMENTATION")
    print("="*70)
    print()
    
    concepts_with_doc = [
        concept for concept, concept_labels in labels.items()
        if 'documentation' in concept_labels
    ]
    
    if concepts_with_doc:
        sample_concept = concepts_with_doc[0]
        doc = parser.get_label(labels, sample_concept, 'documentation', 'en-US')
        
        # Simplify concept name
        if ':' in sample_concept:
            simple_name = sample_concept.split(':')[1]
        else:
            simple_name = sample_concept
        
        print(f"Concept: {simple_name}")
        print()
        print(f"Documentation:")
        print(f"  {doc[:200]}...")
        print()
    else:
        print("⚠️  No documentation labels found")
        print()
    
    # Show usage example
    print("="*70)
    print("USAGE EXAMPLE")
    print("="*70)
    print()
    
    print("Getting human-readable names for reports:")
    print()
    
    report_concepts = [
        'us-gaap:Cash',
        'us-gaap:AccountsReceivableNet',
        'us-gaap:PropertyPlantAndEquipmentNet',
    ]
    
    for concept in report_concepts:
        label = parser.get_label(labels, concept, 'terse', 'en-US')
        if not label:
            label = parser.get_label(labels, concept, 'standard', 'en-US')
        
        if label:
            print(f"  {concept:40} → {label}")
        else:
            print(f"  {concept:40} → (no label)")
    
    print()
    print("This makes reports readable for humans!")
    print()
    
    # Validation checks
    print("="*70)
    print("VALIDATION CHECKS")
    print("="*70)
    print()
    
    # Check 1: Coverage
    coverage = (stats['concepts_with_standard'] / stats['total_concepts'] * 100
                if stats['total_concepts'] > 0 else 0)
    
    print(f"✅ Standard label coverage: {coverage:.1f}%")
    
    # Check 2: Documentation
    doc_coverage = (stats['concepts_with_documentation'] / stats['total_concepts'] * 100
                    if stats['total_concepts'] > 0 else 0)
    
    print(f"✅ Documentation coverage: {doc_coverage:.1f}%")
    
    print()
    
    # Success
    print("="*70)
    print("✅ TEST COMPLETED")
    print("="*70)
    print()
    print(f"Successfully parsed labels for {len(labels)} concepts")
    print(f"  Total labels: {stats['total_labels']}")
    print(f"  Languages: {stats['unique_languages']}")
    print(f"  Standard label coverage: {coverage:.1f}%")
    print()
    
    return 0


def main():
    """Main entry point."""
    try:
        return test_label_parsing()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())