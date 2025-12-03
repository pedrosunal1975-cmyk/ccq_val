#!/usr/bin/env python3
"""
Find concepts that appear in BOTH Map Pro and CCQ
and see where they're placed.
"""

import json
from pathlib import Path
from collections import defaultdict

# Paths
map_pro_dir = Path("/mnt/map_pro/data/mapped_statements/sec/PLUG_POWER_INC/10-K/2025-03-03")
ccq_dir = Path("/mnt/map_pro/data/ccq_mapped/sec/PLUG_POWER_INC/10-K/2025-03-03")

statements = ['balance_sheet', 'income_statement', 'cash_flow', 'other']

# Build indexes
map_pro_concepts = defaultdict(set)  # concept -> set of statements
ccq_concepts = defaultdict(set)      # concept -> set of statements

print("="*80)
print("CONCEPT PLACEMENT COMPARISON")
print("="*80)

# Read Map Pro
for stmt in statements:
    file_path = map_pro_dir / f"{stmt}.json"
    if file_path.exists():
        with open(file_path) as f:
            data = json.load(f)
            facts = data.get('facts', [])
            for fact in facts:
                concept = fact.get('concept')
                if concept:
                    map_pro_concepts[concept].add(stmt)

# Read CCQ
for stmt in statements:
    file_path = ccq_dir / f"{stmt}.json"
    if file_path.exists():
        with open(file_path) as f:
            data = json.load(f)
            line_items = data.get('line_items', [])
            for item in line_items:
                concept = item.get('qname')
                if concept:
                    ccq_concepts[concept].add(stmt)

print(f"\nMap Pro concepts: {len(map_pro_concepts)}")
print(f"CCQ concepts: {len(ccq_concepts)}")

# Find concepts in BOTH
common_concepts = set(map_pro_concepts.keys()) & set(ccq_concepts.keys())
print(f"Concepts in BOTH: {len(common_concepts)}")

# Find ones in same statement
same_statement = []
different_statement = []

for concept in common_concepts:
    mp_stmts = map_pro_concepts[concept]
    ccq_stmts = ccq_concepts[concept]
    
    # Do they have ANY statement in common?
    if mp_stmts & ccq_stmts:  # Set intersection
        same_statement.append((concept, mp_stmts, ccq_stmts))
    else:
        different_statement.append((concept, mp_stmts, ccq_stmts))

print(f"\nConcepts in SAME statement: {len(same_statement)}")
print(f"Concepts in DIFFERENT statements: {len(different_statement)}")

if same_statement:
    print(f"\n{'='*80}")
    print("SAMPLE: Concepts in SAME statement (first 10):")
    print(f"{'='*80}")
    for concept, mp_stmts, ccq_stmts in same_statement[:10]:
        common = mp_stmts & ccq_stmts
        print(f"\n{concept}")
        print(f"  Map Pro: {mp_stmts}")
        print(f"  CCQ:     {ccq_stmts}")
        print(f"  Common:  {common}")

if different_statement:
    print(f"\n{'='*80}")
    print("SAMPLE: Concepts in DIFFERENT statements (first 10):")
    print(f"{'='*80}")
    for concept, mp_stmts, ccq_stmts in different_statement[:10]:
        print(f"\n{concept}")
        print(f"  Map Pro: {mp_stmts}")
        print(f"  CCQ:     {ccq_stmts}")

print(f"\n{'='*80}")