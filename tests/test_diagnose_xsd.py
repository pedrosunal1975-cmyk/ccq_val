#!/usr/bin/env python3
"""
Test: Diagnose XSD File Contents
=================================

Analyzes taxonomy XSD files to understand why concepts aren't loading.

Run from ccq_val root:
    python3 tests/test_diagnose_xsd.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import xml.etree.ElementTree as ET


def test_xsd_structure():
    """Analyze XSD file structure to diagnose parsing issues."""
    
    # Sample XSD file from your structure
    xsd_file = Path('/mnt/map_pro/data/taxonomies/libraries/us-gaap-2024/us-gaap-2024/stm/us-gaap-stm-sfp-cls-2024.xsd')
    
    print("=" * 70)
    print("XSD FILE DIAGNOSTIC TEST")
    print("=" * 70)
    print(f"\nFile: {xsd_file}")
    print(f"Exists: {xsd_file.exists()}")
    
    if not xsd_file.exists():
        print("\nERROR: File not found!")
        print("Trying main taxonomy directory instead...")
        
        # Try main us-gaap file
        xsd_file = Path('/mnt/map_pro/data/taxonomies/libraries/us-gaap-2024/us-gaap-2024/us-gaap-2024.xsd')
        print(f"\nAlternate file: {xsd_file}")
        print(f"Exists: {xsd_file.exists()}")
        
        if not xsd_file.exists():
            print("\nERROR: Neither file found!")
            return False
    
    print("\n" + "-" * 70)
    print("PARSING XML")
    print("-" * 70)
    
    try:
        tree = ET.parse(xsd_file)
        root = tree.getroot()
        
        print(f"\n✓ XML parsed successfully")
        print(f"  Root tag: {root.tag}")
        print(f"  Root attributes: {list(root.attrib.keys())}")
        
        # Get target namespace
        target_ns = root.get('targetNamespace', 'Not found')
        print(f"  Target namespace: {target_ns}")
        
    except ET.ParseError as e:
        print(f"\n✗ XML parsing failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False
    
    print("\n" + "-" * 70)
    print("SEARCHING FOR ELEMENTS")
    print("-" * 70)
    
    # Define namespaces
    NAMESPACES = {
        'xsd': 'http://www.w3.org/2001/XMLSchema',
        'xbrli': 'http://www.xbrl.org/2003/instance',
    }
    
    # Method 1: Search with namespace
    print("\n[Method 1] Using XPath with xsd namespace:")
    elements = root.findall('.//xsd:element', NAMESPACES)
    print(f"  Found: {len(elements)} elements")
    
    if elements:
        print("\n  First 5 elements:")
        for i, elem in enumerate(elements[:5]):
            name = elem.get('name', 'NO NAME')
            elem_type = elem.get('type', 'NO TYPE')
            balance = elem.get('{http://www.xbrl.org/2003/instance}balance', 'none')
            period = elem.get('{http://www.xbrl.org/2003/instance}periodType', 'none')
            print(f"    {i+1}. name='{name}'")
            print(f"       type='{elem_type}'")
            print(f"       balance='{balance}' period='{period}'")
    
    # Method 2: Check all tags
    print("\n[Method 2] Analyzing all XML elements:")
    all_elements = list(root.iter())
    print(f"  Total elements in file: {len(all_elements)}")
    
    # Find unique tags
    unique_tags = set(elem.tag for elem in all_elements)
    print(f"  Unique tags: {len(unique_tags)}")
    
    # Show tags that contain 'element'
    element_tags = [tag for tag in unique_tags if 'element' in tag.lower()]
    if element_tags:
        print(f"\n  Tags containing 'element': {len(element_tags)}")
        for tag in element_tags[:5]:
            print(f"    - {tag}")
    
    # Method 3: Direct namespace search
    print("\n[Method 3] Direct namespace search:")
    xsd_ns = '{http://www.w3.org/2001/XMLSchema}'
    element_tag = f'{xsd_ns}element'
    
    direct_elements = root.findall(f'.//{element_tag}')
    print(f"  Found with direct namespace: {len(direct_elements)}")
    
    if direct_elements and not elements:
        print("\n  ⚠ WARNING: Direct search works but XPath doesn't!")
        print("  This suggests namespace registration issue.")
    
    print("\n" + "-" * 70)
    print("DIAGNOSIS")
    print("-" * 70)
    
    if len(elements) > 0:
        print("\n✓ SUCCESS: Elements found using XPath")
        print(f"  Parser should work correctly")
        return True
    elif len(direct_elements) > 0:
        print("\n⚠ ISSUE: Elements exist but XPath namespace not working")
        print("  Problem: Namespace registration in NAMESPACES dict")
        print("  Solution: Use direct namespace strings in findall()")
        return False
    else:
        print("\n✗ PROBLEM: No element definitions in this file")
        print("  This might be a linkbase or import-only file")
        print("  Solution: Check main us-gaap-2024.xsd file instead")
        return False


def test_multiple_files():
    """Test multiple XSD files to find which ones have elements."""
    
    print("\n" + "=" * 70)
    print("TESTING MULTIPLE XSD FILES")
    print("=" * 70)
    
    base_dir = Path('/mnt/map_pro/data/taxonomies/libraries/us-gaap-2024/us-gaap-2024')
    
    if not base_dir.exists():
        print(f"\nDirectory not found: {base_dir}")
        return
    
    # Find all XSD files
    xsd_files = list(base_dir.rglob('*.xsd'))
    print(f"\nFound {len(xsd_files)} XSD files")
    
    # Test first 5 files
    print("\nTesting first 5 files:")
    
    NAMESPACES = {
        'xsd': 'http://www.w3.org/2001/XMLSchema',
    }
    
    for i, xsd_file in enumerate(xsd_files[:5]):
        try:
            tree = ET.parse(xsd_file)
            root = tree.getroot()
            elements = root.findall('.//xsd:element', NAMESPACES)
            
            print(f"\n  {i+1}. {xsd_file.name}")
            print(f"     Elements: {len(elements)}")
            
        except Exception as e:
            print(f"\n  {i+1}. {xsd_file.name}")
            print(f"     Error: {e}")


def main():
    """Run all diagnostic tests."""
    
    print("\n")
    success = test_xsd_structure()
    
    print("\n")
    test_multiple_files()
    
    print("\n" + "=" * 70)
    if success:
        print("✓ DIAGNOSIS COMPLETE: Parser should work")
    else:
        print("✗ DIAGNOSIS COMPLETE: Issues found (see above)")
    print("=" * 70)
    print("\n")
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())