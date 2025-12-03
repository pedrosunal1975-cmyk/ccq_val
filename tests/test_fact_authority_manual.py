# File: tests/test_fact_authority_manual.py
# Path: tests/test_fact_authority_manual.py

"""
Fact Authority Manual Test Runner
==================================

Tests fact_authority without pytest dependency.
Run: python3 tests/test_fact_authority_manual.py
"""

import sys
from pathlib import Path
from io import StringIO
import tempfile
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engines.fact_authority import (
    PresentationLinkbaseParser,
    TaxonomyAuthorityReader,
    get_taxonomy_authority,
    FilingTaxonomyDetector,
    StatementLoader,
    FactReconciler,
    StatementReconciler
)

# Try to import Component 4 modules (may fail in flat file structure)
COMPONENT_4_AVAILABLE = False
try:
    from engines.fact_authority import (
        JointStatementConstructor,
        NullQualityHandler,
        OutputWriter,
        ReconciliationReporter
    )
    COMPONENT_4_AVAILABLE = True
except ImportError as e:
    print(f"Note: Component 4 imports unavailable (expected in flat structure): {e}")
    print("Component 4 tests will be skipped.\n")


def test_presentation_parser_initialization():
    """Test parser initialization."""
    print("Testing PresentationLinkbaseParser initialization...")
    parser = PresentationLinkbaseParser()
    assert parser is not None
    assert hasattr(parser, 'NAMESPACES')
    print("  PASS: Parser initialized correctly")


def test_classify_statement_role():
    """Test role URI classification."""
    print("\nTesting statement role classification...")
    parser = PresentationLinkbaseParser()
    
    # Test balance sheet
    bs_uri = "http://fasb.org/us-gaap/role/statement/StatementOfFinancialPosition"
    assert parser._classify_statement_role(bs_uri) == 'balance_sheet'
    print("  PASS: Balance sheet role classified")
    
    # Test income statement
    is_uri = "http://fasb.org/us-gaap/role/statement/StatementOfIncome"
    assert parser._classify_statement_role(is_uri) == 'income_statement'
    print("  PASS: Income statement role classified")
    
    # Test cash flow
    cf_uri = "http://fasb.org/us-gaap/role/statement/StatementOfCashFlows"
    assert parser._classify_statement_role(cf_uri) == 'cash_flow'
    print("  PASS: Cash flow role classified")


def test_extract_concept_from_href():
    """Test concept extraction from href."""
    print("\nTesting concept extraction from href...")
    parser = PresentationLinkbaseParser()
    
    # Test simple fragment
    concept = parser._extract_concept_from_href("#us-gaap_Cash")
    assert concept == "us-gaap:Cash"
    print("  PASS: Simple fragment extracted")
    
    # Test with path
    concept = parser._extract_concept_from_href("../us-gaap-2024.xsd#us-gaap_Assets")
    assert concept == "us-gaap:Assets"
    print("  PASS: Fragment with path extracted")
    
    # Test no hash
    concept = parser._extract_concept_from_href("no-hash")
    assert concept is None
    print("  PASS: No hash handled correctly")


def test_parse_sample_linkbase():
    """Test parsing a sample presentation linkbase."""
    print("\nTesting linkbase parsing...")
    parser = PresentationLinkbaseParser()
    
    # Create sample linkbase XML
    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
<linkbase xmlns="http://www.xbrl.org/2003/linkbase"
          xmlns:xlink="http://www.w3.org/1999/xlink"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <presentationLink xlink:type="extended"
                      xlink:role="http://fasb.org/us-gaap/role/statement/StatementOfFinancialPosition">
        <loc xlink:type="locator"
             xlink:href="../us-gaap-2024.xsd#us-gaap_Assets"
             xlink:label="loc_Assets"/>
        <loc xlink:type="locator"
             xlink:href="../us-gaap-2024.xsd#us-gaap_AssetsCurrent"
             xlink:label="loc_AssetsCurrent"/>
        <loc xlink:type="locator"
             xlink:href="../us-gaap-2024.xsd#us-gaap_Cash"
             xlink:label="loc_Cash"/>
        
        <presentationArc xlink:type="arc"
                        xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child"
                        xlink:from="loc_Assets"
                        xlink:to="loc_AssetsCurrent"
                        order="1.0"/>
        <presentationArc xlink:type="arc"
                        xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child"
                        xlink:from="loc_AssetsCurrent"
                        xlink:to="loc_Cash"
                        order="1.0"/>
    </presentationLink>
