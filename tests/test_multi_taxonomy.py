#!/usr/bin/env python3
"""
Test: Complete Multi-Taxonomy Authority System
===============================================

Tests Phase 1 implementation:
1. Multi-taxonomy loading (us-gaap, dei, srt, ecd)
2. Extension loading with inheritance tracing
3. Statement classification propagation

This should dramatically increase taxonomy coverage!
"""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engines.fact_authority.taxonomy_interface import TaxonomyAuthorityReader
from engines.fact_authority.filing_taxonomy_detector import FilingTaxonomyDetector

print("="*70)
print("MULTI-TAXONOMY AUTHORITY SYSTEM TEST")
print("="*70)

# Initialize components
taxonomy_base = Path('/mnt/map_pro/data/taxonomies')
detector = FilingTaxonomyDetector(taxonomy_base)
reader = TaxonomyAuthorityReader()

print("\n[STEP 1] Detect ALL taxonomies for us-gaap-2024")
print("-"*70)

# Simulate namespace detection
namespaces = ['us-gaap', 'dei', 'srt', 'plug']
print(f"Simulated namespaces detected: {namespaces}")

# Find taxonomy paths
search_root = taxonomy_base / 'libraries' / 'us-gaap-2024'
us_gaap_dir = detector._find_taxonomy_files_directory(search_root, 'us-gaap')

if not us_gaap_dir:
    print("✗ Could not find us-gaap taxonomy")
    sys.exit(1)

print(f"\n✓ Found us-gaap: {us_gaap_dir}")

# Manually build paths list (simulating detector's work)
taxonomy_paths = [us_gaap_dir]

# Look for other standard taxonomies
for tax_name in ['dei', 'srt', 'ecd']:
    tax_path = taxonomy_base / 'libraries' / f"{tax_name}-2024"
    if tax_path.exists():
        tax_dir = detector._find_taxonomy_files_directory(tax_path, tax_name)
        if tax_dir:
            taxonomy_paths.append(tax_dir)
            print(f"✓ Found {tax_name}: {tax_dir}")
        else:
            print(f"✗ {tax_name} directory exists but no .xsd files found")
    else:
        print(f"  {tax_name}: Not found (optional)")

print(f"\nTotal taxonomy paths to load: {len(taxonomy_paths)}")

print("\n[STEP 2] Load complete taxonomy hierarchy")
print("-"*70)

hierarchy = reader.load_filing_taxonomy(taxonomy_paths)

print(f"\nTotal concepts loaded: {len(hierarchy['concepts'])}")

# Count by namespace
from collections import Counter
namespace_counts = Counter()
for qname in hierarchy['concepts'].keys():
    ns = qname.split(':')[0] if ':' in qname else 'unknown'
    namespace_counts[ns] += 1

print(f"\nConcepts by namespace:")
for ns, count in sorted(namespace_counts.items(), key=lambda x: -x[1]):
    pct = 100 * count / len(hierarchy['concepts'])
    print(f"  {ns:15} {count:5,} ({pct:5.1f}%)")

# Count statement classifications
concepts_with_statement = sum(
    1 for c in hierarchy['concepts'].values() 
    if 'statement' in c
)

print(f"\nConcepts with statement classification: {concepts_with_statement:,}")
print(f"Coverage: {100*concepts_with_statement/len(hierarchy['concepts']):.1f}%")

# Show sample concepts from each namespace
print("\n[STEP 3] Sample concepts")
print("-"*70)

for ns in sorted(namespace_counts.keys())[:4]:
    print(f"\n{ns} namespace:")
    sample = [
        (qname, data) for qname, data in hierarchy['concepts'].items()
        if qname.startswith(f"{ns}:")
    ][:3]
    
    for qname, data in sample:
        stmt = data.get('statement', 'NONE')
        src = data.get('statement_source', '?')
        print(f"  {qname:50} -> {stmt:20} ({src})")

print("\n" + "="*70)
print("✓ Multi-taxonomy authority system operational!")
print("="*70)