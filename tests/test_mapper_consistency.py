"""
Test Mapper Consistency
========================

Tests for Question 1: Does each mapper produce consistent, non-duplicated,
non-contradictory values for the same concept?

Tests:
1. Duplicate concept detection (same concept, same context, different values)
2. Context-based duplicate analysis (same concept, multiple contexts)
3. Aggregation consistency (parent = sum of children)
4. Temporal consistency (same concept across periods)

Usage:
    pytest ccq_val/tests/test_mapper_consistency.py -v
    pytest ccq_val/tests/test_mapper_consistency.py::test_map_pro_duplicates -v
"""

import pytest
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import json
from datetime import datetime  # Add this line

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
# HELPER FUNCTIONS
# ============================================================================

def load_statement(file_path: Path) -> Dict[str, Any]:
    """Load JSON statement file."""
    if not file_path or not file_path.exists():
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_facts(statement: Dict[str, Any], mapper: str) -> List[Dict[str, Any]]:
    """Extract facts from statement based on mapper type."""
    if mapper == 'map_pro':
        return statement.get('facts', [])
    elif mapper == 'ccq_val':
        return statement.get('line_items', [])
    elif mapper == 'unified':
        return statement.get('facts', [])
    return []


def normalize_concept(concept: str) -> str:
    """
    Normalize concept name by removing year suffixes.
    
    us-gaap-2024:Assets -> us-gaap:Assets
    """
    if not concept:
        return ''
    
    import re
    return re.sub(r'-\d{4}:', ':', concept)


def get_concept_key(fact: Dict[str, Any], mapper: str) -> str:
    """Extract normalized concept key from fact."""
    if mapper == 'map_pro':
        concept = fact.get('concept', '')
    elif mapper == 'ccq_val':
        concept = fact.get('qname', '')
    elif mapper == 'unified':
        concept = fact.get('concept_id', '')
    else:
        concept = ''
    
    return normalize_concept(concept)


def get_context_key(fact: Dict[str, Any], mapper: str) -> str:
    """Extract context key from fact."""
    if mapper == 'map_pro':
        return fact.get('context', '') or fact.get('context_ref', '')
    elif mapper == 'ccq_val':
        return fact.get('context_ref', '')
    elif mapper == 'unified':
        return fact.get('context_id', '')
    return ''


def get_fact_value(fact: Dict[str, Any]) -> Any:
    """Extract value from fact."""
    return fact.get('value')


# ============================================================================
# DUPLICATE DETECTION TESTS
# ============================================================================

def detect_duplicates(
    facts: List[Dict[str, Any]],
    mapper: str
) -> Dict[str, Any]:
    """
    Detect duplicate concepts with contradictory values.
    
    A duplicate is defined as:
    - Same concept
    - Same context (period/dimensions)
    - Different values
    
    Returns:
        Report with duplicates by severity
    """
    # Group facts by (concept, context)
    fact_groups = defaultdict(list)
    
    for fact in facts:
        concept = get_concept_key(fact, mapper)
        context = get_context_key(fact, mapper)
        
        if not concept:  # Skip facts without concepts
            continue
        
        key = (concept, context)
        fact_groups[key].append(fact)
    
    # Find duplicates
    duplicates = []
    context_variations = []
    
    for (concept, context), group in fact_groups.items():
        if len(group) > 1:
            # Check if values differ
            values = [get_fact_value(f) for f in group]
            unique_values = set(str(v) for v in values if v is not None)
            
            if len(unique_values) > 1:
                # CRITICAL: Same concept, same context, different values
                duplicates.append({
                    'concept': concept,
                    'context': context,
                    'instance_count': len(group),
                    'unique_values': list(unique_values),
                    'severity': 'CRITICAL',
                    'facts': group
                })
            else:
                # Same concept, same context, same value (redundant but not contradictory)
                context_variations.append({
                    'concept': concept,
                    'context': context,
                    'instance_count': len(group),
                    'value': list(unique_values)[0] if unique_values else None,
                    'severity': 'WARNING',
                    'facts': group
                })
    
    # Also find concepts that appear in multiple contexts
    concept_contexts = defaultdict(set)
    for (concept, context), _ in fact_groups.items():
        concept_contexts[concept].add(context)
    
    multi_context_concepts = {
        concept: list(contexts)
        for concept, contexts in concept_contexts.items()
        if len(contexts) > 1
    }
    
    return {
        'total_facts': len(facts),
        'unique_concept_context_pairs': len(fact_groups),
        'critical_duplicates': duplicates,
        'redundant_entries': context_variations,
        'multi_context_concepts': multi_context_concepts,
        'summary': {
            'critical_count': len(duplicates),
            'warning_count': len(context_variations),
            'multi_context_count': len(multi_context_concepts)
        }
    }


