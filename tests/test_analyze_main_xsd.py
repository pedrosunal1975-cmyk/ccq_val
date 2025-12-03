#!/usr/bin/env python3
"""
Test: Deep Analysis of us-gaap-2024.xsd
========================================

Analyzes the main taxonomy file to understand why elements aren't being extracted.

Run from ccq_val root:
    python3 tests/test_analyze_main_xsd.py
"""

import sys
from pathlib import Path
import xml.etree.ElementTree as ET

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def analyze_main_file():
    """Deep analysis of us-gaap-2024.xsd file."""
    
    # Try to find the main file
    possible_paths = [
        Path('/mnt/map_pro/data/taxonomies/libraries/us-gaap-2024/us-gaap-2024/elts/us-gaap-2024.xsd'),
        Path('/mnt/map_pro/data/taxonomies/libraries/us-gaap-2024/us-gaap-2024/us-gaap-2024.xsd'),
    ]
    
    main_file = None
    for path in possible_paths:
        if path.exists():
            main_file = path
            break
    
    if not main_file:
        print("ERROR: Could not find us-gaap-2024.xsd")
        return
    
    print("=" * 70)
    print("DEEP ANALYSIS OF us-gaap-2024.xsd")
    print("=" * 70)
    print(f"\nFile: {main_file}")
    print(f"Size: {main_file.stat().st_size:,} bytes")
    
    print("\n" + "-" * 70)
    print("PARSING XML")
    print("-" * 70)
    
    try:
        tree = ET.parse(main_file)
        root = tree.getroot()
        
        print("\n✓ XML parsed successfully")
        print(f"  Root tag: {root.tag}")
        
        # Show all root attributes
        print("\n  Root attributes:")
        for key, value in root.attrib.items():
            print(f"    {key}: {value}")
        
    except Exception as e:
        print(f"\n✗ Parse error: {e}")
        return
    
    print("\n" + "-" * 70)
    print("NAMESPACE ANALYSIS")
    print("-" * 70)
    
    # Get all unique namespaces used in the document
    all_tags = set(elem.tag for elem in root.iter())
    namespaces_used = set()
    
    for tag in all_tags:
        if '}' in tag:
            ns = tag.split('}')[0] + '}'
            namespaces_used.add(ns)
    
    print(f"\nUnique namespaces in document: {len(namespaces_used)}")
    for ns in sorted(namespaces_used):
        print(f"  {ns}")
    
    print("\n" + "-" * 70)
    print("SEARCHING FOR ELEMENTS - METHOD 1: XPath with namespace")
    print("-" * 70)
    
    NAMESPACES = {
        'xsd': 'http://www.w3.org/2001/XMLSchema',
        'xbrli': 'http://www.xbrl.org/2003/instance',
    }
    
    elements = root.findall('.//xsd:element', NAMESPACES)
    print(f"\nElements found: {len(elements)}")
    
    if elements:
        print("\nFirst 10 elements:")
        for i, elem in enumerate(elements[:10]):
            name = elem.get('name', 'NO NAME')
            elem_type = elem.get('type', 'NO TYPE')
            print(f"  {i+1}. {name} (type: {elem_type})")
    
    print("\n" + "-" * 70)
    print("SEARCHING FOR ELEMENTS - METHOD 2: Direct namespace")
    print("-" * 70)
    
    xsd_ns = '{http://www.w3.org/2001/XMLSchema}'
    element_tag = f'{xsd_ns}element'
    
    direct_elements = list(root.iter(element_tag))
    print(f"\nElements found with iter(): {len(direct_elements)}")
    
    if direct_elements:
        print("\nFirst 10 elements:")
        for i, elem in enumerate(direct_elements[:10]):
            name = elem.get('name', 'NO NAME')
            elem_type = elem.get('type', 'NO TYPE')
            balance = elem.get('{http://www.xbrl.org/2003/instance}balance')
            period = elem.get('{http://www.xbrl.org/2003/instance}periodType')
            
            print(f"  {i+1}. {name}")
            print(f"      type: {elem_type}")
            if balance:
                print(f"      balance: {balance}")
            if period:
                print(f"      period: {period}")
    
    print("\n" + "-" * 70)
    print("ELEMENT STRUCTURE ANALYSIS")
    print("-" * 70)
    
    if direct_elements:
        # Analyze first element in detail
        first_elem = direct_elements[0]
        
        print("\nFirst element detailed view:")
        print(f"  Tag: {first_elem.tag}")
        print(f"  Attributes:")
        for key, value in first_elem.attrib.items():
            print(f"    {key}: {value}")
        
        print(f"\n  Children: {len(list(first_elem))}")
        for child in list(first_elem)[:3]:
            print(f"    {child.tag}: {child.attrib}")
    
    print("\n" + "-" * 70)
    print("STATISTICS")
    print("-" * 70)
    
    # Count elements with names
    elements_with_names = [e for e in direct_elements if e.get('name')]
    
    # Count elements with xbrli attributes
    elements_with_balance = [e for e in direct_elements if e.get('{http://www.xbrl.org/2003/instance}balance')]
    elements_with_period = [e for e in direct_elements if e.get('{http://www.xbrl.org/2003/instance}periodType')]
    
    print(f"\nTotal elements: {len(direct_elements)}")
    print(f"Elements with 'name' attribute: {len(elements_with_names)}")
    print(f"Elements with 'balance' attribute: {len(elements_with_balance)}")
    print(f"Elements with 'periodType' attribute: {len(elements_with_period)}")
    
    # Count elements with substitutionGroup
    subst_groups = {}
    for elem in direct_elements:
        sg = elem.get('substitutionGroup')
        if sg:
            subst_groups[sg] = subst_groups.get(sg, 0) + 1
    
    if subst_groups:
        print(f"\nSubstitution groups:")
        for sg, count in sorted(subst_groups.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {sg}: {count}")
    
    print("\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    
    if len(direct_elements) > 0:
        print(f"\n✓ File contains {len(direct_elements)} element definitions")
        print(f"✓ Parsing method works (use root.iter() instead of findall())")
        
        if len(elements_with_names) == len(direct_elements):
            print(f"✓ All elements have 'name' attribute")
        else:
            print(f"⚠ Only {len(elements_with_names)} elements have 'name' attribute")
        
        print("\nRECOMMENDATION:")
        print("  Change taxonomy_loader.py line ~143:")
        print("  FROM: root.findall('.//xsd:element', NAMESPACES)")
        print("  TO:   root.iter('{http://www.w3.org/2001/XMLSchema}element')")
    else:
        print("\n✗ No elements found - file structure unexpected")


if __name__ == '__main__':
    analyze_main_file()