</linkbase>"""
    
    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='_pre.xml', delete=False) as f:
        f.write(sample_xml)
        temp_path = Path(f.name)
    
    try:
        # Parse linkbase
        result = parser.parse_presentation_linkbase(temp_path)
        
        # Verify results
        assert 'concepts' in result
        assert 'metadata' in result
        print("  PASS: Linkbase parsed successfully")
        
        concepts = result['concepts']
        assert 'us-gaap:Assets' in concepts
        assert 'us-gaap:AssetsCurrent' in concepts
        assert 'us-gaap:Cash' in concepts
        print("  PASS: All concepts found")
        
        # Check hierarchy
        cash = concepts['us-gaap:Cash']
        assert cash['statement'] == 'balance_sheet'
        assert cash['parent'] == 'us-gaap:AssetsCurrent'
        assert cash['order'] == 1.0
        print("  PASS: Hierarchy correct for Cash")
        
        assets_current = concepts['us-gaap:AssetsCurrent']
        assert assets_current['parent'] == 'us-gaap:Assets'
        print("  PASS: Hierarchy correct for AssetsCurrent")
        
        # Check metadata
        metadata = result['metadata']
        assert metadata['total_concepts'] == 3
        assert 'balance_sheet' in metadata['statements']
        print("  PASS: Metadata correct")
        
    finally:
        # Cleanup
        temp_path.unlink()


def test_taxonomy_authority_reader():
    """Test taxonomy authority reader."""
    print("\nTesting TaxonomyAuthorityReader...")
    reader = TaxonomyAuthorityReader()
    assert reader is not None
    assert hasattr(reader, 'presentation_parser')
    print("  PASS: Reader initialized")


def test_normalize_concept_name():
    """Test concept name normalization."""
    print("\nTesting concept name normalization...")
    reader = TaxonomyAuthorityReader()
    
    assert reader._normalize_concept_name("us-gaap_Cash") == "us-gaap:Cash"
    print("  PASS: Underscore to colon")
    
    assert reader._normalize_concept_name("us-gaap:Cash") == "us-gaap:Cash"
    print("  PASS: Already colon")
    
    assert reader._normalize_concept_name("") == ""
    print("  PASS: Empty string")


def test_get_concept_authority():
    """Test getting concept authority."""
    print("\nTesting concept authority lookup...")
    reader = TaxonomyAuthorityReader()
    
    # Test not found
    hierarchy = {'concepts': {}, 'metadata': {}}
    authority = reader.get_concept_authority('unknown:Concept', hierarchy)
    assert authority['has_authority'] is False
    print("  PASS: Unknown concept handled")
    
    # Test found
    hierarchy = {
        'concepts': {
            'us-gaap:Cash': {
                'statement': 'balance_sheet',
                'role_uri': 'http://fasb.org/us-gaap/role/statement/StatementOfFinancialPosition',
                'parent': 'us-gaap:AssetsCurrent',
                'order': 1.0
            }
        },
        'metadata': {}
    }
    
    authority = reader.get_concept_authority('us-gaap:Cash', hierarchy)
    assert authority['has_authority'] is True
    assert authority['statement'] == 'balance_sheet'
    print("  PASS: Known concept found")


def test_validate_statement_placement():
    """Test statement placement validation."""
    print("\nTesting statement placement validation...")
    reader = TaxonomyAuthorityReader()
    
    hierarchy = {
        'concepts': {
            'us-gaap:Cash': {
                'statement': 'balance_sheet',
                'parent': 'us-gaap:AssetsCurrent',
                'order': 1.0
            }
        },
        'metadata': {}
    }
    
    # Test exact match
    validation = reader.validate_statement_placement(
        'us-gaap:Cash',
        'balance_sheet',
        hierarchy
    )
    assert validation['is_valid'] is True
    assert validation['agreement'] == 'exact_match'
    print("  PASS: Exact match validated")
    
    # Test override needed
    validation = reader.validate_statement_placement(
        'us-gaap:Cash',
        'income_statement',
        hierarchy
    )
    assert validation['is_valid'] is False
    assert validation['agreement'] == 'override_needed'
    assert validation['action'] == 'override'
    print("  PASS: Override detected")
    
    # Test no authority
    validation = reader.validate_statement_placement(
        'unknown:Concept',
        'income_statement',
        hierarchy
    )
    assert validation['is_valid'] is True
    assert validation['agreement'] == 'no_authority'
    print("  PASS: No authority handled")


def test_convenience_function():
    """Test convenience function."""
    print("\nTesting convenience function...")
    reader = get_taxonomy_authority(
        taxonomy_paths=[Path('/fake/path')],
        cache_key='test'
    )
    assert isinstance(reader, TaxonomyAuthorityReader)
    print("  PASS: Convenience function works")


def test_filing_taxonomy_detector_initialization():
    """Test FilingTaxonomyDetector initialization."""
    print("\nTesting FilingTaxonomyDetector initialization...")
    detector = FilingTaxonomyDetector()
    assert detector is not None
    assert hasattr(detector, 'STANDARD_TAXONOMIES')
    assert hasattr(detector, 'taxonomy_base_path')
    print("  PASS: Detector initialized")


def test_extract_namespace_from_url():
    """Test namespace extraction from URLs."""
    print("\nTesting namespace extraction from URLs...")
    detector = FilingTaxonomyDetector()
    
    # Test US-GAAP
    ns = detector._extract_namespace_from_url(
        'http://fasb.org/us-gaap/2024/us-gaap-2024-01-31.xsd'
    )
    assert ns == 'us-gaap'
    print("  PASS: US-GAAP extracted")
    
    # Test IFRS
    ns = detector._extract_namespace_from_url(
        'http://xbrl.ifrs.org/taxonomy/2024/ifrs-full.xsd'
    )
    assert ns == 'ifrs'
    print("  PASS: IFRS extracted")
    
    # Test none
    ns = detector._extract_namespace_from_url('http://example.com/other.xsd')
    assert ns is None
    print("  PASS: Non-taxonomy URL handled")


def test_extract_namespaces_from_facts():
    """Test namespace extraction from facts data."""
    print("\nTesting namespace extraction from facts...")
    detector = FilingTaxonomyDetector()
    
    sample_data = {
        'metadata': {
            'schema_refs': [
                'http://fasb.org/us-gaap/2024/us-gaap-2024-01-31.xsd'
            ],
            'namespaces': {
                'us-gaap': 'http://fasb.org/us-gaap/2024',
                'plug': 'http://www.plugpower.com/20241231'
            }
        },
        'facts': [
            {'concept_qname': 'us-gaap:Cash'},
            {'concept_qname': 'us-gaap:Assets'},
            {'concept_qname': 'plug:HydrogenRevenue'}
        ]
    }
    
    namespaces = detector._extract_namespaces_from_facts(sample_data)
    
    assert 'us-gaap' in namespaces
    assert 'plug' in namespaces
    print("  PASS: Namespaces extracted correctly")


def test_determine_standard_taxonomy():
    """Test standard taxonomy determination."""
    print("\nTesting standard taxonomy determination...")
    detector = FilingTaxonomyDetector()
    
    namespaces = {'us-gaap', 'plug', 'dei'}
    metadata = {'market': 'sec', 'filing_date': '2024-12-31'}
    
    result = detector._determine_standard_taxonomy(namespaces, metadata)
    
    assert result['taxonomy'] == 'us-gaap'
    assert result['version'] == '2024'
    print("  PASS: Standard taxonomy determined")


def test_find_extension_namespace():
    """Test extension namespace detection."""
    print("\nTesting extension namespace detection...")
    detector = FilingTaxonomyDetector()
    
    # With extension
    namespaces = {'us-gaap', 'plug', 'dei'}
    extension = detector._find_extension_namespace(namespaces)
    assert extension == 'plug'
    print("  PASS: Extension namespace found")
    
    # Without extension
    namespaces = {'us-gaap', 'dei'}
    extension = detector._find_extension_namespace(namespaces)
    assert extension is None
    print("  PASS: No extension handled")


def test_detect_from_sample_facts():
    """Test full detection from sample facts file."""
    print("\nTesting full detection from sample facts...")
    detector = FilingTaxonomyDetector()
    
    # Create sample facts file
    sample_facts = {
        'metadata': {
            'filing_id': 'TEST_10K_2024',
            'company': 'Test Company',
            'ticker': 'TEST',
            'filing_date': '2024-12-31',
            'market': 'sec',
            'schema_refs': [
                'http://fasb.org/us-gaap/2024/us-gaap-2024-01-31.xsd'
            ],
            'namespaces': {
                'us-gaap': 'http://fasb.org/us-gaap/2024',
                'test': 'http://www.test.com/20241231'
            }
        },
        'facts': [
            {'concept_qname': 'us-gaap:Cash', 'value': '1000'},
            {'concept_qname': 'us-gaap:Assets', 'value': '5000'},
            {'concept_qname': 'test:CustomRevenue', 'value': '2000'}
        ]
    }
    
    # Write to temp file
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.json',
        delete=False
    ) as f:
        json.dump(sample_facts, f)
        temp_path = Path(f.name)
    
    try:
        result = detector.detect_from_parsed_facts(temp_path)
        
        # Verify results
        assert result['standard_taxonomy'] == 'us-gaap'
        assert result['standard_version'] == '2024'
        assert result['extension_namespace'] == 'test'
        assert 'us-gaap' in result['namespaces']
        assert 'test' in result['namespaces']
        assert result['metadata']['company'] == 'Test Company'
        
        print("  PASS: Full detection successful")
        print(f"    Standard: {result['standard_taxonomy']}-{result['standard_version']}")
        print(f"    Extension: {result['extension_namespace']}")
        print(f"    Namespaces: {result['namespaces']}")
        
    finally:
        # Cleanup
        temp_path.unlink()


def test_statement_loader_initialization():
    """Test StatementLoader initialization."""
    print("\nTesting StatementLoader initialization...")
    loader = StatementLoader()
    assert loader is not None
    assert hasattr(loader, 'STATEMENT_TYPES')
    print("  PASS: Loader initialized")


def test_normalize_ccq_facts():
    """Test CCQ fact normalization."""
    print("\nTesting CCQ fact normalization...")
    loader = StatementLoader()
    
    ccq_line_items = [
        {
            'qname': 'us-gaap:Cash',
            'label': 'Cash and cash equivalents',
            'value': '1000000',
            'unit': 'USD',
            'classification': {'statement': 'balance_sheet'}
        }
    ]
    
    normalized = loader._normalize_ccq_facts(ccq_line_items)
    
    assert len(normalized) == 1
    assert normalized[0]['concept_qname'] == 'us-gaap:Cash'
    assert normalized[0]['value'] == '1000000'
    assert normalized[0]['source'] == 'ccq'
    print("  PASS: CCQ facts normalized")


def test_fact_reconciler_initialization():
    """Test FactReconciler initialization."""
    print("\nTesting FactReconciler initialization...")
    
    mock_hierarchy = {
        'concepts': {
            'us-gaap:Cash': {
                'statement': 'balance_sheet',
                'parent': 'us-gaap:AssetsCurrent'
            }
        },
        'metadata': {}
    }
    
    reconciler = FactReconciler(mock_hierarchy)
    assert reconciler is not None
    assert reconciler.taxonomy_concepts is not None
    print("  PASS: Reconciler initialized")


def test_reconcile_unanimous_agreement():
    """Test reconciliation when both mappers agree with taxonomy."""
    print("\nTesting unanimous agreement reconciliation...")
    
    mock_hierarchy = {
        'concepts': {
            'us-gaap:Cash': {
                'statement': 'balance_sheet'
            }
        },
        'metadata': {}
    }
    
    reconciler = FactReconciler(mock_hierarchy)
    
    map_pro_facts = [
        {'concept_qname': 'us-gaap:Cash', 'value': '1000', 'source': 'map_pro'}
    ]
    
    ccq_facts = [
        {'concept_qname': 'us-gaap:Cash', 'value': '1000', 'source': 'ccq'}
    ]
    
    result = reconciler.reconcile_statement(
        'balance_sheet',
        map_pro_facts,
        ccq_facts
    )
    
    assert result['statistics']['unanimous'] == 1
    assert result['statistics']['total_concepts'] == 1
    assert len(result['reconciled_facts']) == 1
    print("  PASS: Unanimous agreement detected")


def test_statement_reconciler_initialization():
    """Test StatementReconciler initialization."""
    print("\nTesting StatementReconciler initialization...")
    
    mock_hierarchy = {
        'concepts': {},
        'metadata': {}
    }
    
    reconciler = StatementReconciler(mock_hierarchy)
    assert reconciler is not None
    assert hasattr(reconciler, 'statement_loader')
    assert hasattr(reconciler, 'fact_reconciler')
    print("  PASS: Statement reconciler initialized")


def test_joint_statement_constructor_initialization():
    """Test JointStatementConstructor initialization."""
    print("\nTesting JointStatementConstructor initialization...")
    constructor = JointStatementConstructor()
    assert constructor is not None
    print("  PASS: Constructor initialized")


def test_build_line_item():
    """Test building a line item from reconciled fact."""
    print("\nTesting line item construction...")
    constructor = JointStatementConstructor()
    
    fact = {
        'concept_qname': 'us-gaap:Cash',
        'value': '1000000',
        'label': 'Cash and cash equivalents',
        'authority': 'taxonomy_confirmed',
        'taxonomy_confirmed': True,
        'agreement': 'unanimous',
        'ccq_also_found': True
    }
    
    line_item = constructor._build_line_item(fact)
    
    assert line_item['concept_qname'] == 'us-gaap:Cash'
    assert line_item['value'] == '1000000'
    assert line_item['authority']['source'] == 'taxonomy_confirmed'
    assert line_item['authority']['taxonomy_confirmed'] is True
    assert 'map_pro' in line_item['sources']
    assert 'ccq' in line_item['sources']
    print("  PASS: Line item constructed correctly")


def test_null_quality_handler_initialization():
    """Test NullQualityHandler initialization."""
    print("\nTesting NullQualityHandler initialization...")
    handler = NullQualityHandler()
    assert handler is not None
    print("  PASS: Null quality handler initialized")


def test_extract_null_concepts():
    """Test extracting concepts from null quality data."""
    print("\nTesting null concept extraction...")
    handler = NullQualityHandler()
    
    null_facts = [
        {'concept_qname': 'us-gaap:Concept1', 'null_reason': 'missing_value'},
        {'concept_qname': 'us-gaap:Concept2', 'null_reason': 'invalid_format'}
    ]
    
    concepts = handler._extract_null_concepts(null_facts)
    
    assert 'us-gaap:Concept1' in concepts
    assert 'us-gaap:Concept2' in concepts
    assert len(concepts) == 2
    print("  PASS: Null concepts extracted")


def test_compare_null_quality():
    """Test null quality comparison between mappers."""
    print("\nTesting null quality comparison...")
    handler = NullQualityHandler()
    
    map_pro_concepts = {'us-gaap:A', 'us-gaap:B', 'us-gaap:C'}
    ccq_concepts = {'us-gaap:B', 'us-gaap:C', 'us-gaap:D'}
    
    comparison = handler._compare_null_quality(map_pro_concepts, ccq_concepts)
    
    assert len(comparison['common_nulls']) == 2  # B and C
    assert len(comparison['map_pro_only']) == 1  # A
    assert len(comparison['ccq_only']) == 1      # D
    assert comparison['agreement_rate'] == 50.0  # 2 common out of 4 total
    print("  PASS: Null quality compared correctly")


def test_output_writer_initialization():
    """Test OutputWriter initialization."""
    print("\nTesting OutputWriter initialization...")
    
    # Use temp directory for testing
    import tempfile
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        writer = OutputWriter(temp_dir)
        assert writer is not None
        assert writer.base_path == temp_dir
        assert temp_dir.exists()
        print("  PASS: Output writer initialized")
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_create_output_directory():
    """Test output directory creation."""
    print("\nTesting output directory creation...")
    
    import tempfile
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        writer = OutputWriter(temp_dir)
        
        output_dir = writer._create_output_directory(
            market='sec',
            company='Test Company',
            form_type='10-K',
            filing_date='2024-12-31'
        )
        
        assert output_dir.exists()
        assert 'sec' in str(output_dir)
        assert 'Test_Company' in str(output_dir)
        assert '10-K' in str(output_dir)
        assert '2024-12-31' in str(output_dir)
        print("  PASS: Output directory created with correct structure")
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_reconciliation_reporter_initialization():
    """Test ReconciliationReporter initialization."""
    print("\nTesting ReconciliationReporter initialization...")
    reporter = ReconciliationReporter()
    assert reporter is not None
    print("  PASS: Reporter initialized")


def test_generate_executive_summary():
    """Test executive summary generation."""
    print("\nTesting executive summary generation...")
    reporter = ReconciliationReporter()
    
    mock_reconciliation = {
        'overall_statistics': {
            'total_concepts': 100,
            'unanimous': 85,
            'map_pro_only': 10,
            'ccq_only': 5,
            'taxonomy_override_both': 0
        },
        'taxonomy_coverage': {
            'coverage_rate': 95.0
        }
    }
    
    mock_null_analysis = {
        'map_pro_null_count': 5,
        'ccq_null_count': 3
    }
    
    summary = reporter._generate_executive_summary(
        mock_reconciliation,
        mock_null_analysis
    )
    
    assert summary['total_concepts_reconciled'] == 100
    assert summary['unanimous_agreement'] == 85
    assert summary['unanimous_percentage'] == 85.0
    assert summary['taxonomy_coverage_rate'] == 95.0
    assert summary['overall_quality'] == 'EXCELLENT'  # (85 + 95) / 2 = 90%
    print("  PASS: Executive summary generated")


def test_assess_overall_quality():
    """Test overall quality assessment."""
    print("\nTesting quality assessment...")
    reporter = ReconciliationReporter()
    
    # Test excellent quality
    quality = reporter._assess_overall_quality(95.0, 95.0)
    assert quality == 'EXCELLENT'
    
    # Test good quality
    quality = reporter._assess_overall_quality(85.0, 85.0)
    assert quality == 'GOOD'
    
    # Test fair quality
    quality = reporter._assess_overall_quality(75.0, 75.0)
    assert quality == 'FAIR'
    
    # Test poor quality
    quality = reporter._assess_overall_quality(60.0, 60.0)
    assert quality == 'POOR'
    
    print("  PASS: Quality assessment correct")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("FACT AUTHORITY MANUAL TEST SUITE")
    print("=" * 60)
    
    # Component 1-3 tests (always available)
    core_tests = [
        # Component 1: Taxonomy Authority
        test_presentation_parser_initialization,
        test_classify_statement_role,
        test_extract_concept_from_href,
        test_parse_sample_linkbase,
        test_taxonomy_authority_reader,
        test_normalize_concept_name,
        test_get_concept_authority,
        test_validate_statement_placement,
        test_convenience_function,
        
        # Component 2: Taxonomy Detection
        test_filing_taxonomy_detector_initialization,
        test_extract_namespace_from_url,
        test_extract_namespaces_from_facts,
        test_determine_standard_taxonomy,
        test_find_extension_namespace,
        test_detect_from_sample_facts,
        
        # Component 3: Statement Reconciliation
        test_statement_loader_initialization,
        test_normalize_ccq_facts,
        test_fact_reconciler_initialization,
        test_reconcile_unanimous_agreement,
        test_statement_reconciler_initialization,
    ]
    
    # Component 4 tests (may not be available in flat structure)
    component_4_tests = [
        test_joint_statement_constructor_initialization,
        test_build_line_item,
        test_null_quality_handler_initialization,
        test_extract_null_concepts,
        test_compare_null_quality,
        test_output_writer_initialization,
        test_create_output_directory,
        test_reconciliation_reporter_initialization,
        test_generate_executive_summary,
        test_assess_overall_quality
    ]
    
    # Combine tests
    tests = core_tests
    if COMPONENT_4_AVAILABLE:
        tests.extend(component_4_tests)
    else:
        print("\nNote: Component 4 tests skipped (imports unavailable)")
        print("This is expected if running from flat file structure.\n")
    
    passed = 0
    failed = 0
    skipped = 0 if COMPONENT_4_AVAILABLE else len(component_4_tests)
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n  FAIL: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed", end="")
    if skipped > 0:
        print(f", {skipped} skipped (Component 4)")
    else:
        print()
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)