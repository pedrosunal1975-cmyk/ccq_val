#!/usr/bin/env python3
# File: tests/diagnose_import_error.py
# Diagnostic script to find where taxonomy_file_discoverer is being imported

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("DIAGNOSTIC: Finding taxonomy_file_discoverer import")
print("=" * 80)

# Check all __init__.py files
fact_authority_path = project_root / 'engines' / 'fact_authority'

init_files = [
    fact_authority_path / '__init__.py',
    fact_authority_path / 'taxonomy_reader' / '__init__.py',
    fact_authority_path / 'filings_reader' / '__init__.py',
    fact_authority_path / 'facts_reader' / '__init__.py',
    fact_authority_path / 'input' / '__init__.py',
    fact_authority_path / 'process' / '__init__.py',
    fact_authority_path / 'output' / '__init__.py',
]

print("\nChecking __init__.py files for 'taxonomy_file_discoverer':")
print("-" * 80)

for init_file in init_files:
    if init_file.exists():
        with open(init_file, 'r') as f:
            content = f.read()
            if 'taxonomy_file_discoverer' in content:
                print(f"\n✗ FOUND in: {init_file}")
                print("  Lines containing it:")
                for i, line in enumerate(content.split('\n'), 1):
                    if 'taxonomy_file_discoverer' in line:
                        print(f"    Line {i}: {line.strip()}")
            else:
                print(f"✓ Clean: {init_file.relative_to(project_root)}")
    else:
        print(f"⚠ Missing: {init_file.relative_to(project_root)}")

# Check for __pycache__
print("\n" + "=" * 80)
print("Checking for __pycache__ directories:")
print("-" * 80)

pycache_dirs = list(fact_authority_path.rglob('__pycache__'))
if pycache_dirs:
    print(f"\nFound {len(pycache_dirs)} __pycache__ directories:")
    for p in pycache_dirs:
        print(f"  {p.relative_to(project_root)}")
    print("\n⚠ Old cached imports might be causing issues!")
    print("  Solution: Delete all __pycache__ directories")
else:
    print("✓ No __pycache__ directories found")

# Check for old .py files in root
print("\n" + "=" * 80)
print("Checking for old .py files in fact_authority root:")
print("-" * 80)

root_py_files = [f for f in fact_authority_path.glob('*.py') if f.name != '__init__.py']
if root_py_files:
    print(f"\nFound {len(root_py_files)} .py files in root:")
    for f in root_py_files:
        print(f"  {f.name}")
        # Check if it imports taxonomy_file_discoverer
        with open(f, 'r') as file:
            if 'taxonomy_file_discoverer' in file.read():
                print(f"    ✗ This file imports taxonomy_file_discoverer!")
else:
    print("✓ No extra .py files in root (besides fact_authority.py expected)")

print("\n" + "=" * 80)
print("RECOMMENDATION:")
print("=" * 80)

print("""
1. Delete all __pycache__ directories:
   cd /home/a/Desktop/Stock_software/ccq_val
   find engines/fact_authority -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

2. Check the files flagged above and remove bad imports

3. Run this test again to verify
""")