#!/usr/bin/env python3
"""
Real XBRL Load Facts Test
==========================

Tests loading facts from actual XBRL file for the filing you just ran.
Run from ccq_val root: python tests/test_duplicate_source_tracking.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("="*80)
print("REAL XBRL LOAD FACTS TEST")
print("="*80)
print()

# The filing you just ran
filing_id = "ec098617-aed4-4f25-8194-ae0e6ddbbc34"
print(f"Testing with filing: {filing_id}")
print()

# Find the XBRL file
# Based on your Map Pro structure, it should be in:
# /mnt/map_pro/data/entities/sec/PLUG_POWER_INC/filings/10-K/{accession}/extracted/*.xml

map_pro_root = Path("/mnt/map_pro")
entities_path = map_pro_root / "data" / "entities" / "sec" / "PLUG_POWER_INC" / "filings" / "10-K"

print(f"Searching for XBRL in: {entities_path}")
print()

if not entities_path.exists():
    print(f"ERROR: Path doesn't exist: {entities_path}")
    sys.exit(1)

# Find the XML file
xbrl_file = None
for accession_dir in entities_path.iterdir():
    if not accession_dir.is_dir():
        continue
    
    extracted_dir = accession_dir / "extracted"
    if not extracted_dir.exists():
        continue
    
    for xml_file in extracted_dir.glob("*.xml"):
        # Skip schema files
        if '_htm.xml' in xml_file.name or xml_file.name.startswith('xbrldi'):
            continue
        xbrl_file = xml_file
        break
    
    if xbrl_file:
        break

if not xbrl_file:
    print("ERROR: Could not find XBRL instance file")
    print("Checked directories:")
    for d in entities_path.iterdir():
        if d.is_dir():
            print(f"  - {d}")
    sys.exit(1)

print(f"Found XBRL file: {xbrl_file}")
print(f"File exists: {xbrl_file.exists()}")
print(f"File size: {xbrl_file.stat().st_size:,} bytes")
print()

# Now test loading facts
print("="*80)
print("TESTING XBRLLoader.load_facts()")
print("="*80)
print()

from engines.ccq_mapper.loaders.xbrl_loader import XBRLLoader

loader = XBRLLoader()

print("Loading facts from raw XBRL...")
try:
    facts = loader.load_facts(xbrl_file)
    print(f"✓ Successfully loaded {len(facts)} facts from raw XBRL")
    print()
    
    if len(facts) == 0:
        print("ERROR: No facts were loaded!")
        print("This means the load_facts method is not working correctly.")
        sys.exit(1)
    
    # Show sample facts
    print("Sample facts (first 5):")
    print("-"*80)
    for i, fact in enumerate(facts[:5], 1):
        print(f"{i}. Concept: {fact.get('concept')}")
        print(f"   Context: {fact.get('context_ref', '')[:50]}...")
        print(f"   Value: {fact.get('value', '')[:50]}")
        print()
    
    # Check for duplicates in raw XBRL
    print("="*80)
    print("CHECKING FOR DUPLICATES IN RAW XBRL")
    print("="*80)
    print()
    
    from collections import defaultdict
    
    fact_groups = defaultdict(list)
    for fact in facts:
        concept = fact.get('concept')
        context = fact.get('context_ref')
        if concept and context:
            key = (concept, context)
            fact_groups[key].append(fact)
    
    duplicate_groups = {k: v for k, v in fact_groups.items() if len(v) > 1}
    
    print(f"Total facts: {len(facts)}")
    print(f"Unique (concept, context) pairs: {len(fact_groups)}")
    print(f"Duplicate groups: {len(duplicate_groups)}")
    print()
    
    if duplicate_groups:
        print("Found duplicates in raw XBRL! Showing first 3:")
        print("-"*80)
        for i, ((concept, context), dupe_facts) in enumerate(list(duplicate_groups.items())[:3], 1):
            values = [f.get('value') for f in dupe_facts]
            print(f"{i}. Concept: {concept}")
            print(f"   Context: {context[:50]}...")
            print(f"   Count: {len(dupe_facts)}")
            print(f"   Values: {values}")
            print()
        
        print("✓ Raw XBRL contains duplicates - source tracing should work!")
    else:
        print("⚠ No duplicates found in raw XBRL")
        print("  This means duplicates are being introduced during parsing or mapping")
    
except Exception as e:
    print(f"✗ Failed to load facts: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("="*80)
print("TEST COMPLETE")
print("="*80)
print()
print("Summary:")
print(f"  - XBRLLoader.load_facts() works: YES")
print(f"  - Facts loaded from XBRL: {len(facts)}")
print(f"  - Duplicates in raw XBRL: {len(duplicate_groups)}")
print()
print("If the mapper still shows 'Unknown: 100%', then:")
print("  1. Check that mapper_coordinator is passing the correct xbrl_path")
print("  2. The path might be None or incorrect during actual mapping")