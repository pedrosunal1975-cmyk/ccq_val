#!/usr/bin/env python3
# Fix taxonomy_reader.py - remove taxonomy_file_discoverer dependency

import sys
from pathlib import Path

taxonomy_reader_file = Path('/home/a/Desktop/Stock_software/ccq_val/engines/fact_authority/taxonomy_reader/taxonomy_reader.py')

if not taxonomy_reader_file.exists():
    print(f"✗ File not found: {taxonomy_reader_file}")
    sys.exit(1)

print("=" * 80)
print("ANALYZING taxonomy_reader.py")
print("=" * 80)

# Read the file
with open(taxonomy_reader_file, 'r') as f:
    lines = f.readlines()

# Find the bad import
bad_import_lines = []
for i, line in enumerate(lines, 1):
    if 'taxonomy_file_discoverer' in line.lower():
        bad_import_lines.append((i, line.strip()))

print(f"\nFound {len(bad_import_lines)} lines with 'taxonomy_file_discoverer':")
print("-" * 80)
for line_num, line_text in bad_import_lines:
    print(f"Line {line_num}: {line_text}")

# Check for usage of TaxonomyFileDiscoverer
usage_lines = []
for i, line in enumerate(lines, 1):
    if 'TaxonomyFileDiscoverer' in line and 'import' not in line:
        usage_lines.append((i, line.strip()))

if usage_lines:
    print(f"\n⚠ TaxonomyFileDiscoverer is USED in the code ({len(usage_lines)} times):")
    print("-" * 80)
    for line_num, line_text in usage_lines:
        print(f"Line {line_num}: {line_text}")
    print("\n✗ CANNOT AUTO-FIX: TaxonomyFileDiscoverer is being used in the code")
    print("   You need to manually remove or replace these usages")
    print(f"\n   Backup created at: {taxonomy_reader_file}.backup")
else:
    print("\n✓ TaxonomyFileDiscoverer is only imported, never used!")
    print("   Safe to remove the import line")
    
    # Create backup
    import shutil
    backup_file = Path(str(taxonomy_reader_file) + '.backup')
    shutil.copy2(taxonomy_reader_file, backup_file)
    print(f"✓ Backup created: {backup_file}")
    
    # Remove the import line
    new_lines = []
    for line in lines:
        if 'taxonomy_file_discoverer' not in line.lower():
            new_lines.append(line)
    
    # Write fixed version
    with open(taxonomy_reader_file, 'w') as f:
        f.writelines(new_lines)
    
    print(f"✓ Fixed file written")
    print(f"✓ Removed {len(bad_import_lines)} import line(s)")
    
    # Test import
    print("\n" + "=" * 80)
    print("TESTING IMPORT")
    print("=" * 80)
    
    sys.path.insert(0, '/home/a/Desktop/Stock_software/ccq_val')
    try:
        from engines.fact_authority.taxonomy_reader import TaxonomyReader
        print("✓ TaxonomyReader imported successfully!")
        print("\n✓✓✓ FIX SUCCESSFUL! ✓✓✓")
    except Exception as e:
        print(f"✗ Import failed: {e}")
        print("\n⚠ Restoring backup...")
        shutil.copy2(backup_file, taxonomy_reader_file)
        print("✓ Original file restored")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("DONE")
print("=" * 80)