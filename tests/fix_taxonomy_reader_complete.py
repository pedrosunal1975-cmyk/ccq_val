#!/usr/bin/env python3
# Complete fix for taxonomy_reader.py

import sys
from pathlib import Path

file_path = Path('/home/a/Desktop/Stock_software/ccq_val/engines/fact_authority/taxonomy_reader/taxonomy_reader.py')

print("=" * 80)
print("COMPLETE FIX: taxonomy_reader.py")
print("=" * 80)

# Read file
with open(file_path, 'r') as f:
    lines = f.readlines()

print("\nStep 1: Analyzing usage of TaxonomyFileDiscoverer...")

# Find all references
import_line = None
usage_lines = []

for i, line in enumerate(lines):
    if 'from engines.fact_authority.taxonomy_file_discoverer import' in line:
        import_line = i
        print(f"  Line {i+1}: Import statement")
    elif 'TaxonomyFileDiscoverer' in line:
        usage_lines.append(i)
        print(f"  Line {i+1}: {line.strip()}")

print(f"\nFound: 1 import + {len(usage_lines)} usage(s)")

# Check if file_discoverer is used elsewhere
print("\nStep 2: Checking if self.file_discoverer is used...")
discoverer_usages = []
for i, line in enumerate(lines):
    if 'self.file_discoverer' in line and i not in usage_lines:
        discoverer_usages.append(i)
        print(f"  Line {i+1}: {line.strip()}")

if discoverer_usages:
    print(f"\n✗ self.file_discoverer is used {len(discoverer_usages)} times")
    print("  Cannot safely remove without refactoring")
    print("\nThese lines need manual fixes:")
    for line_num in discoverer_usages:
        print(f"  Line {line_num+1}: {lines[line_num].strip()}")
else:
    print("  ✓ self.file_discoverer is never used!")
    print("  Safe to remove")

print("\nStep 3: Creating fixed version...")

# Create backup
import shutil
backup = str(file_path) + '.backup2'
shutil.copy2(file_path, backup)
print(f"  ✓ Backup: {backup}")

# Remove the problematic lines
new_lines = []
for i, line in enumerate(lines):
    # Skip import line
    if import_line is not None and i == import_line:
        print(f"  - Removing line {i+1}: import statement")
        continue
    # Skip usage lines
    if i in usage_lines:
        print(f"  - Removing line {i+1}: self.file_discoverer = ...")
        continue
    new_lines.append(line)

# Write fixed file
with open(file_path, 'w') as f:
    f.writelines(new_lines)

print(f"  ✓ Wrote {len(new_lines)} lines (removed {len(lines) - len(new_lines)} lines)")

print("\nStep 4: Testing import...")
sys.path.insert(0, '/home/a/Desktop/Stock_software/ccq_val')

try:
    # Clear any cached imports
    if 'engines.fact_authority.taxonomy_reader.taxonomy_reader' in sys.modules:
        del sys.modules['engines.fact_authority.taxonomy_reader.taxonomy_reader']
    if 'engines.fact_authority.taxonomy_reader' in sys.modules:
        del sys.modules['engines.fact_authority.taxonomy_reader']
    if 'engines.fact_authority' in sys.modules:
        del sys.modules['engines.fact_authority']
    
    from engines.fact_authority.taxonomy_reader import TaxonomyReader
    print("  ✓ TaxonomyReader imported successfully!")
    
    print("\n" + "=" * 80)
    print("✓✓✓ FIX SUCCESSFUL ✓✓✓")
    print("=" * 80)
    print("\nNow run: python tests/test_fact_authority_imports.py")
    
except Exception as e:
    print(f"  ✗ Import failed: {e}")
    print("\nRestoring backup...")
    shutil.copy2(backup, file_path)
    print("  ✓ Restored from backup")
    
    print("\n" + "=" * 80)
    print("✗ FIX FAILED")
    print("=" * 80)
    print("\nThe file needs manual editing.")
    print("Error details:")
    import traceback
    traceback.print_exc()
    sys.exit(1)