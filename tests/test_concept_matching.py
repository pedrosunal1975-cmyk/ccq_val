#!/usr/bin/env python3
"""
Diagnostic: Concept Matching Analysis
======================================

Analyzes why taxonomy coverage is low (26.7% instead of expected 60-75%).
Checks concept normalization, taxonomy lookups, and matching issues.
"""

import sys
import json
from pathlib import Path
from collections import Counter

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engines.fact_authority.fact_reconciler import FactReconciler
from engines.fact_authority.taxonomy_interface import TaxonomyAuthorityReader
from engines.fact_authority.filing_taxonomy_detector import FilingTaxonomyDetector

print("="*70)
print("CONCEPT MATCHING DIAGNOSTIC")
print("="*70)

# Load Map Pro facts
map_pro_file = Path('/mnt/map_pro/data/entities/PLUG_POWER_INC/10-K/2025-03-03/parsed_facts/map_pro_facts.json')
ccq_file = Path('/mnt/map_pro/data/entities/PLUG_POWER_INC/10-K/2025-03-03/parsed_facts/ccq_facts.json')

print("\n[STEP 1] Load facts")
print("-"*70)

with open(map_pro_file) as f:
    map_pro_data = json.load(f)
    map_pro_facts = map_pro_data.get('balance_sheet', [])[:10]  # First 10

with open(ccq_file) as f:
    ccq_data = json.load(f)
    ccq_facts = ccq_data.get('balance_sheet', [])[:10]  # First 10

print(f"Loaded {len(map_pro_facts)} Map Pro facts (sample)")
print(f"Loaded {len(ccq_facts)} CCQ facts (sample)")

# Load taxonomy
print("\n[STEP 2] Load taxonomy")
print("-"*70)

taxonomy_base = Path('/mnt/map_pro/data/taxonomies')
detector = FilingTaxonomyDetector(taxonomy_base)
search_root = taxonomy_base / 'libraries' / 'us-gaap-2024'
taxonomy_dir = detector._find_taxonomy_files_directory(search_root, 'us-gaap')

reader = TaxonomyAuthorityReader()
hierarchy = reader.load_filing_taxonomy([taxonomy_dir])

print(f"Taxonomy concepts: {len(hierarchy['concepts'])}")
concepts_with_statement = sum(1 for c in hierarchy['concepts'].values() if 'statement' in c)
print(f"Concepts with statement: {concepts_with_statement}")

# Analyze Map Pro concepts
print("\n[STEP 3] Analyze Map Pro concept formats")
print("-"*70)

for i, fact in enumerate(map_pro_facts[:5], 1):
    concept = fact.get('concept') or fact.get('concept_qname')
    normalized = FactReconciler.normalize_concept(concept)
    
    in_taxonomy = normalized in hierarchy['concepts']
    has_statement = hierarchy['concepts'].get(normalized, {}).get('statement') is not None
    
    print(f"\n  Fact {i}:")
    print(f"    Original: {concept}")
    print(f"    Normalized: {normalized}")
    print(f"    In taxonomy: {in_taxonomy}")
    if in_taxonomy:
        print(f"    Has statement: {has_statement}")
        if has_statement:
            print(f"    Statement: {hierarchy['concepts'][normalized]['statement']}")

# Analyze CCQ concepts
print("\n[STEP 4] Analyze CCQ concept formats")
print("-"*70)

for i, fact in enumerate(ccq_facts[:5], 1):
    concept = fact.get('concept') or fact.get('concept_qname')
    normalized = FactReconciler.normalize_concept(concept)
    
    in_taxonomy = normalized in hierarchy['concepts']
    has_statement = hierarchy['concepts'].get(normalized, {}).get('statement') is not None
    
    print(f"\n  Fact {i}:")
    print(f"    Original: {concept}")
    print(f"    Normalized: {normalized}")
    print(f"    In taxonomy: {in_taxonomy}")
    if in_taxonomy:
        print(f"    Has statement: {has_statement}")
        if has_statement:
            print(f"    Statement: {hierarchy['concepts'][normalized]['statement']}")

# Count matches across all facts
print("\n[STEP 5] Overall matching statistics")
print("-"*70)

with open(map_pro_file) as f:
    all_map_pro = json.load(f)
    all_map_pro_facts = []
    for stmt in ['balance_sheet', 'income_statement', 'cash_flow', 'other']:
        all_map_pro_facts.extend(all_map_pro.get(stmt, []))

with open(ccq_file) as f:
    all_ccq = json.load(f)
    all_ccq_facts = []
    for stmt in ['balance_sheet', 'income_statement', 'cash_flow', 'other']:
        all_ccq_facts.extend(all_ccq.get(stmt, []))

map_pro_concepts = []
for fact in all_map_pro_facts:
    concept = fact.get('concept') or fact.get('concept_qname')
    if concept:
        normalized = FactReconciler.normalize_concept(concept)
        map_pro_concepts.append(normalized)

ccq_concepts = []
for fact in all_ccq_facts:
    concept = fact.get('concept') or fact.get('concept_qname')
    if concept:
        normalized = FactReconciler.normalize_concept(concept)
        ccq_concepts.append(normalized)

# Check taxonomy coverage
map_pro_in_taxonomy = sum(1 for c in set(map_pro_concepts) if c in hierarchy['concepts'])
map_pro_with_statement = sum(1 for c in set(map_pro_concepts) 
                              if hierarchy['concepts'].get(c, {}).get('statement'))

ccq_in_taxonomy = sum(1 for c in set(ccq_concepts) if c in hierarchy['concepts'])
ccq_with_statement = sum(1 for c in set(ccq_concepts) 
                         if hierarchy['concepts'].get(c, {}).get('statement'))

print(f"\nMap Pro ({len(set(map_pro_concepts))} unique concepts):")
print(f"  Found in taxonomy: {map_pro_in_taxonomy} ({100*map_pro_in_taxonomy/len(set(map_pro_concepts)):.1f}%)")
print(f"  Have statement field: {map_pro_with_statement} ({100*map_pro_with_statement/len(set(map_pro_concepts)):.1f}%)")

print(f"\nCCQ ({len(set(ccq_concepts))} unique concepts):")
print(f"  Found in taxonomy: {ccq_in_taxonomy} ({100*ccq_in_taxonomy/len(set(ccq_concepts)):.1f}%)")
print(f"  Have statement field: {ccq_with_statement} ({100*ccq_with_statement/len(set(ccq_concepts)):.1f}%)")

# Sample concepts NOT in taxonomy
print("\n[STEP 6] Sample concepts NOT in taxonomy")
print("-"*70)

not_in_taxonomy = [c for c in set(map_pro_concepts + ccq_concepts) 
                   if c not in hierarchy['concepts']][:10]

print(f"\nFirst 10 concepts not found in taxonomy:")
for concept in not_in_taxonomy:
    print(f"  - {concept}")

print("\n" + "="*70)