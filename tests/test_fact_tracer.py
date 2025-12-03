"""
Fact Tracer
===========

Trace individual facts through the mapping pipeline:
Parsed Raw → Map Pro → CCQ Mapper → Unified

This helps understand:
- Why certain facts are mapped/not mapped
- How each mapper handles specific facts
- Differences in mapping logic

Usage:
    pytest ccq_val/tests/test_fact_tracer.py -v
    pytest ccq_val/tests/test_fact_tracer.py::test_trace_random_facts -v -s
"""

import pytest
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
import json
import random
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
# FACT TRACING
# ============================================================================

class FactTracer:
    """Trace a fact through the mapping pipeline."""
    
    def __init__(self, paths: CCQPaths, filing: Dict[str, str]):
        self.paths = paths
        self.filing = filing
        self.parsed_facts = None
        self.map_pro_statements = None
        self.ccq_statements = None
        self.unified_statements = None
    
    def load_data(self):
        """Load all necessary data."""
        # Load parsed facts
        facts_file = self.paths.find_parsed_facts_filing(
            self.filing['market'],
            self.filing['company'],
            self.filing['form_type'],
            self.filing['filing_date']
        )
        
        if facts_file:
            with open(facts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.parsed_facts = data.get('facts', [])
        
        # Load Map Pro statements
        self.map_pro_statements = self._load_statements(self.paths.input_mapped, 'map_pro')
        
        # Load CCQ statements
        if self.paths.mapper_output:
            self.ccq_statements = self._load_statements(self.paths.mapper_output, 'ccq_val')
        
        # Load Unified statements (if they exist)
        # Unified statements are typically in mapper_output with different naming
        # This is a placeholder - adjust based on actual unified output location
    
    def _load_statements(self, base_path: Path, mapper: str) -> Dict[str, List[Dict]]:
        """Load all statements from a mapper."""
        statements = {}
        
        for stmt_name in ['balance_sheet', 'income_statement', 'cash_flow', 'other']:
            stmt_file = base_path / self.filing['market'] / \
                       self.filing['company'].replace(' ', '_') / \
                       self.filing['form_type'] / self.filing['filing_date'] / \
                       f"{stmt_name}.json"
            
            if not stmt_file.exists():
                for variation in self.paths._generate_name_variations(self.filing['company']):
                    stmt_file = base_path / self.filing['market'] / variation / \
                               self.filing['form_type'] / self.filing['filing_date'] / \
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
    
    def trace_fact_by_id(self, fact_id: str) -> Dict[str, Any]:
        """Trace a single fact by its fact_id."""
        # Find in parsed facts
        parsed_fact = None
        for fact in self.parsed_facts or []:
            if fact.get('fact_id') == fact_id:
                parsed_fact = fact
                break
        
        if not parsed_fact:
            return {
                'fact_id': fact_id,
                'found': False,
                'error': 'Fact ID not found in parsed facts'
            }
        
        # Find in Map Pro (has fact_id linkage)
        map_pro_fact = None
        map_pro_statement = None
        
        for stmt_name, facts in (self.map_pro_statements or {}).items():
            for fact in facts:
                if fact.get('fact_id') == fact_id:
                    map_pro_fact = fact
                    map_pro_statement = stmt_name
                    break
            if map_pro_fact:
                break
        
        # Find in CCQ (by concept matching)
        ccq_fact = None
        ccq_statement = None
        parsed_concept = self._normalize_concept(parsed_fact.get('concept_qname', ''))
        
        for stmt_name, facts in (self.ccq_statements or {}).items():
            for fact in facts:
                ccq_concept = self._normalize_concept(fact.get('qname', ''))
                if ccq_concept == parsed_concept:
                    # Additional check: compare values if possible
                    if self._values_similar(parsed_fact.get('fact_value'), fact.get('value')):
                        ccq_fact = fact
                        ccq_statement = stmt_name
                        break
            if ccq_fact:
                break
        
        return {
            'fact_id': fact_id,
            'found': True,
            'parsed': {
                'concept': parsed_fact.get('concept_qname'),
                'label': parsed_fact.get('concept_label'),
                'value': parsed_fact.get('fact_value'),
                'context': parsed_fact.get('context_ref'),
                'period_type': 'instant' if parsed_fact.get('is_instant') else 'duration',
                'namespace': parsed_fact.get('concept_namespace')
            },
            'map_pro': {
                'found': map_pro_fact is not None,
                'statement': map_pro_statement,
                'concept': map_pro_fact.get('concept') if map_pro_fact else None,
                'value': map_pro_fact.get('value') if map_pro_fact else None,
                'mapping_confidence': map_pro_fact.get('mapping_confidence') if map_pro_fact else None,
                'mapping_method': map_pro_fact.get('mapping_method') if map_pro_fact else None
            },
            'ccq_val': {
                'found': ccq_fact is not None,
                'statement': ccq_statement,
                'concept': ccq_fact.get('qname') if ccq_fact else None,
                'value': ccq_fact.get('value') if ccq_fact else None,
                'classification': ccq_fact.get('classification') if ccq_fact else None
            },
            'mapping_status': self._determine_mapping_status(map_pro_fact, ccq_fact)
        }
    
    def trace_multiple_facts(
        self,
        fact_ids: List[str] = None,
        sample_size: int = 10,
        stratify_by: str = 'namespace'
    ) -> List[Dict[str, Any]]:
        """
        Trace multiple facts.
        
        Args:
            fact_ids: Specific fact IDs to trace. If None, sample randomly.
            sample_size: Number of facts to sample if fact_ids not provided
            stratify_by: How to stratify sampling ('namespace', 'period_type', 'random')
        
        Returns:
            List of trace results
        """
        if fact_ids:
            return [self.trace_fact_by_id(fid) for fid in fact_ids]
        
        # Sample facts
        if not self.parsed_facts:
            return []
        
        # Filter to mappable facts only
        mappable = self._filter_mappable_facts(self.parsed_facts)
        
        if stratify_by == 'random':
            sampled = random.sample(mappable, min(sample_size, len(mappable)))
        elif stratify_by == 'namespace':
            sampled = self._stratified_sample_by_namespace(mappable, sample_size)
        elif stratify_by == 'period_type':
            sampled = self._stratified_sample_by_period(mappable, sample_size)
        else:
            sampled = random.sample(mappable, min(sample_size, len(mappable)))
        
        return [self.trace_fact_by_id(fact['fact_id']) for fact in sampled]
    
    def _normalize_concept(self, concept: str) -> str:
        """Normalize concept by removing year suffix."""
        import re
        return re.sub(r'-\d{4}:', ':', concept)
    
    def _values_similar(self, val1: Any, val2: Any) -> bool:
        """Check if two values are similar."""
        if val1 is None and val2 is None:
            return True
        if val1 is None or val2 is None:
            return False
        
        # Convert to strings for comparison
        str1 = str(val1).strip()
        str2 = str(val2).strip()
        
        # Exact match
        if str1 == str2:
            return True
        
        # Numeric comparison
        try:
            num1 = float(str1.replace(',', ''))
            num2 = float(str2.replace(',', ''))
            return abs(num1 - num2) < 0.01
        except (ValueError, TypeError):
            pass
        
        return False
    
    def _determine_mapping_status(
        self,
        map_pro_fact: Optional[Dict],
        ccq_fact: Optional[Dict]
    ) -> str:
        """Determine overall mapping status."""
        if map_pro_fact and ccq_fact:
            return 'BOTH_MAPPED'
        elif map_pro_fact and not ccq_fact:
            return 'MAP_PRO_ONLY'
        elif ccq_fact and not map_pro_fact:
            return 'CCQ_ONLY'
        else:
            return 'UNMAPPED'
    
    def _filter_mappable_facts(self, facts: List[Dict]) -> List[Dict]:
        """Filter to only mappable facts (exclude DEI, SRT, etc.)."""
        excluded_prefixes = ['dei:', 'srt:', 'country:', 'currency:']
        
        return [
            fact for fact in facts
            if not any(fact.get('concept_qname', '').startswith(prefix) for prefix in excluded_prefixes)
            and fact.get('fact_id')
        ]
    
    def _stratified_sample_by_namespace(self, facts: List[Dict], size: int) -> List[Dict]:
        """Sample facts stratified by namespace."""
        by_namespace = defaultdict(list)
        
        for fact in facts:
            ns = fact.get('concept_namespace', 'unknown')
            # Simplify namespace
            if 'us-gaap' in ns:
                ns = 'us-gaap'
            elif 'ifrs' in ns:
                ns = 'ifrs'
            else:
                ns = fact.get('concept_qname', '').split(':')[0] if ':' in fact.get('concept_qname', '') else 'other'
            
            by_namespace[ns].append(fact)
        
        # Sample proportionally from each namespace
        sampled = []
        per_namespace = max(1, size // len(by_namespace))
        
        for ns, ns_facts in by_namespace.items():
            sampled.extend(random.sample(ns_facts, min(per_namespace, len(ns_facts))))
        
        # Fill remaining slots randomly
        remaining = size - len(sampled)
        if remaining > 0:
            available = [f for f in facts if f not in sampled]
            sampled.extend(random.sample(available, min(remaining, len(available))))
        
        return sampled[:size]
    
    def _stratified_sample_by_period(self, facts: List[Dict], size: int) -> List[Dict]:
        """Sample facts stratified by period type."""
        instant = [f for f in facts if f.get('is_instant')]
        duration = [f for f in facts if f.get('is_duration')]
        
        instant_count = size // 2
        duration_count = size - instant_count
        
        sampled = []
        sampled.extend(random.sample(instant, min(instant_count, len(instant))))
        sampled.extend(random.sample(duration, min(duration_count, len(duration))))
        
        return sampled


# ============================================================================
# TESTS
# ============================================================================

def test_trace_random_facts(paths, sample_filing):
    """Trace random sample of facts through mapping pipeline."""
    print("\n" + "="*80)
    print("FACT TRACING: Random Sample")
    print("="*80)
    
    # Initialize tracer
    tracer = FactTracer(paths, sample_filing)
    tracer.load_data()
    
    if not tracer.parsed_facts:
        pytest.skip("Parsed facts not found")
    
    # Trace 10 random facts
    print(f"\n🔍 Tracing 10 random facts...")
    traces = tracer.trace_multiple_facts(sample_size=10, stratify_by='namespace')
    
    # Analyze results
    mapping_status = defaultdict(int)
    
    for i, trace in enumerate(traces, 1):
        print(f"\n{'='*80}")
        print(f"FACT #{i}: {trace['fact_id']}")
        print(f"{'='*80}")
        
        if not trace.get('found'):
            print(f"❌ {trace.get('error')}")
            continue
        
        # Parsed fact info
        parsed = trace['parsed']
        print(f"\n📖 PARSED FACT:")
        print(f"  Concept: {parsed['concept']}")
        print(f"  Label: {parsed['label']}")
        print(f"  Value: {parsed['value']}")
        print(f"  Period: {parsed['period_type']}")
        print(f"  Namespace: {parsed['namespace']}")
        
        # Map Pro mapping
        mp = trace['map_pro']
        print(f"\n🔵 MAP PRO:")
        if mp['found']:
            print(f"  ✅ Found in: {mp['statement']}")
            print(f"  Mapped concept: {mp['concept']}")
            print(f"  Value: {mp['value']}")
            print(f"  Confidence: {mp['mapping_confidence']}")
            print(f"  Method: {mp['mapping_method']}")
        else:
            print(f"  ❌ Not mapped")
        
        # CCQ mapping
        ccq = trace['ccq_val']
        print(f"\n🟢 CCQ MAPPER:")
        if ccq['found']:
            print(f"  ✅ Found in: {ccq['statement']}")
            print(f"  Mapped concept: {ccq['concept']}")
            print(f"  Value: {ccq['value']}")
            if ccq['classification']:
                print(f"  Classification: {ccq['classification']}")
        else:
            print(f"  ❌ Not mapped")
        
        # Overall status
        status = trace['mapping_status']
        mapping_status[status] += 1
        print(f"\n📊 MAPPING STATUS: {status}")
    
    # Summary
    print("\n" + "="*80)
    print("TRACING SUMMARY")
    print("="*80)
    
    print(f"\nMapping Status Distribution:")
    for status, count in mapping_status.items():
        print(f"  {status}: {count} facts ({count/len(traces)*100:.1f}%)")
    
    print(f"\n✅ Traced {len(traces)} facts successfully")


def test_trace_specific_concepts(paths, sample_filing):
    """Trace specific high-value concepts through the pipeline."""
    print("\n" + "="*80)
    print("FACT TRACING: Specific Concepts")
    print("="*80)
    
    tracer = FactTracer(paths, sample_filing)
    tracer.load_data()
    
    if not tracer.parsed_facts:
        pytest.skip("Parsed facts not found")
    
    # Find specific high-value concepts
    target_concepts = [
        'us-gaap:Assets',
        'us-gaap:Liabilities',
        'us-gaap:StockholdersEquity',
        'us-gaap:Revenues',
        'us-gaap:NetIncomeLoss',
        'us-gaap:CashAndCashEquivalentsAtCarryingValue'
    ]
    
    print(f"\n🎯 Looking for key financial concepts...")
    
    found_facts = []
    for fact in tracer.parsed_facts:
        concept = tracer._normalize_concept(fact.get('concept_qname', ''))
        if concept in target_concepts:
            found_facts.append(fact)
    
    print(f"  Found {len(found_facts)} instances of target concepts")
    
    # Trace them
    fact_ids = [f['fact_id'] for f in found_facts[:10]]  # Limit to 10
    traces = tracer.trace_multiple_facts(fact_ids=fact_ids)
    
    # Print concise summary
    for trace in traces:
        if not trace.get('found'):
            continue
        
        concept = trace['parsed']['concept']
        value = trace['parsed']['value']
        mp_status = "✅" if trace['map_pro']['found'] else "❌"
        ccq_status = "✅" if trace['ccq_val']['found'] else "❌"
        
        print(f"\n{concept}")
        print(f"  Value: {value}")
        print(f"  Map Pro: {mp_status}  CCQ: {ccq_status}")


def test_export_trace_report(paths, sample_filing):
    """Export detailed trace report to JSON."""
    print("\n" + "="*80)
    print("EXPORTING TRACE REPORT")
    print("="*80)
    
    # Use CCQ output path for reports  
    if paths.mapper_output:
        output_dir = paths.mapper_output.parent / 'test_reports'
    else:
        output_dir = paths.output_validated.parent / 'test_reports'
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    tracer = FactTracer(paths, sample_filing)
    tracer.load_data()
    
    if not tracer.parsed_facts:
        pytest.skip("Parsed facts not found")
    
    # Trace 20 facts
    traces = tracer.trace_multiple_facts(sample_size=20, stratify_by='namespace')
    
    # Build report
    report = {
        'filing': sample_filing,
        'traces': traces,
        'summary': {
            status: sum(1 for t in traces if t.get('mapping_status') == status)
            for status in ['BOTH_MAPPED', 'MAP_PRO_ONLY', 'CCQ_ONLY', 'UNMAPPED']
        },
        'generated_at': datetime.now().isoformat()
    }
    
    # Save
    report_file = output_dir / 'fact_trace_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Report saved to: {report_file}")
    print(f"\nTo analyze the report:")
    print(f"  cat {report_file} | jq '.traces[] | select(.mapping_status==\"UNMAPPED\")'")
    print(f"  cat {report_file} | jq '.summary'")
    
    return report_file


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])