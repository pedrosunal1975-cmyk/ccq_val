"""
Test Coverage Analysis
======================

Tests for Question 2: What facts from parsed raw data are missed (if any)?

Tests:
1. Load all parsed facts (ground truth)
2. Load mapped facts from Map Pro
3. Load mapped facts from CCQ Mapper
4. Compute coverage:
   - Facts mapped by both
   - Facts mapped only by Map Pro
   - Facts mapped only by CCQ
   - Facts missed by both (THE GAP!)
5. Analyze patterns in unmapped facts

Usage:
    pytest ccq_val/tests/test_coverage_analysis.py -v
"""

import pytest
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
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
# HELPER FUNCTIONS
# ============================================================================

def load_parsed_facts(paths: CCQPaths, filing: Dict[str, str]) -> Tuple[List[Dict], Dict]:
    """Load parsed facts (ground truth)."""
    facts_file = paths.find_parsed_facts_filing(
        filing['market'],
        filing['company'],
        filing['form_type'],
        filing['filing_date']
    )
    
    if not facts_file:
        return [], {}
    
    with open(facts_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    facts = data.get('facts', [])
    metadata = data.get('metadata', {})
    
    return facts, metadata


def load_mapped_statements(
    paths: CCQPaths,
    filing: Dict[str, str],
    mapper: str
) -> Dict[str, List[Dict]]:
    """
    Load all mapped statements from a mapper.
    
    Returns:
        Dict mapping statement_type -> list of facts
    """
    base_path = paths.input_mapped if mapper == 'map_pro' else paths.mapper_output
    
    if not base_path:
        return {}
    
    statements = {}
    
    for stmt_name in ['balance_sheet', 'income_statement', 'cash_flow', 'other']:
        stmt_file = base_path / filing['market'] / \
                   filing['company'].replace(' ', '_') / \
                   filing['form_type'] / filing['filing_date'] / \
                   f"{stmt_name}.json"
        
        # Try name variations
        if not stmt_file.exists():
            for variation in paths._generate_name_variations(filing['company']):
                stmt_file = base_path / filing['market'] / variation / \
                           filing['form_type'] / filing['filing_date'] / \
                           f"{stmt_name}.json"
                if stmt_file.exists():
                    break
        
        if not stmt_file.exists():
            continue
        
        with open(stmt_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if mapper == 'map_pro':
            facts = data.get('facts', [])
        else:  # ccq_val
            facts = data.get('line_items', [])
        
        statements[stmt_name] = facts
    
    return statements


def build_fact_index_by_id(facts: List[Dict]) -> Dict[str, Dict]:
    """Build index of parsed facts by fact_id."""
    return {
        fact['fact_id']: fact
        for fact in facts
        if 'fact_id' in fact
    }


def build_fact_index_by_concept(facts: List[Dict]) -> Dict[str, List[Dict]]:
    """Build index of parsed facts by concept."""
    index = defaultdict(list)
    for fact in facts:
        concept = fact.get('concept_qname', '')
        if concept:
            index[concept].append(fact)
    return dict(index)


def extract_mapped_fact_ids(statements: Dict[str, List[Dict]]) -> Set[str]:
    """
    Extract all fact_ids from mapped statements.
    
    Map Pro includes fact_id field linking back to parsed facts.
    """
    fact_ids = set()
    
    for stmt_facts in statements.values():
        for fact in stmt_facts:
            fact_id = fact.get('fact_id')
            if fact_id:
                fact_ids.add(fact_id)
    
    return fact_ids


def extract_mapped_concepts(statements: Dict[str, List[Dict]], mapper: str) -> Set[str]:
    """
    Extract all concepts from mapped statements.
    
    CCQ doesn't have fact_id, so we match by concept.
    """
    concepts = set()
    
    for stmt_facts in statements.values():
        for fact in stmt_facts:
            if mapper == 'map_pro':
                concept = fact.get('concept', '') or fact.get('original_concept', '')
            else:  # ccq_val
                concept = fact.get('qname', '')
            
            if concept:
                # Normalize concept (remove year suffix)
                import re
                concept = re.sub(r'-\d{4}:', ':', concept)
                concepts.add(concept)
    
    return concepts


def normalize_concept(concept: str) -> str:
    """Normalize concept by removing year suffix."""
    if not concept:
        return ''
    
    import re
    return re.sub(r'-\d{4}:', ':', concept)


def filter_mappable_facts(facts: List[Dict]) -> List[Dict]:
    """
    Filter parsed facts to only include mappable facts.
    
    Excludes:
    - DEI namespace (document metadata)
    - SRT namespace (statement reference taxonomy)
    - Country/currency namespaces
    """
    mappable = []
    
    excluded_namespaces = {
        'http://xbrl.sec.gov/dei/',
        'http://xbrl.sec.gov/srt/',
        'http://xbrl.sec.gov/country/',
        'http://xbrl.sec.gov/currency/'
    }
    
    for fact in facts:
        namespace = fact.get('concept_namespace', '')
        
        # Check if namespace should be excluded
        is_excluded = any(
            namespace.startswith(excl) for excl in excluded_namespaces
        )
        
        if not is_excluded:
            mappable.append(fact)
    
    return mappable


# ============================================================================
# COVERAGE ANALYSIS TESTS
# ============================================================================

def analyze_coverage(
    parsed_facts: List[Dict],
    map_pro_statements: Dict[str, List[Dict]],
    ccq_statements: Dict[str, List[Dict]]
) -> Dict[str, Any]:
    """
    Comprehensive coverage analysis.
    
    Returns:
        Detailed report on mapping coverage
    """
    # Filter to only mappable facts
    mappable_facts = filter_mappable_facts(parsed_facts)
    
    # Build indexes
    parsed_by_id = build_fact_index_by_id(mappable_facts)
    parsed_by_concept = build_fact_index_by_concept(mappable_facts)
    
    # Extract mapped fact IDs (Map Pro has direct traceability)
    map_pro_fact_ids = extract_mapped_fact_ids(map_pro_statements)
    
    # Extract mapped concepts (for CCQ comparison)
    map_pro_concepts = extract_mapped_concepts(map_pro_statements, 'map_pro')
    ccq_concepts = extract_mapped_concepts(ccq_statements, 'ccq_val')
    
    # Compute coverage by fact_id (Map Pro only)
    mapped_by_map_pro_ids = set(parsed_by_id.keys()) & map_pro_fact_ids
    unmapped_by_map_pro_ids = set(parsed_by_id.keys()) - map_pro_fact_ids
    
    # Compute coverage by concept (both mappers)
    parsed_concepts = {
        normalize_concept(fact.get('concept_qname', ''))
        for fact in mappable_facts
        if fact.get('concept_qname')
    }
    
    mapped_by_both_concepts = parsed_concepts & map_pro_concepts & ccq_concepts
    mapped_by_map_pro_only = (parsed_concepts & map_pro_concepts) - ccq_concepts
    mapped_by_ccq_only = (parsed_concepts & ccq_concepts) - map_pro_concepts
    unmapped_by_both = parsed_concepts - map_pro_concepts - ccq_concepts
    
    # Analyze unmapped facts
    unmapped_fact_analysis = analyze_unmapped_facts(
        [parsed_by_id[fid] for fid in unmapped_by_map_pro_ids if fid in parsed_by_id]
    )
    
    # Compute statistics
    total_parsed = len(mappable_facts)
    total_concepts = len(parsed_concepts)
    
    map_pro_coverage_by_id = (len(mapped_by_map_pro_ids) / total_parsed * 100) if total_parsed > 0 else 0
    map_pro_coverage_by_concept = (len(map_pro_concepts & parsed_concepts) / total_concepts * 100) if total_concepts > 0 else 0
    ccq_coverage_by_concept = (len(ccq_concepts & parsed_concepts) / total_concepts * 100) if total_concepts > 0 else 0
    union_coverage = len((map_pro_concepts | ccq_concepts) & parsed_concepts) / total_concepts * 100 if total_concepts > 0 else 0
    
    return {
        'parsed_facts': {
            'total': len(parsed_facts),
            'mappable': total_parsed,
            'filtered_out': len(parsed_facts) - total_parsed
        },
        'concepts': {
            'total_parsed': total_concepts,
            'mapped_by_both': len(mapped_by_both_concepts),
            'mapped_by_map_pro_only': len(mapped_by_map_pro_only),
            'mapped_by_ccq_only': len(mapped_by_ccq_only),
            'unmapped_by_both': len(unmapped_by_both)
        },
        'coverage_rates': {
            'map_pro_by_fact_id': round(map_pro_coverage_by_id, 2),
            'map_pro_by_concept': round(map_pro_coverage_by_concept, 2),
            'ccq_by_concept': round(ccq_coverage_by_concept, 2),
            'union_coverage': round(union_coverage, 2)
        },
        'unmapped_analysis': unmapped_fact_analysis,
        'sample_unmapped_concepts': list(unmapped_by_both)[:20],
        'sample_map_pro_only': list(mapped_by_map_pro_only)[:10],
        'sample_ccq_only': list(mapped_by_ccq_only)[:10]
    }


def analyze_unmapped_facts(unmapped: List[Dict]) -> Dict[str, Any]:
    """Analyze patterns in unmapped facts."""
    if not unmapped:
        return {
            'count': 0,
            'patterns': {}
        }
    
    # Group by namespace
    by_namespace = defaultdict(int)
    by_period_type = defaultdict(int)
    by_has_value = defaultdict(int)
    
    for fact in unmapped:
        namespace = fact.get('concept_namespace', 'unknown')
        by_namespace[namespace] += 1
        
        if fact.get('is_instant'):
            by_period_type['instant'] += 1
        elif fact.get('is_duration'):
            by_period_type['duration'] += 1
        else:
            by_period_type['unknown'] += 1
        
        has_value = 'has_value' if fact.get('fact_value') else 'null_value'
        by_has_value[has_value] += 1
    
    return {
        'count': len(unmapped),
        'by_namespace': dict(by_namespace),
        'by_period_type': dict(by_period_type),
        'by_value_status': dict(by_has_value)
    }


def test_coverage_analysis(paths, sample_filing):
    """Test coverage analysis for both mappers."""
    print("\n" + "="*80)
    print("COVERAGE ANALYSIS")
    print("="*80)
    
    # Load parsed facts (ground truth)
    print("\n📖 Loading parsed facts...")
    parsed_facts, metadata = load_parsed_facts(paths, sample_filing)
    print(f"  Total parsed facts: {len(parsed_facts)}")
    
    if not parsed_facts:
        pytest.skip("Parsed facts not found")
    
    # Load mapped statements
    print("\n📥 Loading Map Pro statements...")
    map_pro_statements = load_mapped_statements(paths, sample_filing, 'map_pro')
    map_pro_fact_count = sum(len(facts) for facts in map_pro_statements.values())
    print(f"  Total Map Pro facts: {map_pro_fact_count}")
    
    print("\n📥 Loading CCQ Mapper statements...")
    ccq_statements = load_mapped_statements(paths, sample_filing, 'ccq_val')
    ccq_fact_count = sum(len(facts) for facts in ccq_statements.values())
    print(f"  Total CCQ Mapper facts: {ccq_fact_count}")
    
    if not ccq_statements:
        print("  ⚠️  CCQ Mapper output not found - skipping CCQ analysis")
        ccq_statements = {}
    
    # Analyze coverage
    print("\n🔍 Analyzing coverage...")
    analysis = analyze_coverage(parsed_facts, map_pro_statements, ccq_statements)
    
    # Print results
    print("\n" + "="*80)
    print("COVERAGE RESULTS")
    print("="*80)
    
    print(f"\n📊 Parsed Facts:")
    print(f"  Total parsed: {analysis['parsed_facts']['total']}")
    print(f"  Mappable (after filtering): {analysis['parsed_facts']['mappable']}")
    print(f"  Filtered out (DEI, SRT, etc.): {analysis['parsed_facts']['filtered_out']}")
    
    print(f"\n📊 Concept Coverage:")
    print(f"  Total unique concepts: {analysis['concepts']['total_parsed']}")
    print(f"  ✅ Mapped by both mappers: {analysis['concepts']['mapped_by_both']}")
    print(f"  🔵 Map Pro only: {analysis['concepts']['mapped_by_map_pro_only']}")
    print(f"  🟢 CCQ only: {analysis['concepts']['mapped_by_ccq_only']}")
    print(f"  ❌ Unmapped by both: {analysis['concepts']['unmapped_by_both']}")
    
    print(f"\n📈 Coverage Rates:")
    print(f"  Map Pro (by fact_id): {analysis['coverage_rates']['map_pro_by_fact_id']}%")
    print(f"  Map Pro (by concept): {analysis['coverage_rates']['map_pro_by_concept']}%")
    print(f"  CCQ (by concept): {analysis['coverage_rates']['ccq_by_concept']}%")
    print(f"  🎯 Union coverage: {analysis['coverage_rates']['union_coverage']}%")
    
    # Unmapped analysis
    print(f"\n🔍 Unmapped Fact Analysis:")
    print(f"  Total unmapped by Map Pro: {analysis['unmapped_analysis']['count']}")
    if analysis['unmapped_analysis']['count'] > 0 and 'by_namespace' in analysis['unmapped_analysis']:
        print(f"  By namespace:")
        for ns, count in sorted(
            analysis['unmapped_analysis']['by_namespace'].items(),
            key=lambda x: -x[1]
        )[:5]:
            print(f"    • {ns}: {count} facts")
    
    # Sample unmapped concepts
    if analysis['sample_unmapped_concepts']:
        print(f"\n❌ Sample unmapped concepts (first 10):")
        for concept in analysis['sample_unmapped_concepts'][:10]:
            print(f"  • {concept}")
    
    # Assert reasonable coverage
    union_coverage = analysis['coverage_rates']['union_coverage']
    assert union_coverage >= 85.0, \
        f"Union coverage is {union_coverage}% - expected at least 85%"
    
    print("\n✅ Coverage test passed!")


def test_export_coverage_report(paths, sample_filing):
    """Export detailed coverage report to JSON."""
    print("\n" + "="*80)
    print("EXPORTING COVERAGE REPORT")
    print("="*80)
    
    # Use CCQ output path for reports
    if paths.mapper_output:
        output_dir = paths.mapper_output.parent / 'test_reports'
    else:
        output_dir = paths.output_validated.parent / 'test_reports'
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    parsed_facts, metadata = load_parsed_facts(paths, sample_filing)
    map_pro_statements = load_mapped_statements(paths, sample_filing, 'map_pro')
    ccq_statements = load_mapped_statements(paths, sample_filing, 'ccq_val')
    
    # Analyze
    analysis = analyze_coverage(parsed_facts, map_pro_statements, ccq_statements)
    
    # Add metadata
    report = {
        'filing': sample_filing,
        'metadata': metadata,
        'analysis': analysis,
        'generated_at': datetime.now().isoformat()
    }
    
    # Save report
    report_file = output_dir / 'coverage_analysis_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Report saved to: {report_file}")
    print(f"\nTo analyze the report:")
    print(f"  cat {report_file} | jq '.analysis.coverage_rates'")
    print(f"  cat {report_file} | jq '.analysis.sample_unmapped_concepts'")
    
    return report_file


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])