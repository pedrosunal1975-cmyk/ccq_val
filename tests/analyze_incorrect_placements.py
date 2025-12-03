#!/usr/bin/env python3
"""
Diagnostic: Analyze the 699 concepts where BOTH mappers placed incorrectly.

This will help us understand:
1. What types of concepts are being misplaced?
2. Are they extensions or base concepts?
3. What statements are they placed in vs. what taxonomy says?
4. Are there patterns we can fix?
"""

import json
from pathlib import Path
from collections import Counter, defaultdict

# Read reconciliation report
report_path = Path("/mnt/map_pro/data/unified_mapped/sec/PLUG_POWER_INC/10-K/2025-03-03/reconciliation_report.json")

with open(report_path) as f:
    report = json.load(f)

print("="*80)
print("ANALYZING 699 INCORRECT PLACEMENTS")
print("="*80)

statements = report.get('statements', {})
incorrect_concepts = []

# Collect all concepts where both mappers are wrong
for stmt_type, stmt_data in statements.items():
    for concept_data in stmt_data.get('taxonomy_correct_neither', []):
        concept_data['statement_being_reconciled'] = stmt_type
        incorrect_concepts.append(concept_data)

print(f"\nFound {len(incorrect_concepts)} incorrect placements")

# ANALYSIS 1: Extension vs. Base concepts
print("\n" + "="*80)
print("ANALYSIS 1: Extension vs Base Concepts")
print("="*80)

extension_count = 0
base_count = 0

for c in incorrect_concepts:
    concept = c.get('concept', '')
    if ':' in concept:
        prefix = concept.split(':')[0]
        if prefix in ['us-gaap', 'dei', 'srt', 'invest', 'currency']:
            base_count += 1
        else:
            extension_count += 1
    else:
        extension_count += 1

print(f"Extensions (company-specific): {extension_count}")
print(f"Base taxonomy concepts: {base_count}")

# ANALYSIS 2: What statements are they in?
print("\n" + "="*80)
print("ANALYSIS 2: Where Both Mappers Placed Them")
print("="*80)

map_pro_statements = Counter()
ccq_statements = Counter()
taxonomy_statements = Counter()

for c in incorrect_concepts:
    # Current statement being reconciled
    current_stmt = c.get('statement_being_reconciled')
    
    # Where taxonomy says it should be
    taxonomy_stmt = c.get('taxonomy_statement', 'unknown')
    
    # Both mappers placed it in current_stmt (that's why they're both wrong)
    map_pro_statements[current_stmt] += 1
    ccq_statements[current_stmt] += 1
    taxonomy_statements[taxonomy_stmt] += 1

print("\nMappers placed them in:")
for stmt, count in map_pro_statements.most_common():
    print(f"  {stmt}: {count}")

print("\nTaxonomy says they should be in:")
for stmt, count in taxonomy_statements.most_common():
    print(f"  {stmt}: {count}")

# ANALYSIS 3: Common misplacement patterns
print("\n" + "="*80)
print("ANALYSIS 3: Common Misplacement Patterns")
print("="*80)

patterns = defaultdict(int)

for c in incorrect_concepts:
    current_stmt = c.get('statement_being_reconciled')
    taxonomy_stmt = c.get('taxonomy_statement', 'unknown')
    
    pattern = f"{current_stmt} → should be {taxonomy_stmt}"
    patterns[pattern] += 1

print("\nTop misplacement patterns:")
for pattern, count in sorted(patterns.items(), key=lambda x: -x[1])[:10]:
    print(f"  {pattern}: {count} concepts")

# ANALYSIS 4: Sample concepts by pattern
print("\n" + "="*80)
print("ANALYSIS 4: Sample Concepts by Pattern")
print("="*80)

# Group by pattern
pattern_samples = defaultdict(list)

for c in incorrect_concepts:
    current_stmt = c.get('statement_being_reconciled')
    taxonomy_stmt = c.get('taxonomy_statement', 'unknown')
    pattern = f"{current_stmt} → {taxonomy_stmt}"
    
    if len(pattern_samples[pattern]) < 5:  # Keep first 5 of each pattern
        pattern_samples[pattern].append({
            'concept': c.get('concept'),
            'is_extension': not any(p in c.get('concept', '') for p in ['us-gaap', 'dei', 'srt'])
        })

for pattern, samples in sorted(pattern_samples.items(), key=lambda x: -len(x[1]))[:5]:
    print(f"\n{pattern} (showing {len(samples)} examples):")
    for s in samples:
        ext_marker = " [EXTENSION]" if s['is_extension'] else " [BASE]"
        print(f"    {s['concept']}{ext_marker}")

# ANALYSIS 5: Concept name patterns
print("\n" + "="*80)
print("ANALYSIS 5: Common Words in Misplaced Concepts")
print("="*80)

# Extract words from concept names
word_counts = Counter()

for c in incorrect_concepts:
    concept = c.get('concept', '')
    # Remove namespace prefix
    if ':' in concept:
        concept = concept.split(':')[1]
    
    # Split camelCase into words
    import re
    words = re.findall('[A-Z][a-z]*', concept)
    
    for word in words:
        if len(word) > 3:  # Skip short words
            word_counts[word.lower()] += 1

print("\nMost common words in misplaced concepts:")
for word, count in word_counts.most_common(20):
    print(f"  {word}: {count}")

# ANALYSIS 6: Period type distribution
print("\n" + "="*80)
print("ANALYSIS 6: Do Incorrect Concepts Have Period Type Issues?")
print("="*80)

# This would require checking the actual taxonomy properties
# For now, let's see if there are patterns in names

instant_keywords = ['balance', 'outstanding', 'payable', 'receivable', 'asset', 'liability', 'equity']
duration_keywords = ['revenue', 'expense', 'income', 'loss', 'payment', 'receipt', 'change']

likely_instant = 0
likely_duration = 0
unclear = 0

for c in incorrect_concepts:
    concept_lower = c.get('concept', '').lower()
    
    has_instant = any(k in concept_lower for k in instant_keywords)
    has_duration = any(k in concept_lower for k in duration_keywords)
    
    if has_instant and not has_duration:
        likely_instant += 1
    elif has_duration and not has_instant:
        likely_duration += 1
    else:
        unclear += 1

print(f"Likely instant (balance sheet) concepts: {likely_instant}")
print(f"Likely duration (flow statement) concepts: {likely_duration}")
print(f"Unclear from name: {unclear}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

print(f"\nTotal incorrect placements: {len(incorrect_concepts)}")
print(f"Extensions: {extension_count} ({extension_count/len(incorrect_concepts)*100:.1f}%)")
print(f"Base concepts: {base_count} ({base_count/len(incorrect_concepts)*100:.1f}%)")

print("\nKey findings:")
print("1. Check if extensions need better period_type extraction")
print("2. Check if base concepts have missing/wrong taxonomy data")
print("3. Review top misplacement patterns for systematic issues")

print("="*80)