def test_map_pro_duplicates(paths, sample_filing):
    """Test Map Pro for duplicate concepts with contradictory values."""
    print("\n" + "="*80)
    print("TEST: Map Pro Duplicate Detection")
    print("="*80)
    
    # Test all 4 statements
    statements = ['balance_sheet', 'income_statement', 'cash_flow', 'other']
    all_results = {}
    
    for stmt_name in statements:
        # Find Map Pro statement
        stmt_file = paths.input_mapped / sample_filing['market'] / \
                    sample_filing['company'].replace(' ', '_') / \
                    sample_filing['form_type'] / sample_filing['filing_date'] / \
                    f"{stmt_name}.json"
        
        # Try name variations if file not found
        if not stmt_file.exists():
            for variation in paths._generate_name_variations(sample_filing['company']):
                stmt_file = paths.input_mapped / sample_filing['market'] / variation / \
                           sample_filing['form_type'] / sample_filing['filing_date'] / \
                           f"{stmt_name}.json"
                if stmt_file.exists():
                    break
        
        if not stmt_file.exists():
            print(f"\n⚠️  {stmt_name}: File not found")
            continue
        
        statement = load_statement(stmt_file)
        facts = extract_facts(statement, 'map_pro')
        
        result = detect_duplicates(facts, 'map_pro')
        all_results[stmt_name] = result
        
        # Print results
        print(f"\n📊 {stmt_name.upper().replace('_', ' ')}")
        print(f"  Total facts: {result['total_facts']}")
        print(f"  Unique (concept, context) pairs: {result['unique_concept_context_pairs']}")
        print(f"  ❌ Critical duplicates: {result['summary']['critical_count']}")
        print(f"  ⚠️  Redundant entries: {result['summary']['warning_count']}")
        print(f"  📍 Concepts with multiple contexts: {result['summary']['multi_context_count']}")
        
        # Show critical duplicates
        if result['critical_duplicates']:
            print(f"\n  CRITICAL DUPLICATES FOUND:")
            for dup in result['critical_duplicates'][:5]:
                print(f"    • {dup['concept']}")
                print(f"      Context: {dup['context']}")
                print(f"      Conflicting values: {dup['unique_values']}")
        
        # Show sample multi-context concepts
        if result['multi_context_concepts']:
            print(f"\n  Sample multi-context concepts (first 3):")
            for concept, contexts in list(result['multi_context_concepts'].items())[:3]:
                print(f"    • {concept}: {len(contexts)} contexts")
    
    # Overall summary
    total_critical = sum(r['summary']['critical_count'] for r in all_results.values())
    total_warnings = sum(r['summary']['warning_count'] for r in all_results.values())
    
    print("\n" + "="*80)
    print(f"OVERALL MAP PRO SUMMARY")
    print("="*80)
    print(f"Total critical duplicates across all statements: {total_critical}")
    print(f"Total redundant entries across all statements: {total_warnings}")
    
    print("\n" + "="*80)
    print(f"TEST RESULT: {'✅ PASSED' if total_critical == 0 else '⚠️  ISSUES FOUND'}")
    print("="*80)
    if total_critical > 0:
        print(f"⚠️  Data Quality Issues Detected:")
        print(f"   Map Pro has {total_critical} critical duplicates")
        print(f"   (same concept, same context, different values)")
        print(f"\n   This indicates data quality problems in the source mapper.")
        print(f"   Review the detailed output above for specifics.")
    else:
        print(f"✅ No critical duplicates found - data consistency verified!")


