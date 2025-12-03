#!/usr/bin/env python3
"""
Diagnostic: Why doesn't Map Pro ever match the taxonomy?
"""

import sys
import json
from pathlib import Path

# Load the reconciliation report
report_path = Path("/mnt/map_pro/data/unified_mapped/sec/PLUG_POWER_INC/10-K/2025-03-03/reconciliation_report.json")

if not report_path.exists():
    print(f"Report not found: {report_path}")
    sys.exit(1)

with open(report_path) as f:
    report = json.load(f)

print("="*80)
print("MAP PRO MATCHING DIAGNOSTIC")
print("="*80)

# Get overall stats
stats = report.get('overall_statistics', {})
print(f"\nOverall Statistics:")
print(f"  Total concepts: {stats.get('total_concepts')}")
print(f"  taxonomy_correct_both: {stats.get('taxonomy_correct_both')}")
print(f"  taxonomy_correct_map_pro_only: {stats.get('taxonomy_correct_map_pro_only')}")
print(f"  taxonomy_correct_ccq_only: {stats.get('taxonomy_correct_ccq_only')}")
print(f"  taxonomy_correct_neither: {stats.get('taxonomy_correct_neither')}")
print(f"  not_in_taxonomy: {stats.get('not_in_taxonomy')}")
print(f"  Map Pro facts: {stats.get('map_pro_facts')}")
print(f"  CCQ facts: {stats.get('ccq_facts')}")

# Look at discrepancies per statement
print(f"\n{'='*80}")
print("STATEMENT-BY-STATEMENT ANALYSIS")
print(f"{'='*80}")

statements = report.get('statements', {})
for stmt_name, stmt_data in statements.items():
    print(f"\n{stmt_name}:")
    stmt_stats = stmt_data.get('statistics', {})
    print(f"  Total concepts: {stmt_stats.get('total_concepts', 0)}")
    print(f"  Map Pro facts: {stmt_stats.get('map_pro_facts', 0)}")
    print(f"  CCQ facts: {stmt_stats.get('ccq_facts', 0)}")
    print(f"  taxonomy_correct_both: {stmt_stats.get('taxonomy_correct_both', 0)}")
    print(f"  taxonomy_correct_ccq_only: {stmt_stats.get('taxonomy_correct_ccq_only', 0)}")
    
    # Show some sample discrepancies
    discrepancies = stmt_data.get('discrepancies', [])
    if discrepancies:
        print(f"\n  Sample discrepancies (first 3):")
        for disc in discrepancies[:3]:
            concept = disc.get('concept', 'N/A')
            expected = disc.get('expected_statement', 'N/A')
            current = disc.get('current_statement', 'N/A')
            in_map_pro = disc.get('in_map_pro', False)
            in_ccq = disc.get('in_ccq', False)
            reason = disc.get('reason', 'N/A')
            
            print(f"    - {concept}")
            print(f"      Expected: {expected}, Current: {current}")
            print(f"      Map Pro: {in_map_pro}, CCQ: {in_ccq}")
            print(f"      Reason: {reason}")

print(f"\n{'='*80}")
print("DIAGNOSTIC COMPLETE")
print(f"{'='*80}")