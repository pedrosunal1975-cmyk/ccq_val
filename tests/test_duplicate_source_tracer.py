"""
Duplicate Source Tracer
=======================

This test answers THE critical question:
Are the 12 critical duplicates in the SOURCE XBRL or created by Map Pro?

Tests:
1. Load parsed facts (raw XBRL source)
2. Search for the exact duplicate patterns found in Map Pro output
3. Determine if duplicates exist in source or are mapper-generated

Key Duplicates to Trace:
- NetIncomeLoss: -2100000000 vs -2104701000 (2024)
- NetIncomeLoss: -1368833000 vs -1400000000 (2023)
- AllocatedShareBasedCompensationExpense: 70341000 vs 70300000 (2024)
- DeferredTaxAssetsValuationAllowance: 1110852000 vs 1100000000 (2024)

Usage:
    pytest ccq_val/tests/test_duplicate_source_tracer.py -v -s
"""

import pytest
from pathlib import Path
from typing import Dict, List, Any, Set
from collections import defaultdict
import json
from datetime import datetime

from core.data_paths import CCQPaths, initialize_paths


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def paths():
    """Initialize CCQPaths from config."""
    from core.config_loader import ConfigLoader
    
    config_loader = ConfigLoader()
    config = config_loader.get_all()
    return initialize_paths(config)


@pytest.fixture
def sample_filing():
    """Sample filing coordinates for testing."""
    return {
        'market': 'sec',
        'company': 'PLUG POWER INC',
        'form_type': '10-K',
        'filing_date': '2025-03-03'
    }


# ============================================================================
# CRITICAL DUPLICATES TO TRACE
# ============================================================================

