#!/usr/bin/env python3
"""
Analyze the 699 discrepancies to understand misplacement patterns.
"""

import json
from pathlib import Path
from collections import Counter, defaultdict
import re

report_path = Path("/mnt/map_pro/data/unified_mapped/sec/PLUG_POWER_INC/10-K/2025-03-03/reconciliation_report.json")

with open(report_path) as f:
    report = json.load(f)

discrepancies = report.get('discrepancies', [])

print("="*80)
print(f"ANALYZING {len(discrepancies)} INCORRECT PLACEMENTS")
print("="*80)

# ANALYSIS 1: Extension vs Base
print("\n" + "="*80)
print("ANALYSIS 1: Extension vs Base Concepts")
print("="*80)

extension_count = 0
base_count = 0
by_namespace = Counter()

for disc in discrepancies:
    concept = disc.get('concept', '')
    if ':' in concept:
        namespace = concept.split(':')[0]
        by_namespace[namespace] += 1
        
        if namespace in ['us-gaap', 'dei', 'srt', 'invest', 'currency']:
            base_count += 1
        else:
            extension_count += 1
    else:
        extension_count += 1

print(f"\nExtensions (company-specific): {extension_count} ({extension_count/len(discrepancies)*100:.1f}%)")
print(f"Base taxonomy concepts: {base_count} ({base_count/len(discrepancies)*100:.1f}%)")

print(f"\nBreakdown by namespace:")
for ns, count in by_namespace.most_common():
    print(f"  {ns}: {count}")

# ANALYSIS 2: Misplacement Patterns
print("\n" + "="*80)
print("ANALYSIS 2: Misplacement Patterns")
print("="*80)

patterns = Counter()

for disc in discrepancies:
    current = disc.get('current_statement', 'unknown')
    expected = disc.get('expected_statement', 'unknown')
    pattern = f"{current} → {expected}"
    patterns[pattern] += 1

print("\nTop misplacement patterns:")
for pattern, count in patterns.most_common():
    print(f"  {pattern}: {count} concepts ({count/len(discrepancies)*100:.1f}%)")

# ANALYSIS 3: Sample concepts by pattern
print("\n" + "="*80)
print("ANALYSIS 3: Sample Concepts by Pattern")
print("="*80)

pattern_samples = defaultdict(list)

for disc in discrepancies:
    current = disc.get('current_statement', 'unknown')
    expected = disc.get('expected_statement', 'unknown')
    pattern = f"{current} → {expected}"
    
    if len(pattern_samples[pattern]) < 5:
        concept = disc.get('concept', '')
        is_ext = ':' in concept and concept.split(':')[0] not in ['us-gaap', 'dei', 'srt']
        
        pattern_samples[pattern].append({
            'concept': concept,
            'is_extension': is_ext,
            'in_map_pro': disc.get('in_map_pro', False),
            'in_ccq': disc.get('in_ccq', False)
        })

for pattern, samples in sorted(pattern_samples.items(), key=lambda x: -patterns[x[0]])[:5]:
    count = patterns[pattern]
    print(f"\n{pattern} ({count} total):")
    for s in samples:
        ext = "[EXT]" if s['is_extension'] else "[BASE]"
        mappers = []
        if s['in_map_pro']: mappers.append("MP")
        if s['in_ccq']: mappers.append("CCQ")
        mapper_str = "+".join(mappers) if mappers else "NONE"
        
        print(f"  {s['concept']:60s} {ext:7s} in: {mapper_str}")

# ANALYSIS 4: Who has these concepts?
print("\n" + "="*80)
print("ANALYSIS 4: Mapper Coverage of Incorrect Concepts")
print("="*80)

both_have = sum(1 for d in discrepancies if d.get('in_map_pro') and d.get('in_ccq'))
only_mp = sum(1 for d in discrepancies if d.get('in_map_pro') and not d.get('in_ccq'))
only_ccq = sum(1 for d in discrepancies if not d.get('in_map_pro') and d.get('in_ccq'))
neither = sum(1 for d in discrepancies if not d.get('in_map_pro') and not d.get('in_ccq'))

print(f"\nBoth mappers have concept: {both_have} ({both_have/len(discrepancies)*100:.1f}%)")
print(f"Only Map Pro has it: {only_mp} ({only_mp/len(discrepancies)*100:.1f}%)")
print(f"Only CCQ has it: {only_ccq} ({only_ccq/len(discrepancies)*100:.1f}%)")
print(f"Neither has it: {neither} ({neither/len(discrepancies)*100:.1f}%)")

# ANALYSIS 5: Common concept name patterns
print("\n" + "="*80)
print("ANALYSIS 5: Common Words in Misplaced Concepts")
print("="*80)

word_counts = Counter()

for disc in discrepancies:
    concept = disc.get('concept', '')
    if ':' in concept:
        concept = concept.split(':')[1]
    
    # Split camelCase
    words = re.findall('[A-Z][a-z]*', concept)
    
    for word in words:
        if len(word) > 3:
            word_counts[word.lower()] += 1

print("\nMost frequent words:")
for word, count in word_counts.most_common(20):
    print(f"  {word:20s}: {count:3d}")

# ANALYSIS 6: Focus on most problematic pattern
print("\n" + "="*80)
print("ANALYSIS 6: Deep Dive - Most Common Misplacement")
print("="*80)

top_pattern = patterns.most_common(1)[0][0]
top_pattern_discs = [d for d in discrepancies 
                     if f"{d.get('current_statement')} → {d.get('expected_statement')}" == top_pattern]

print(f"\nPattern: {top_pattern} ({len(top_pattern_discs)} concepts)")

# Check if these are extensions or base
ext_in_pattern = sum(1 for d in top_pattern_discs 
                     if ':' in d.get('concept', '') 
                     and d.get('concept', '').split(':')[0] not in ['us-gaap', 'dei', 'srt'])

print(f"Extensions: {ext_in_pattern} ({ext_in_pattern/len(top_pattern_discs)*100:.1f}%)")
print(f"Base: {len(top_pattern_discs) - ext_in_pattern} ({(len(top_pattern_discs) - ext_in_pattern)/len(top_pattern_discs)*100:.1f}%)")

print(f"\nSample concepts from this pattern:")
for d in top_pattern_discs[:10]:
    concept = d.get('concept', '')
    short_concept = concept.split(':')[1] if ':' in concept else concept
    ext = "[EXT]" if ':' in concept and concept.split(':')[0] not in ['us-gaap', 'dei', 'srt'] else "[BASE]"
    print(f"  {short_concept:50s} {ext}")

print("\n" + "="*80)
print("SUMMARY & RECOMMENDATIONS")
print("="*80)

print(f"\nTotal misplacements: {len(discrepancies)}")
print(f"Extensions: {extension_count} ({extension_count/len(discrepancies)*100:.1f}%)")
print(f"Base concepts: {base_count} ({base_count/len(discrepancies)*100:.1f}%)")

print(f"\nBiggest issue: {top_pattern} ({patterns[top_pattern]} concepts)")

print("\nPossible root causes to investigate:")
print("1. Extension period_type extraction may be wrong")
print("2. Taxonomy classification logic may not match XBRL spec")
print("3. Some concepts may legitimately appear in multiple statements")
print("4. Text block concepts (descriptions) may be misclassified")

print("="*80)