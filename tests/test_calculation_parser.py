#!/usr/bin/env python3
"""
Calculation Parser Test
=======================

Tests calculation relationship extraction from XBRL calculation linkbases.

Usage:
    python3 test_calculation_parser.py
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, '/home/a/Desktop/Stock_software/ccq_val')

from engines.fact_authority.taxonomy_reader.calculation_parser import (
    CalculationParser
)
from engines.fact_authority.taxonomy_file_discoverer import (
    TaxonomyFileDiscoverer
)


def test_calculation_parsing():
    """Test calculation parsing from US-GAAP 2025."""
    
    print("\n" + "="*70)
    print("CALCULATION PARSER TEST")
    print("="*70)
    print()
    
    # Initialize
    parser = CalculationParser()
    discoverer = TaxonomyFileDiscoverer()
    
    # US-GAAP 2025 taxonomy
    taxonomy_path = Path('/mnt/map_pro/data/taxonomies/libraries/us-gaap-2025')
    
    if not taxonomy_path.exists():
        print(f"❌ Taxonomy not found: {taxonomy_path}")
        return 1
    
    print(f"Taxonomy: {taxonomy_path}")
    print()
    
    # Find calculation linkbases
    print("🔍 Finding calculation linkbases...")
    calc_files = discoverer.find_calculation_linkbases([taxonomy_path])
    print(f"   Found {len(calc_files)} calculation linkbases")
    print()
    
    # Parse all calculation linkbases
    print("📖 Parsing calculation relationships...")
    calculations = parser.parse_multiple(calc_files)
    print(f"   ✅ Parsed {len(calculations)} calculation roles")
    print()
    
    # Show statistics
    print("="*70)
    print("STATISTICS")
    print("="*70)
    print()
    
    stats = parser.get_statistics(calculations)
    
    print(f"Total roles:             {stats['total_roles']}")
    print(f"Total parent concepts:   {stats['total_parent_concepts']}")
    print(f"Total relationships:     {stats['total_relationships']}")
    print(f"  Additive (+):          {stats['additive_relationships']}")
    print(f"  Subtractive (-):       {stats['subtractive_relationships']}")
    print()
    
    # Find balance sheet calculations
    print("="*70)
    print("BALANCE SHEET CALCULATIONS")
    print("="*70)
    print()
    
    # Look for balance sheet role
    bs_role = None
    for role in calculations.keys():
        if 'StatementOfFinancialPosition' in role or 'BalanceSheet' in role:
            bs_role = role
            break
    
    if bs_role:
        print(f"Role: {bs_role}")
        print()
        
        bs_calcs = calculations[bs_role]
        
        # Show key calculations
        key_concepts = [
            'us-gaap:Assets',
            'us-gaap:AssetsCurrent',
            'us-gaap:Liabilities',
            'us-gaap:LiabilitiesAndStockholdersEquity',
        ]
        
        for concept in key_concepts:
            if concept in bs_calcs:
                data = bs_calcs[concept]
                children = data.get('children', [])
                
                if children:
                    formula = parser.get_calculation_formula(concept, children)
                    print(f"{formula}")
                    print(f"  Children: {len(children)}")
                    
                    # Show first few children
                    for child in children[:3]:
                        sign = '+' if child['weight'] > 0 else '-'
                        print(f"    {sign} {child['concept']} (weight: {child['weight']})")
                    
                    if len(children) > 3:
                        print(f"    ... and {len(children) - 3} more")
                    print()
    else:
        print("⚠️  No balance sheet role found")
        print()
    
    # Find income statement calculations
    print("="*70)
    print("INCOME STATEMENT CALCULATIONS")
    print("="*70)
    print()
    
    # Look for income statement role
    is_role = None
    for role in calculations.keys():
        if 'IncomeStatement' in role or 'StatementOfIncome' in role:
            is_role = role
            break
    
    if is_role:
        print(f"Role: {is_role}")
        print()
        
        is_calcs = calculations[is_role]
        
        # Show key calculations
        key_concepts = [
            'us-gaap:NetIncomeLoss',
            'us-gaap:Revenues',
            'us-gaap:GrossProfit',
            'us-gaap:OperatingIncomeLoss',
        ]
        
        for concept in key_concepts:
            if concept in is_calcs:
                data = is_calcs[concept]
                children = data.get('children', [])
                
                if children:
                    formula = parser.get_calculation_formula(concept, children)
                    print(f"{formula}")
                    print(f"  Children: {len(children)}")
                    
                    # Show children
                    for child in children[:5]:
                        sign = '+' if child['weight'] > 0 else '-'
                        print(f"    {sign} {child['concept']} (weight: {child['weight']})")
                    
                    if len(children) > 5:
                        print(f"    ... and {len(children) - 5} more")
                    print()
    else:
        print("⚠️  No income statement role found")
        print()
    
    # Show sample roles
    print("="*70)
    print("SAMPLE CALCULATION ROLES")
    print("="*70)
    print()
    
    for i, role in enumerate(list(calculations.keys())[:5]):
        role_calcs = calculations[role]
        print(f"{i+1}. {role}")
        print(f"   Parent concepts: {len(role_calcs)}")
        
        total_children = sum(
            len(data.get('children', []))
            for data in role_calcs.values()
        )
        print(f"   Total relationships: {total_children}")
        print()
    
    # Validation example
    print("="*70)
    print("CALCULATION VALIDATION EXAMPLE")
    print("="*70)
    print()
    
    print("Example: Validating Assets = AssetsCurrent + AssetsNoncurrent")
    print()
    
    # Mock data
    assets = 1000.0
    assets_current = 600.0
    assets_noncurrent = 400.0
    
    is_valid, diff = parser.validate_calculation(
        parent_value=assets,
        children_values=[(assets_current, 1.0), (assets_noncurrent, 1.0)],
        tolerance=0.01
    )
    
    print(f"Assets:            {assets:,.2f}")
    print(f"  AssetsCurrent:   {assets_current:,.2f} (weight: +1.0)")
    print(f"  AssetsNoncurrent: {assets_noncurrent:,.2f} (weight: +1.0)")
    print(f"Expected:          {assets_current + assets_noncurrent:,.2f}")
    print(f"Difference:        {diff:,.2f}")
    print(f"Valid:             {'✅ Yes' if is_valid else '❌ No'}")
    print()
    
    # Invalid example
    print("Example: Invalid calculation (Assets don't balance)")
    print()
    
    assets_wrong = 1000.0
    assets_current_wrong = 600.0
    assets_noncurrent_wrong = 450.0  # Too high!
    
    is_valid2, diff2 = parser.validate_calculation(
        parent_value=assets_wrong,
        children_values=[
            (assets_current_wrong, 1.0),
            (assets_noncurrent_wrong, 1.0)
        ],
        tolerance=0.01
    )
    
    print(f"Assets:            {assets_wrong:,.2f}")
    print(f"  AssetsCurrent:   {assets_current_wrong:,.2f} (weight: +1.0)")
    print(f"  AssetsNoncurrent: {assets_noncurrent_wrong:,.2f} (weight: +1.0)")
    print(f"Expected:          {assets_current_wrong + assets_noncurrent_wrong:,.2f}")
    print(f"Difference:        {diff2:,.2f}")
    print(f"Valid:             {'✅ Yes' if is_valid2 else '❌ No (exceeds tolerance)'}")
    print()
    
    # Success
    print("="*70)
    print("✅ TEST COMPLETED")
    print("="*70)
    print()
    print(f"Successfully parsed {len(calculations)} calculation roles")
    print(f"  Total relationships: {stats['total_relationships']}")
    print(f"  Additive: {stats['additive_relationships']}")
    print(f"  Subtractive: {stats['subtractive_relationships']}")
    print()
    
    return 0


def main():
    """Main entry point."""
    try:
        return test_calculation_parsing()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())