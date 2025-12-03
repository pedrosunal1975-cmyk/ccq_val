#!/usr/bin/env python3
# File: tests/diagnose_all_imports.py
# Comprehensive diagnostic - checks ALL .py files

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("COMPREHENSIVE DIAGNOSTIC: Checking ALL .py files")
print("=" * 80)

fact_authority_path = project_root / 'engines' / 'fact_authority'

# Search ALL .py files for bad imports
bad_imports = [
    'taxonomy_file_discoverer',
    'from engines.fact_authority.taxonomy_interface',
    'from engines.fact_authority.taxonomy_constants',
    'from .taxonomy_file_discoverer',
    'from .taxonomy_interface',
    'from .taxonomy_constants',
]

print("\nSearching ALL .py files for bad imports...")
print("-" * 80)

found_issues = False

for py_file in fact_authority_path.rglob('*.py'):
    # Skip __pycache__
    if '__pycache__' in str(py_file):
        continue
    
    with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        lines = content.split('\n')
        
        for bad_import in bad_imports:
            if bad_import in content:
                found_issues = True
                print(f"\n✗ FOUND '{bad_import}' in:")
                print(f"   {py_file.relative_to(project_root)}")
                print("   Lines:")
                for i, line in enumerate(lines, 1):
                    if bad_import in line:
                        print(f"     Line {i}: {line.strip()}")

if not found_issues:
    print("\n✓ No bad imports found in any .py files!")
    print("\n⚠ This is very strange - the error must be coming from elsewhere")
    print("\nLet's check if the SUB-ENGINE files exist:")
    
    critical_files = [
        'taxonomy_reader/taxonomy_reader.py',
        'filings_reader/filing_reader.py',
        'facts_reader/parsed_facts_loader.py',
    ]
    
    print("\nChecking critical files exist:")
    print("-" * 80)
    for rel_path in critical_files:
        full_path = fact_authority_path / rel_path
        if full_path.exists():
            print(f"✓ {rel_path}")
        else:
            print(f"✗ MISSING: {rel_path}")

print("\n" + "=" * 80)
print("TRYING DIRECT IMPORT TO GET DETAILED ERROR:")
print("=" * 80)

print("\nAttempting to import TaxonomyReader directly...")
try:
    from engines.fact_authority.taxonomy_reader import TaxonomyReader
    print("✓ TaxonomyReader imported successfully!")
except Exception as e:
    print(f"✗ FAILED: {e}")
    print("\nDetailed traceback:")
    import traceback
    traceback.print_exc()

print("\nAttempting to import FilingReader directly...")
try:
    from engines.fact_authority.filings_reader import FilingReader
    print("✓ FilingReader imported successfully!")
except Exception as e:
    print(f"✗ FAILED: {e}")
    print("\nDetailed traceback:")
    import traceback
    traceback.print_exc()

print("\nAttempting to import ParsedFactsLoader directly...")
try:
    from engines.fact_authority.facts_reader import ParsedFactsLoader
    print("✓ ParsedFactsLoader imported successfully!")
except Exception as e:
    print(f"✗ FAILED: {e}")
    print("\nDetailed traceback:")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("DIAGNOSIS COMPLETE")
print("=" * 80)