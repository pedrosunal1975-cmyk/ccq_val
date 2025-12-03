#!/usr/bin/env python3
"""
Diagnostic: Check Loaded Taxonomy Data Structure
=================================================

Tests what data structure is returned by taxonomy loading and whether
concepts have 'statement' field for fact authority reconciliation.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engines.fact_authority.taxonomy_interface import TaxonomyAuthorityReader

print("="*70)
print("TAXONOMY DATA STRUCTURE DIAGNOSTIC")
print("="*70)

# Initialize reader
print("\n[STEP 1] Initialize TaxonomyAuthorityReader")
print("-"*70)
reader = TaxonomyAuthorityReader()

# Load taxonomy
print("\n[STEP 2] Load taxonomy for us-gaap-2024")
print("-"*70)
taxonomy_base = Path('/mnt/map_pro/data/taxonomies')

# Find the actual elts directory that has the main file
from engines.fact_authority.filing_taxonomy_detector import FilingTaxonomyDetector

detector = FilingTaxonomyDetector(taxonomy_base)

# Manually find the directory with main file
search_root = taxonomy_base / 'libraries' / 'us-gaap-2024'
taxonomy_dir = detector._find_taxonomy_files_directory(search_root, 'us-gaap')

if not taxonomy_dir:
    print(f"✗ Could not find taxonomy directory")
    sys.exit(1)

print(f"Found taxonomy directory: {taxonomy_dir}")

# Load taxonomy using this path
paths = [taxonomy_dir]

hierarchy = reader.load_filing_taxonomy(paths)

print("\n[STEP 3] Inspect loaded data structure")
print("-"*70)

# Check structure
print(f"\nTop-level keys: {list(hierarchy.keys())}")

if 'concepts' in hierarchy:
    concepts = hierarchy['concepts']
    print(f"Number of concepts: {len(concepts)}")
    
    if len(concepts) > 0:
        # Get first few concepts
        sample_concepts = list(concepts.items())[:5]
        
        print(f"\nFirst 5 concepts:")
        for qname, data in sample_concepts:
            print(f"\n  Concept: {qname}")
            print(f"  Keys: {list(data.keys())}")
            
            # Check for statement field
            if 'statement' in data:
                print(f"  ✓ Has 'statement' field: {data['statement']}")
            else:
                print(f"  ✗ MISSING 'statement' field!")
            
            # Show all fields
            print(f"  Data: {data}")
    
    # Check how many concepts have 'statement' field
    concepts_with_statement = sum(1 for c in concepts.values() if 'statement' in c)
    print(f"\n[CRITICAL] Concepts with 'statement' field: {concepts_with_statement}/{len(concepts)}")
    
    if concepts_with_statement == 0:
        print("\n✗ PROBLEM: No concepts have 'statement' field!")
        print("  This means fact authority cannot determine statement placement.")
        print("  Taxonomy concepts need 'statement' field from presentation linkbase.")
    else:
        print(f"\n✓ OK: {concepts_with_statement} concepts have statement assignments")

if 'metadata' in hierarchy:
    metadata = hierarchy['metadata']
    print(f"\nMetadata: {metadata}")

print("\n" + "="*70)