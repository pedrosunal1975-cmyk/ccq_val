#!/usr/bin/env python3
"""
Definition Parser Test
======================

Tests dimensional relationship extraction from XBRL definition linkbases.

Usage:
    python3 test_definition_parser.py
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, '/home/a/Desktop/Stock_software/ccq_val')

from engines.fact_authority.taxonomy_reader.definition_parser import (
    DefinitionParser
)
from engines.fact_authority.taxonomy_file_discoverer import (
    TaxonomyFileDiscoverer
)


def test_definition_parsing():
    """Test definition parsing from US-GAAP 2025."""
    
    print("\n" + "="*70)
    print("DEFINITION PARSER TEST")
    print("="*70)
    print()
    
    # Initialize
    parser = DefinitionParser()
    discoverer = TaxonomyFileDiscoverer()
    
    # US-GAAP 2025 taxonomy
    taxonomy_path = Path('/mnt/map_pro/data/taxonomies/libraries/us-gaap-2025')
    
    if not taxonomy_path.exists():
        print(f"❌ Taxonomy not found: {taxonomy_path}")
        return 1
    
    print(f"Taxonomy: {taxonomy_path}")
    print()
    
    # Find definition linkbases
    print("🔍 Finding definition linkbases...")
    def_files = discoverer.find_definition_linkbases([taxonomy_path])
    print(f"   Found {len(def_files)} definition linkbases")
    print()
    
    # Parse all definition linkbases
    print("📖 Parsing dimensional relationships...")
    dimensions = parser.parse_multiple(def_files)
    print(f"   ✅ Parsed dimensional structures")
    print()
    
    # Show statistics
    print("="*70)
    print("STATISTICS")
    print("="*70)
    print()
    
    stats = parser.get_statistics(dimensions)
    
    print(f"Total axes:              {stats['total_axes']}")
    print(f"Total hypercubes:        {stats['total_hypercubes']}")
    print(f"Total members:           {stats['total_members']}")
    print(f"Axes with members:       {stats['axes_with_members']}")
    print()
    
    # Show sample axes
    print("="*70)
    print("SAMPLE AXES (DIMENSIONS)")
    print("="*70)
    print()
    
    axes = dimensions.get('axes', {})
    sample_axes = list(axes.keys())[:10]
    
    for axis in sample_axes:
        axis_data = axes[axis]
        domain = axis_data.get('domain', 'N/A')
        members = axis_data.get('members', [])
        
        # Simplify names
        if ':' in axis:
            simple_axis = axis.split(':')[1]
        else:
            simple_axis = axis
        
        print(f"{simple_axis}:")
        print(f"  Domain: {domain}")
        print(f"  Members: {len(members)}")
        
        if members:
            # Show first few members
            for member in members[:3]:
                if ':' in member:
                    simple_member = member.split(':')[1]
                else:
                    simple_member = member
                print(f"    - {simple_member}")
            
            if len(members) > 3:
                print(f"    ... and {len(members) - 3} more")
        print()
    
    # Look for geographic axis
    print("="*70)
    print("GEOGRAPHIC DIMENSION (Detailed)")
    print("="*70)
    print()
    
    geo_axis = None
    for axis in axes.keys():
        if 'Geograph' in axis or 'Geographic' in axis:
            geo_axis = axis
            break
    
    if geo_axis:
        axis_data = axes[geo_axis]
        print(f"Axis: {geo_axis}")
        print(f"Domain: {axis_data.get('domain', 'N/A')}")
        print(f"Members ({len(axis_data.get('members', []))}):")
        
        for member in axis_data.get('members', []):
            print(f"  - {member}")
        print()
    else:
        print("⚠️  No geographic axis found")
        print()
    
    # Look for segment axis
    print("="*70)
    print("BUSINESS SEGMENT DIMENSION")
    print("="*70)
    print()
    
    seg_axis = None
    for axis in axes.keys():
        if 'Segment' in axis or 'segment' in axis:
            seg_axis = axis
            break
    
    if seg_axis:
        axis_data = axes[seg_axis]
        print(f"Axis: {seg_axis}")
        print(f"Domain: {axis_data.get('domain', 'N/A')}")
        print(f"Members ({len(axis_data.get('members', []))}):")
        
        for member in axis_data.get('members', [])[:10]:
            print(f"  - {member}")
        
        if len(axis_data.get('members', [])) > 10:
            print(f"  ... and {len(axis_data.get('members', [])) - 10} more")
        print()
    else:
        print("⚠️  No segment axis found")
        print()
    
    # Show sample hypercubes
    print("="*70)
    print("SAMPLE HYPERCUBES (TABLES)")
    print("="*70)
    print()
    
    hypercubes = dimensions.get('hypercubes', {})
    sample_hypercubes = list(hypercubes.keys())[:5]
    
    for hypercube in sample_hypercubes:
        hypercube_data = hypercubes[hypercube]
        dims = hypercube_data.get('dimensions', [])
        items = hypercube_data.get('primary_items', [])
        
        # Simplify name
        if ':' in hypercube:
            simple_hypercube = hypercube.split(':')[1]
        else:
            simple_hypercube = hypercube
        
        print(f"{simple_hypercube}:")
        print(f"  Dimensions: {len(dims)}")
        
        for dim in dims:
            if ':' in dim:
                simple_dim = dim.split(':')[1]
            else:
                simple_dim = dim
            print(f"    - {simple_dim}")
        
        print(f"  Primary items: {len(items)}")
        
        for item in items[:3]:
            if ':' in item:
                simple_item = item.split(':')[1]
            else:
                simple_item = item
            print(f"    - {simple_item}")
        
        if len(items) > 3:
            print(f"    ... and {len(items) - 3} more")
        print()
    
    # Usage example
    print("="*70)
    print("DIMENSIONAL DATA EXAMPLE")
    print("="*70)
    print()
    
    print("Example: Revenue by Geography")
    print()
    print("Concept: us-gaap:Revenues")
    print("Dimension: us-gaap:StatementGeographicalAxis")
    print()
    print("Breakdown:")
    print("  Revenues [Geographic=US]      = $100M")
    print("  Revenues [Geographic=Europe]  = $75M")
    print("  Revenues [Geographic=Asia]    = $50M")
    print("  ----------------------------------------")
    print("  Revenues [Geographic=Consolidated] = $225M")
    print()
    print("This dimensional structure is defined in definition linkbases!")
    print()
    
    # Validation checks
    print("="*70)
    print("VALIDATION CHECKS")
    print("="*70)
    print()
    
    # Check 1: All axes have domains
    axes_without_domain = [
        axis for axis, data in axes.items()
        if not data.get('domain')
    ]
    
    if axes_without_domain:
        print(f"⚠️  Found {len(axes_without_domain)} axes without domain")
        print(f"   Examples: {axes_without_domain[:3]}")
    else:
        print(f"✅ All axes have domains")
    
    print()
    
    # Check 2: Axes with members
    axes_with_members = [
        axis for axis, data in axes.items()
        if data.get('members')
    ]
    
    print(f"✅ {len(axes_with_members)} axes have defined members")
    print(f"   ({len(axes_with_members) / len(axes) * 100:.1f}% of all axes)")
    
    print()
    
    # Success
    print("="*70)
    print("✅ TEST COMPLETED")
    print("="*70)
    print()
    print(f"Successfully parsed dimensional structures:")
    print(f"  Axes: {stats['total_axes']}")
    print(f"  Hypercubes: {stats['total_hypercubes']}")
    print(f"  Total members: {stats['total_members']}")
    print()
    
    return 0


def main():
    """Main entry point."""
    try:
        return test_definition_parsing()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())