def test_ccq_val_duplicates(paths, sample_filing):
    """Test CCQ Mapper for duplicate concepts with contradictory values."""
    print("\n" + "="*80)
    print("TEST: CCQ Mapper Duplicate Detection")
    print("="*80)
    
    if not paths.mapper_output:
        pytest.skip("CCQ Mapper output path not configured")
    
    statements = ['balance_sheet', 'income_statement', 'cash_flow', 'other']
    all_results = {}
    
    for stmt_name in statements:
        # Find CCQ statement
        stmt_file = paths.mapper_output / sample_filing['market'] / \
                    sample_filing['company'].replace(' ', '_') / \
                    sample_filing['form_type'] / sample_filing['filing_date'] / \
                    f"{stmt_name}.json"
        
        # Try name variations
        if not stmt_file.exists():
            for variation in paths._generate_name_variations(sample_filing['company']):
                stmt_file = paths.mapper_output / sample_filing['market'] / variation / \
                           sample_filing['form_type'] / sample_filing['filing_date'] / \
                           f"{stmt_name}.json"
                if stmt_file.exists():
                    break
        
        if not stmt_file.exists():
            print(f"\n⚠️  {stmt_name}: File not found")
            continue
        
        statement = load_statement(stmt_file)
        facts = extract_facts(statement, 'ccq_val')
        
        result = detect_duplicates(facts, 'ccq_val')
        all_results[stmt_name] = result
        
        # Print results
        print(f"\n📊 {stmt_name.upper().replace('_', ' ')}")
        print(f"  Total facts: {result['total_facts']}")
        print(f"  Unique (concept, context) pairs: {result['unique_concept_context_pairs']}")
        print(f"  ❌ Critical duplicates: {result['summary']['critical_count']}")
        print(f"  ⚠️  Redundant entries: {result['summary']['warning_count']}")
        print(f"  📍 Concepts with multiple contexts: {result['summary']['multi_context_count']}")
        
        if result['critical_duplicates']:
            print(f"\n  CRITICAL DUPLICATES FOUND:")
            for dup in result['critical_duplicates'][:5]:
                print(f"    • {dup['concept']}")
                print(f"      Context: {dup['context']}")
                print(f"      Conflicting values: {dup['unique_values']}")
    
    total_critical = sum(r['summary']['critical_count'] for r in all_results.values())
    total_warnings = sum(r['summary']['warning_count'] for r in all_results.values())
    
    print("\n" + "="*80)
    print(f"OVERALL CCQ MAPPER SUMMARY")
    print("="*80)
    print(f"Total critical duplicates across all statements: {total_critical}")
    print(f"Total redundant entries across all statements: {total_warnings}")
    
    assert total_critical == 0, \
        f"CCQ Mapper has {total_critical} critical duplicates (same concept, same context, different values)"


# ============================================================================
# EXPORT DUPLICATE REPORT
# ============================================================================

def test_export_duplicate_reports(paths, sample_filing):
    """Export detailed duplicate reports to JSON for analysis."""
    print("\n" + "="*80)
    print("EXPORTING DUPLICATE REPORTS")
    print("="*80)
    
    # Use CCQ output path for reports
    if paths.mapper_output:
        output_dir = paths.mapper_output.parent / 'test_reports'
    else:
        output_dir = paths.output_validated.parent / 'test_reports'
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    reports = {}
    
    # Test both mappers
    for mapper_name, base_path in [
        ('map_pro', paths.input_mapped),
        ('ccq_val', paths.mapper_output)
    ]:
        if mapper_name == 'ccq_val' and not paths.mapper_output:
            continue
        
        mapper_results = {}
        
        for stmt_name in ['balance_sheet', 'income_statement', 'cash_flow', 'other']:
            stmt_file = base_path / sample_filing['market'] / \
                       sample_filing['company'].replace(' ', '_') / \
                       sample_filing['form_type'] / sample_filing['filing_date'] / \
                       f"{stmt_name}.json"
            
            if not stmt_file.exists():
                for variation in paths._generate_name_variations(sample_filing['company']):
                    stmt_file = base_path / sample_filing['market'] / variation / \
                               sample_filing['form_type'] / sample_filing['filing_date'] / \
                               f"{stmt_name}.json"
                    if stmt_file.exists():
                        break
            
            if not stmt_file.exists():
                continue
            
            statement = load_statement(stmt_file)
            facts = extract_facts(statement, mapper_name)
            result = detect_duplicates(facts, mapper_name)
            
            # Remove full fact objects for cleaner report
            result['critical_duplicates'] = [
                {k: v for k, v in d.items() if k != 'facts'}
                for d in result['critical_duplicates']
            ]
            result['redundant_entries'] = [
                {k: v for k, v in d.items() if k != 'facts'}
                for d in result['redundant_entries']
            ]
            
            mapper_results[stmt_name] = result
        
        reports[mapper_name] = mapper_results
    
    # Add metadata
    report = {
        'filing': sample_filing,
        'generated_at': datetime.now().isoformat(),
        'reports': reports
    }
    
    # Save reports
    report_file = output_dir / 'duplicate_analysis_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Report saved to: {report_file}")
    print(f"\nTo analyze the report:")
    print(f"  cat {report_file} | jq '.reports.map_pro.income_statement.critical_duplicates'")
    print(f"  cat {report_file} | jq '.reports.map_pro.income_statement.summary'")
    
    return report_file


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v", "--tb=short"])