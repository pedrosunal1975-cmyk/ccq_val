#!/usr/bin/env python3
"""Test if fact_authority can access files at ANY depth in taxonomies"""

from pathlib import Path
from collections import defaultdict

# Your actual taxonomy path
TAXONOMY_BASE = Path('/mnt/map_pro/data/taxonomies/libraries/us-gaap-2025')

def test_depth_access():
    print("=" * 70)
    print("TAXONOMY FILE ACCESS TEST")
    print("=" * 70)
    print(f"\nBase: {TAXONOMY_BASE}\n")
    
    if not TAXONOMY_BASE.exists():
        print(f"❌ ERROR: Taxonomy base does not exist: {TAXONOMY_BASE}")
        return False
    
    # Track files by depth
    files_by_depth = defaultdict(list)
    max_depth = 0
    total_files = 0
    
    # Use rglob to find ALL files recursively
    print("Scanning for ALL files recursively...")
    for item in TAXONOMY_BASE.rglob('*'):
        if item.is_file():
            try:
                depth = len(item.relative_to(TAXONOMY_BASE).parts) - 1
                files_by_depth[depth].append(item)
                max_depth = max(max_depth, depth)
                total_files += 1
            except ValueError:
                continue
    
    print(f"\n✅ Total files found: {total_files}")
    print(f"✅ Maximum depth reached: {max_depth}")
    print(f"\n{'Depth':<10} {'Count':<10} {'Example File'}")
    print("-" * 70)
    
    for depth in sorted(files_by_depth.keys()):
        count = len(files_by_depth[depth])
        example = files_by_depth[depth][0].name if files_by_depth[depth] else "N/A"
        print(f"{depth:<10} {count:<10} {example}")
    
    # Test specific file types
    print("\n" + "=" * 70)
    print("SPECIFIC FILE TYPE TESTS")
    print("=" * 70)
    
    xml_files = list(TAXONOMY_BASE.rglob('*.xml'))
    xsd_files = list(TAXONOMY_BASE.rglob('*.xsd'))
    pre_files = list(TAXONOMY_BASE.rglob('*pre*.xml'))
    
    print(f"\n✅ XML files: {len(xml_files)}")
    print(f"✅ XSD files: {len(xsd_files)}")
    print(f"✅ Presentation linkbases (*pre*.xml): {len(pre_files)}")
    
    # Test file reading
    if xml_files:
        test_file = xml_files[0]
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
            print(f"\n✅ Can read file contents")
            print(f"   Example: {first_line[:60]}...")
        except Exception as e:
            print(f"\n❌ Cannot read file: {e}")
            return False
    
    print("\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    
    if total_files > 0 and max_depth > 0:
        print("\n✅ SUCCESS: Can access files at ANY depth!")
        print(f"   - Deepest file: depth {max_depth}")
        print(f"   - Total files: {total_files}")
        return True
    else:
        print("\n❌ FAILURE: Cannot access taxonomy files")
        return False

if __name__ == "__main__":
    success = test_depth_access()
    exit(0 if success else 1)