CRITICAL_DUPLICATES = [
    {
        'concept': 'us-gaap:NetIncomeLoss',
        'context': 'Duration_1_1_2024_To_12_31_2024_HuIXPDtafEu4SnZWVFbSRQ',
        'expected_values': ['-2100000000', '-2104701000'],
        'description': 'Net Income Loss 2024 - $4.7M variance'
    },
    {
        'concept': 'us-gaap:NetIncomeLoss',
        'context': 'Duration_1_1_2023_To_12_31_2023_fV09bw9ovEO-HOMBYUdEng',
        'expected_values': ['-1368833000', '-1400000000'],
        'description': 'Net Income Loss 2023 - $31.2M variance'
    },
    {
        'concept': 'us-gaap:AllocatedShareBasedCompensationExpense',
        'context': 'Duration_1_1_2024_To_12_31_2024_us-gaap_PlanNameAxis_plug_StockIncentivePlan2011And2021Member_4uKjHe1ChUG3IzpO-dHobg',
        'expected_values': ['70341000', '70300000'],
        'description': 'Share-Based Comp 2024 - $41K variance'
    },
    {
        'concept': 'us-gaap:DeferredTaxAssetsValuationAllowance',
        'context': 'As_Of_12_31_2024_n8h5jflTb0anKQ9Z8CqXwg',
        'expected_values': ['1110852000', '1100000000'],
        'description': 'Tax Valuation Allowance 2024 - $10.9M variance'
    },
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_parsed_facts(paths: CCQPaths, filing: Dict[str, str]) -> List[Dict]:
    """Load parsed facts from source XBRL."""
    facts_file = paths.find_parsed_facts_filing(
        filing['market'],
        filing['company'],
        filing['form_type'],
        filing['filing_date']
    )
    
    if not facts_file:
        return []
    
    facts_path = Path(facts_file)
    if not facts_path.exists():
        return []
    
    with open(facts_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get('facts', [])


def find_duplicates_in_parsed_facts(
    facts: List[Dict],
    concept: str,
    context: str
) -> List[Dict]:
    """
    Find all facts matching the concept and context in parsed facts.
    
    Returns list of matching facts with their values.
    """
    matches = []
    
    for fact in facts:
        fact_concept = fact.get('concept_qname', '')
        fact_context = fact.get('context_ref', '')
        
        if fact_concept == concept and fact_context == context:
            matches.append({
                'fact_id': fact.get('fact_id'),
                'concept': fact_concept,
                'context': fact_context,
                'value': fact.get('fact_value'),
                'unit': fact.get('unit_ref'),
                'decimals': fact.get('decimals')
            })
    
    return matches


def analyze_duplicate_source(duplicate_spec: Dict, parsed_facts: List[Dict]) -> Dict[str, Any]:
    """
    Analyze a specific duplicate to determine if it exists in source.
    
    Returns detailed analysis of the duplicate.
    """
    concept = duplicate_spec['concept']
    context = duplicate_spec['context']
    expected_values = set(duplicate_spec['expected_values'])
    
    # Find all matching facts in parsed data
    matches = find_duplicates_in_parsed_facts(parsed_facts, concept, context)
    
    # Extract actual values
    actual_values = [str(m['value']) for m in matches if m['value'] is not None]
    actual_values_set = set(actual_values)
    
    # Determine if duplicate exists in source
    has_duplicate_in_source = len(matches) > 1
    has_conflicting_values = len(actual_values_set) > 1
    
    # Check if expected values match
    expected_found = expected_values & actual_values_set
    
    return {
        'concept': concept,
        'context': context,
        'description': duplicate_spec['description'],
        'matches_found': len(matches),
        'unique_values_found': len(actual_values_set),
        'actual_values': list(actual_values_set),
        'expected_values': list(expected_values),
        'expected_values_found': list(expected_found),
        'has_duplicate_in_source': has_duplicate_in_source,
        'has_conflicting_values': has_conflicting_values,
        'verdict': determine_verdict(has_duplicate_in_source, has_conflicting_values, expected_found, expected_values),
        'all_matches': matches
    }


def determine_verdict(
    has_duplicate: bool,
    has_conflict: bool,
    expected_found: Set[str],
    expected_values: Set[str]
) -> str:
    """Determine the verdict on duplicate source."""
    if not has_duplicate:
        return 'NO_DUPLICATE_IN_SOURCE - Map Pro may be creating it'
    
    if has_conflict:
        if expected_found == expected_values:
            return 'CONFIRMED_SOURCE_DUPLICATE - XBRL filing has conflicting values'
        else:
            return 'SOURCE_DUPLICATE_DIFFERENT_VALUES - Duplicate exists but values differ from Map Pro'
    
    return 'SOURCE_DUPLICATE_SAME_VALUE - Redundant but not conflicting'


# ============================================================================
# MAIN TEST
# ============================================================================

def test_trace_critical_duplicates_to_source(paths, sample_filing):
    """
    THE DEFINITIVE TEST: Trace all 12 critical duplicates to their source.
    
    This will answer: Are duplicates in the XBRL or created by Map Pro?
    """
    print("\n" + "="*80)
    print("DUPLICATE SOURCE TRACER - THE DEFINITIVE ANSWER")
    print("="*80)
    
    # Load parsed facts (raw XBRL)
    print(f"\n📖 Loading parsed facts from source XBRL...")
    parsed_facts = load_parsed_facts(paths, sample_filing)
    print(f"  Total parsed facts: {len(parsed_facts)}")
    
    if not parsed_facts:
        pytest.skip("Parsed facts not found")
    
    # Analyze each critical duplicate
    print(f"\n🔬 Analyzing {len(CRITICAL_DUPLICATES)} critical duplicates...")
    
    results = []
    verdicts = defaultdict(int)
    
    for i, dup_spec in enumerate(CRITICAL_DUPLICATES, 1):
        print(f"\n{'='*80}")
        print(f"DUPLICATE #{i}: {dup_spec['description']}")
        print(f"{'='*80}")
        print(f"Concept: {dup_spec['concept']}")
        print(f"Context: {dup_spec['context'][:60]}...")
        print(f"Expected values: {dup_spec['expected_values']}")
        
        # Analyze this duplicate
        result = analyze_duplicate_source(dup_spec, parsed_facts)
        results.append(result)
        
        # Print findings
        print(f"\n🔍 FINDINGS:")
        print(f"  Matches found in source: {result['matches_found']}")
        print(f"  Unique values in source: {result['unique_values_found']}")
        print(f"  Actual values: {result['actual_values']}")
        print(f"  Expected values found: {result['expected_values_found']}")
        
        # Print verdict
        verdict = result['verdict']
        verdicts[verdict] += 1
        
        print(f"\n⚖️  VERDICT: {verdict}")
        
        # Show details if it's a confirmed source duplicate
        if 'CONFIRMED_SOURCE_DUPLICATE' in verdict:
            print(f"\n  ✅ This duplicate EXISTS in the source XBRL filing!")
            print(f"  📋 Details of duplicate facts:")
            for match in result['all_matches'][:3]:  # Show first 3
                print(f"    - Fact ID: {match['fact_id']}")
                print(f"      Value: {match['value']}")
                print(f"      Decimals: {match['decimals']}")
    
    # Overall summary
    print("\n" + "="*80)
    print("OVERALL SUMMARY")
    print("="*80)
    
    print(f"\n📊 Verdict Breakdown:")
    for verdict, count in sorted(verdicts.items(), key=lambda x: -x[1]):
        print(f"  {verdict}: {count} duplicates")
    
    # Calculate key statistics
    source_duplicates = sum(1 for r in results if r['has_duplicate_in_source'])
    conflicting_duplicates = sum(1 for r in results if r['has_conflicting_values'])
    
    print(f"\n📈 Key Statistics:")
    print(f"  Duplicates traced: {len(results)}")
    print(f"  Found in source XBRL: {source_duplicates} ({source_duplicates/len(results)*100:.1f}%)")
    print(f"  With conflicting values: {conflicting_duplicates} ({conflicting_duplicates/len(results)*100:.1f}%)")
    
    # Final verdict
    print("\n" + "="*80)
    print("🎯 FINAL VERDICT")
    print("="*80)
    
    if source_duplicates == len(results):
        print("✅ ALL DUPLICATES EXIST IN THE SOURCE XBRL FILING")
        print("   Map Pro is CORRECTLY preserving the source data.")
        print("   These are DATA QUALITY ISSUES in the XBRL filing itself.")
    elif source_duplicates > 0:
        print(f"⚠️  MIXED RESULTS: {source_duplicates}/{len(results)} duplicates in source")
        print(f"   Some duplicates are from the XBRL, others may be Map Pro artifacts.")
    else:
        print("🚨 NO DUPLICATES FOUND IN SOURCE XBRL")
        print("   Map Pro may be creating these duplicates during processing.")
    
    print("\n" + "="*80)
    
    return results


def test_export_duplicate_source_report(paths, sample_filing):
    """Export detailed duplicate source analysis to JSON."""
    print("\n" + "="*80)
    print("EXPORTING DUPLICATE SOURCE REPORT")
    print("="*80)
    
    # Determine output directory
    if paths.mapper_output:
        output_dir = paths.mapper_output.parent / 'test_reports'
    else:
        output_dir = Path('/mnt/map_pro/data/test_reports')
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load parsed facts
    parsed_facts = load_parsed_facts(paths, sample_filing)
    
    if not parsed_facts:
        pytest.skip("Parsed facts not found")
    
    # Analyze all duplicates
    results = []
    for dup_spec in CRITICAL_DUPLICATES:
        result = analyze_duplicate_source(dup_spec, parsed_facts)
        # Remove verbose all_matches for cleaner report
        result['sample_matches'] = result['all_matches'][:3]
        del result['all_matches']
        results.append(result)
    
    # Build report
    report = {
        'filing': sample_filing,
        'parsed_facts_count': len(parsed_facts),
        'duplicates_analyzed': len(results),
        'results': results,
        'summary': {
            'source_duplicates': sum(1 for r in results if r['has_duplicate_in_source']),
            'conflicting_duplicates': sum(1 for r in results if r['has_conflicting_values']),
            'verdicts': {}
        },
        'generated_at': datetime.now().isoformat()
    }
    
    # Count verdicts
    for result in results:
        verdict = result['verdict']
        report['summary']['verdicts'][verdict] = report['summary']['verdicts'].get(verdict, 0) + 1
    
    # Save report
    report_file = output_dir / 'duplicate_source_analysis.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Report saved to: {report_file}")
    print(f"\nTo analyze the report:")
    print(f"  cat {report_file} | jq '.summary'")
    print(f"  cat {report_file} | jq '.results[] | select(.verdict | contains(\"CONFIRMED\"))'")
    
    return report_file


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])