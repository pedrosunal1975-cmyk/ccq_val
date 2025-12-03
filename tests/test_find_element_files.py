#!/usr/bin/env python3
"""
Test: Find XSD Files with Element Definitions
==============================================

Scans all XSD files to find which ones have actual element definitions.

Run from ccq_val root:
    python3 tests/test_find_element_files.py
"""

import sys
from pathlib import Path
import xml.etree.ElementTree as ET

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def scan_xsd_files():
    """Scan all XSD files and count elements in each."""
    
    base_dir = Path('/mnt/map_pro/data/taxonomies/libraries/us-gaap-2024/us-gaap-2024')
    
    print("=" * 70)
    print("SCANNING ALL XSD FILES FOR ELEMENT DEFINITIONS")
    print("=" * 70)
    print(f"\nBase directory: {base_dir}")
    
    if not base_dir.exists():
        print("ERROR: Directory not found!")
        return
    
    # Find all XSD files
    xsd_files = list(base_dir.rglob('*.xsd'))
    print(f"Total XSD files found: {len(xsd_files)}")
    
    NAMESPACES = {
        'xsd': 'http://www.w3.org/2001/XMLSchema',
    }
    
    # Count elements in each file
    file_counts = []
    
    print("\nScanning files...")
    for xsd_file in xsd_files:
        try:
            tree = ET.parse(xsd_file)
            root = tree.getroot()
            elements = root.findall('.//xsd:element', NAMESPACES)
            
            if len(elements) > 0:
                file_counts.append((xsd_file.name, len(elements), xsd_file))
                
        except Exception as e:
            pass  # Skip files that can't be parsed
    
    # Sort by element count (descending)
    file_counts.sort(key=lambda x: x[1], reverse=True)
    
    print("\n" + "=" * 70)
    print(f"FILES WITH ELEMENTS: {len(file_counts)} out of {len(xsd_files)}")
    print("=" * 70)
    
    if file_counts:
        print("\nTop 20 files by element count:")
        print("-" * 70)
        
        total_elements = 0
        for i, (filename, count, filepath) in enumerate(file_counts[:20]):
            total_elements += count
            print(f"{i+1:3}. {filename:50} {count:6} elements")
        
        print("-" * 70)
        print(f"Total elements in top 20 files: {total_elements:,}")
        
        # Calculate total across ALL files with elements
        all_elements = sum(count for _, count, _ in file_counts)
        print(f"Total elements in ALL {len(file_counts)} files: {all_elements:,}")
        
        # Show file patterns
        print("\n" + "=" * 70)
        print("FILE PATTERNS")
        print("=" * 70)
        
        # Check if main file exists
        main_file = base_dir / 'us-gaap-2024.xsd'
        if main_file.exists():
            print(f"\n✓ Main file exists: {main_file.name}")
            try:
                tree = ET.parse(main_file)
                root = tree.getroot()
                elements = root.findall('.//xsd:element', NAMESPACES)
                print(f"  Elements in main file: {len(elements)}")
            except:
                print(f"  Could not parse main file")
        
        # Check for elts directory (common pattern)
        elts_dir = base_dir / 'elts'
        if elts_dir.exists():
            print(f"\n✓ Elements directory exists: elts/")
            elts_files = list(elts_dir.glob('*.xsd'))
            print(f"  XSD files in elts/: {len(elts_files)}")
        
        # Show directory distribution
        print("\n" + "=" * 70)
        print("DIRECTORY DISTRIBUTION")
        print("=" * 70)
        
        dir_counts = {}
        for filename, count, filepath in file_counts:
            dir_name = filepath.parent.name
            if dir_name not in dir_counts:
                dir_counts[dir_name] = {'files': 0, 'elements': 0}
            dir_counts[dir_name]['files'] += 1
            dir_counts[dir_name]['elements'] += count
        
        print("\nElements by directory:")
        for dir_name in sorted(dir_counts.keys(), key=lambda x: dir_counts[x]['elements'], reverse=True):
            info = dir_counts[dir_name]
            print(f"  {dir_name:20} {info['files']:3} files, {info['elements']:6,} elements")
    
    else:
        print("\n✗ NO FILES WITH ELEMENTS FOUND!")
        print("This indicates a parsing or structure issue.")


if __name__ == '__main__':
    scan_xsd_files()