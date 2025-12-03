# File: tests/test_fact_authority_components.py
# Test: Individual component tests for fact_authority
# Run from project root: python tests/test_fact_authority_components.py

"""
Test Fact Authority Components
===============================

Tests individual components that should work independently:
1. NullQualityHandler
2. ReconciliationReporter
3. OutputWriter (without writing)
4. StatementClassifier (basic structure)
5. XBRLFilingsConsolidator (basic structure)

These tests verify component functionality without requiring
full taxonomy integration.
"""

import sys
import json
from pathlib import Path
from pprint import pprint

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from core.config_loader import ConfigLoader
from core.data_paths import CCQPaths
from engines.fact_authority.process import NullQualityHandler
from engines.fact_authority.output import ReconciliationReporter, OutputWriter
from engines.fact_authority.process import StatementClassifier
from engines.fact_authority.process import XBRLFilingsConsolidator


def test_null_quality_handler():
    """Test NullQualityHandler component."""
    print("=" * 80)
    print("TEST 1: NullQualityHandler")
    print("=" * 80)
    
    try:
        config = ConfigLoader()
        ccq_paths = CCQPaths(
            data_root=config.get('data_root'),
            input_path=config.get('input_path'),
            output_path=config.get('output_path'),
            taxonomy_path=config.get('taxonomy_path'),
            parsed_facts_path=config.get('parsed_facts_path'),
            mapper_xbrl_path=config.get('mapper_xbrl_path'),
            mapper_output_path=config.get('mapper_output_path'),
            unified_output_path=config.get('unified_output_path')
        )
        handler = NullQualityHandler(ccq_paths)
        
        print("✓ NullQualityHandler initialized")
        
        # Test with mock statement data
        mock_map_pro = {
            'balance_sheet': {
                'facts': [
                    {'concept_qname': 'us-gaap:Assets', 'value': 1000},
                    {'concept_qname': 'us-gaap:Liabilities', 'value': None}
                ],
                'metadata': {
                    'null_facts': [
                        {'concept_qname': 'us-gaap:Liabilities', 'null_reason': 'missing'}
                    ]
                }
            },
            'metadata': {}
        }
        
        mock_ccq = {
            'balance_sheet': {
                'facts': [
                    {'concept_qname': 'us-gaap:Assets', 'value': 1000},
                    {'concept_qname': 'us-gaap:Liabilities', 'value': None},
                    {'concept_qname': 'us-gaap:Equity', 'value': None}
                ],
                'metadata': {
                    'null_facts': [
                        {'concept_qname': 'us-gaap:Liabilities', 'null_reason': 'missing'},
                        {'concept_qname': 'us-gaap:Equity', 'null_reason': 'zero'}
                    ]
                }
            },
            'metadata': {}
        }
        
        print("\nAnalyzing mock null quality data...")
        analysis = handler.analyze_from_statements(mock_map_pro, mock_ccq)
        
        print("✓ Analysis completed")
        print(f"\nResults:")
        print(f"  - Map Pro nulls: {analysis['map_pro_null_count']}")
        print(f"  - CCQ nulls: {analysis['ccq_null_count']}")
        print(f"  - Common nulls: {len(analysis['common_null_concepts'])}")
        print(f"  - Map Pro only: {len(analysis['map_pro_only_nulls'])}")
        print(f"  - CCQ only: {len(analysis['ccq_only_nulls'])}")
        
        if analysis['common_null_concepts']:
            print(f"  - Common concepts: {analysis['common_null_concepts']}")
        
        # Verify results
        assert analysis['map_pro_null_count'] == 1, "Wrong Map Pro null count"
        assert analysis['ccq_null_count'] == 2, "Wrong CCQ null count"
        assert 'us-gaap:Liabilities' in analysis['common_null_concepts'], "Missing common null"
        
        print("\n✓ NullQualityHandler working correctly")
        return True
        
    except Exception as e:
        print(f"✗ NullQualityHandler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_reconciliation_reporter():
    """Test ReconciliationReporter component."""
    print("\n" + "=" * 80)
    print("TEST 2: ReconciliationReporter")
    print("=" * 80)
    
    try:
        reporter = ReconciliationReporter()
        
        print("✓ ReconciliationReporter initialized")
        
        # Mock reconciliation result
        mock_reconciliation = {
            'overall_statistics': {
                'total_concepts': 100,
                'taxonomy_correct_both': 80,
                'taxonomy_correct_map_pro_only': 10,
                'taxonomy_correct_ccq_only': 5,
                'taxonomy_correct_neither': 3,
                'not_in_taxonomy': 2,
                'map_pro_facts': 95,
                'ccq_facts': 88
            },
            'statements': {
                'balance_sheet': {
                    'statistics': {
                        'total_concepts': 50,
                        'taxonomy_correct_both': 40,
                        'taxonomy_correct_map_pro_only': 5,
                        'taxonomy_correct_ccq_only': 3,
                        'taxonomy_correct_neither': 1,
                        'not_in_taxonomy': 1,
                        'map_pro_facts': 48,
                        'ccq_facts': 45
                    },
                    'discrepancies': []
                }
            }
        }
        
        # Mock null quality
        mock_null_quality = {
            'map_pro_null_count': 5,
            'ccq_null_count': 7,
            'common_null_concepts': ['us-gaap:SomeNullConcept']
        }
        
        print("\nGenerating report from mock data...")
        report = reporter.generate_report(mock_reconciliation, mock_null_quality)
        
        print("✓ Report generated")
        print(f"\nReport structure:")
        print(f"  - Has metadata: {'report_metadata' in report}")
        print(f"  - Has executive summary: {'executive_summary' in report}")
        print(f"  - Has overall stats: {'overall_statistics' in report}")
        print(f"  - Has statement details: {'statement_details' in report}")
        print(f"  - Has recommendations: {'recommendations' in report}")
        
        # Check executive summary
        if 'executive_summary' in report:
            summary = report['executive_summary']
            print(f"\nExecutive summary:")
            print(f"  - Total concepts: {summary.get('total_concepts_validated')}")
            print(f"  - Correctness: {summary.get('correctness_percentage')}%")
            print(f"  - Quality grade: {summary.get('overall_quality')}")
        
        # Check recommendations
        if 'recommendations' in report:
            print(f"\nRecommendations: {len(report['recommendations'])} items")
            for rec in report['recommendations'][:2]:
                print(f"  - {rec[:80]}...")
        
        # Verify structure
        assert 'report_metadata' in report, "Missing report metadata"
        assert 'executive_summary' in report, "Missing executive summary"
        assert report['report_metadata']['engine'] == 'fact_authority', "Wrong engine"
        
        print("\n✓ ReconciliationReporter working correctly")
        return True
        
    except Exception as e:
        print(f"✗ ReconciliationReporter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_statement_classifier():
    """Test StatementClassifier component (structure only)."""
    print("\n" + "=" * 80)
    print("TEST 3: StatementClassifier")
    print("=" * 80)
    
    try:
        # Mock taxonomy data (empty for now)
        mock_taxonomy = {
            'concepts': {}
        }
        
        classifier = StatementClassifier(mock_taxonomy)
        
        print("✓ StatementClassifier initialized")
        print("  Note: Using empty taxonomy (placeholder)")
        
        # Test classification (will return None with empty taxonomy)
        result = classifier.classify_concept('us-gaap:Assets')
        
        print(f"\nClassification result for 'us-gaap:Assets': {result}")
        print("  Expected: None (taxonomy is empty)")
        
        # Test validation
        validation = classifier.validate_placement('us-gaap:Assets', 'balance_sheet')
        
        print(f"\nValidation result:")
        print(f"  - Is valid: {validation['is_valid']}")
        print(f"  - Reason: {validation['reason']}")
        
        # Should be valid (accepts concepts not in taxonomy)
        assert validation['is_valid'], "Should accept unknown concepts"
        
        print("\n✓ StatementClassifier structure working")
        print("  ⚠ Full functionality requires taxonomy integration")
        return True
        
    except Exception as e:
        print(f"✗ StatementClassifier test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_xbrl_filings_consolidator():
    """Test XBRLFilingsConsolidator component (structure only)."""
    print("\n" + "=" * 80)
    print("TEST 4: XBRLFilingsConsolidator")
    print("=" * 80)
    
    try:
        # Mock taxonomy and filing data
        mock_taxonomy = {
            'concepts': {}
        }
        
        mock_filing = {
            'extension_schema': {
                'concepts': {
                    'aci:CustomRevenue': {
                        'type': 'monetary',
                        'substitutionGroup': 'us-gaap:Revenue',
                        'periodType': 'duration'
                    }
                }
            }
        }
        
        consolidator = XBRLFilingsConsolidator(mock_taxonomy, mock_filing)
        
        print("✓ XBRLFilingsConsolidator initialized")
        
        # Test statistics
        stats = consolidator.get_statistics()
        
        print(f"\nStatistics:")
        print(f"  - Total concepts: {stats['total_concepts']}")
        print(f"  - Base taxonomy: {stats['base_taxonomy_concepts']}")
        print(f"  - Extensions: {stats['extension_concepts']}")
        
        # Test concept lookup
        concept_def = consolidator.get_concept_definition('aci:CustomRevenue')
        
        print(f"\nLooking up 'aci:CustomRevenue':")
        if concept_def:
            print(f"  - Found: Yes")
            print(f"  - Source: {concept_def.get('source')}")
            print(f"  - Type: {concept_def.get('type')}")
            print(f"  - Base concept: {concept_def.get('base_concept')}")
        else:
            print(f"  - Found: No")
        
        # Test extension check
        is_ext = consolidator.is_extension_concept('aci:CustomRevenue')
        print(f"\nIs 'aci:CustomRevenue' an extension? {is_ext}")
        
        is_ext = consolidator.is_extension_concept('us-gaap:Assets')
        print(f"Is 'us-gaap:Assets' an extension? {is_ext}")
        
        print("\n✓ XBRLFilingsConsolidator structure working")
        print("  ⚠ Full functionality requires taxonomy integration")
        return True
        
    except Exception as e:
        print(f"✗ XBRLFilingsConsolidator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_output_writer():
    """Test OutputWriter component (without actually writing)."""
    print("\n" + "=" * 80)
    print("TEST 5: OutputWriter")
    print("=" * 80)
    
    try:
        config = ConfigLoader()
        ccq_paths = CCQPaths(
            data_root=config.get('data_root'),
            input_path=config.get('input_path'),
            output_path=config.get('output_path'),
            taxonomy_path=config.get('taxonomy_path'),
            parsed_facts_path=config.get('parsed_facts_path'),
            mapper_xbrl_path=config.get('mapper_xbrl_path'),
            mapper_output_path=config.get('mapper_output_path'),
            unified_output_path=config.get('unified_output_path')
        )
        writer = OutputWriter(ccq_paths)
        
        print("✓ OutputWriter initialized")
        print(f"  Output path: {ccq_paths.unified_mapped}")
        
        # Verify unified_mapped path exists
        assert ccq_paths.unified_mapped is not None, "Unified output path not configured"
        
        print("\n✓ OutputWriter structure working")
        print("  Note: Not testing actual file writing")
        print("  Will be tested in integration tests")
        return True
        
    except Exception as e:
        print(f"✗ OutputWriter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all component tests."""
    print("=" * 80)
    print("FACT AUTHORITY - COMPONENT TESTS")
    print("=" * 80)
    print()
    
    results = []
    
    # Test 1: NullQualityHandler
    results.append(test_null_quality_handler())
    
    # Test 2: ReconciliationReporter
    results.append(test_reconciliation_reporter())
    
    # Test 3: StatementClassifier
    results.append(test_statement_classifier())
    
    # Test 4: XBRLFilingsConsolidator
    results.append(test_xbrl_filings_consolidator())
    
    # Test 5: OutputWriter
    results.append(test_output_writer())
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests passed: {passed}/{total}")
    
    if all(results):
        print("\n✓ ALL COMPONENT TESTS PASSED")
        print("\nComponents are working correctly!")
        print("\nNote: Some components have placeholder functionality")
        print("      Complete taxonomy integration for full features")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        print("\nCheck error messages above")
        return 1


if __name__ == '__main__':
    sys.exit(main())