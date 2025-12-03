"""
Quality Report Comparator
==========================

Specialized comparator for quality reports:
- Null Quality

Handles quality report comparison logic.
"""

from typing import Dict, Any, Optional

from core.system_logger import get_logger
from core.data_paths import CCQPaths

from .comparison_engine import ComparisonEngine

logger = get_logger(__name__)


class QualityReportComparator:
    """
    Comparator for quality reports.
    
    Handles null quality report comparisons.
    """
    
    def __init__(self, paths: CCQPaths):
        """Initialize with CCQPaths instance."""
        self.paths = paths
        self.engine = ComparisonEngine(paths)
    
    # ========================================================================
    # PUBLIC API - Null Quality Comparison
    # ========================================================================
    
    def compare_null_quality(
        self,
        market: str,
        company: str,
        form_type: str,
        filing_date: str
    ) -> Dict[str, Any]:
        """
        Compare null quality reports from Map Pro and CCQ Mapper.
        
        Validates that both systems have similar data quality assessments.
        """
        logger.info(f"Comparing null quality reports for {company} {form_type} {filing_date}")
        
        # Find files
        map_pro_file = self.engine.find_statement_file(
            self.paths.input_mapped,
            market, company, form_type, filing_date,
            'null_quality.json'
        )
        
        ccq_file = self.engine.find_statement_file(
            self.paths.mapper_output,
            market, company, form_type, filing_date,
            'null_quality.json'
        )
        
        # Check if files exist
        if not map_pro_file:
            return {
                'success': False,
                'error': f'Map Pro null quality report not found for {company} {form_type} {filing_date}',
                'searched_in': str(self.paths.input_mapped)
            }
        
        if not ccq_file:
            return {
                'success': False,
                'error': f'CCQ null quality report not found for {company} {form_type} {filing_date}',
                'searched_in': str(self.paths.mapper_output)
            }
        
        logger.info(f"✓ Found Map Pro file: {map_pro_file}")
        logger.info(f"✓ Found CCQ file: {ccq_file}")
        
        # Load reports
        try:
            map_pro_report = self.engine.load_statement(map_pro_file)
            ccq_report = self.engine.load_statement(ccq_file)
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to load null quality reports: {e}'
            }
        
        # Compare reports
        comparison = self._compare_null_quality_reports(map_pro_report, ccq_report)
        
        # Add metadata
        from datetime import datetime
        comparison['files'] = {
            'map_pro': str(map_pro_file),
            'ccq': str(ccq_file)
        }
        comparison['compared_at'] = datetime.now().isoformat()
        
        return comparison
    
    # ========================================================================
    # PRIVATE - Comparison Logic
    # ========================================================================
    
    def _compare_null_quality_reports(
        self,
        map_pro_report: Dict[str, Any],
        ccq_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare null quality reports from both systems."""
        logger.info("Comparing null quality metrics...")
        
        # Extract Map Pro metrics
        map_pro_metrics = {
            'overall_score': map_pro_report.get('overall_quality_score'),
            'grade': map_pro_report.get('data_quality_grade'),
            'total_facts': map_pro_report.get('parsed_facts_analysis', {}).get('total_facts'),
            'total_nulls': map_pro_report.get('parsed_facts_analysis', {}).get('total_nulls'),
            'null_percentage': map_pro_report.get('parsed_facts_analysis', {}).get('null_percentage'),
            'action_required': map_pro_report.get('action_required')
        }
        
        # Extract CCQ metrics
        ccq_metrics = {
            'overall_score': ccq_report.get('quality_score', {}).get('score'),
            'grade': ccq_report.get('quality_score', {}).get('grade'),
            'total_line_items': ccq_report.get('total_line_items'),
            'total_nulls': ccq_report.get('statistics', {}).get('total_nulls'),
            'validation_type': ccq_report.get('validation_type')
        }
        
        # Compare scores
        scores_match = False
        score_difference = None
        
        if map_pro_metrics['overall_score'] is not None and ccq_metrics['overall_score'] is not None:
            score_difference = abs(map_pro_metrics['overall_score'] - ccq_metrics['overall_score'])
            scores_match = score_difference < 5.0
        
        # Compare grades
        grades_match = map_pro_metrics['grade'] == ccq_metrics['grade']
        
        # Compare null counts
        nulls_match = map_pro_metrics['total_nulls'] == ccq_metrics['total_nulls']
        
        # Build report
        return {
            'success': True,
            'report_type': 'null_quality',
            'summary': {
                'scores_match': scores_match,
                'score_difference': score_difference,
                'grades_match': grades_match,
                'nulls_match': nulls_match,
                'overall_agreement': scores_match and grades_match and nulls_match
            },
            'map_pro_metrics': map_pro_metrics,
            'ccq_metrics': ccq_metrics,
            'analysis': {
                'score_interpretation': self._interpret_score_difference(score_difference),
                'grade_interpretation': self._interpret_grade_match(
                    map_pro_metrics['grade'], 
                    ccq_metrics['grade']
                ),
                'null_interpretation': self._interpret_null_match(
                    map_pro_metrics['total_nulls'], 
                    ccq_metrics['total_nulls']
                )
            },
            'architectural_differences': [
                "Map Pro uses text-based null explanation search",
                "CCQ uses property-based null pattern detection",
                "Both systems independently assess data quality",
                "Agreement validates that quality issues are objective"
            ]
        }
    
    # ========================================================================
    # PRIVATE - Interpretation Helpers
    # ========================================================================
    
    def _interpret_score_difference(self, difference: Optional[float]) -> str:
        """Interpret the quality score difference."""
        if difference is None:
            return "Cannot compare - one or both scores missing"
        
        if difference < 1.0:
            return "Excellent agreement - scores nearly identical"
        elif difference < 5.0:
            return "Good agreement - minor scoring differences"
        elif difference < 10.0:
            return "Moderate agreement - some methodology differences"
        else:
            return "Significant disagreement - requires investigation"
    
    def _interpret_grade_match(self, map_pro_grade: str, ccq_grade: str) -> str:
        """Interpret grade match/mismatch."""
        if map_pro_grade == ccq_grade:
            return f"Perfect match - both systems grade as '{map_pro_grade}'"
        else:
            return f"Grade mismatch - Map Pro: '{map_pro_grade}', CCQ: '{ccq_grade}'"
    
    def _interpret_null_match(self, map_pro_nulls: int, ccq_nulls: int) -> str:
        """Interpret null count match/mismatch."""
        if map_pro_nulls == ccq_nulls:
            if map_pro_nulls == 0:
                return "Perfect - both systems found zero nulls"
            else:
                return f"Match - both systems found {map_pro_nulls} nulls"
        else:
            return f"Mismatch - Map Pro: {map_pro_nulls} nulls, CCQ: {ccq_nulls} nulls"
    
    # ========================================================================
    # PUBLIC API - Reporting
    # ========================================================================
    
    def print_quality_report(self, comparison: Dict[str, Any]):
        """Print a human-readable null quality comparison report."""
        print("\n" + "="*80)
        print("NULL QUALITY COMPARISON REPORT")
        print("="*80)
        
        summary = comparison['summary']
        map_pro = comparison['map_pro_metrics']
        ccq = comparison['ccq_metrics']
        analysis = comparison['analysis']
        
        print(f"\n📊 SUMMARY:")
        print(f"  Overall Agreement: {'✓ YES' if summary['overall_agreement'] else '✗ NO'}")
        print(f"  Scores Match: {'✓' if summary['scores_match'] else '✗'}")
        print(f"  Grades Match: {'✓' if summary['grades_match'] else '✗'}")
        print(f"  Null Counts Match: {'✓' if summary['nulls_match'] else '✗'}")
        
        print(f"\n📈 MAP PRO METRICS:")
        print(f"  Score: {map_pro['overall_score']}")
        print(f"  Grade: {map_pro['grade']}")
        print(f"  Total Facts: {map_pro['total_facts']}")
        print(f"  Total Nulls: {map_pro['total_nulls']}")
        print(f"  Null Percentage: {map_pro['null_percentage']}%")
        
        print(f"\n📈 CCQ METRICS:")
        print(f"  Score: {ccq['overall_score']}")
        print(f"  Grade: {ccq['grade']}")
        print(f"  Total Line Items: {ccq['total_line_items']}")
        print(f"  Total Nulls: {ccq['total_nulls']}")
        print(f"  Validation Type: {ccq['validation_type']}")
        
        print(f"\n🔍 ANALYSIS:")
        print(f"  Score: {analysis['score_interpretation']}")
        print(f"  Grade: {analysis['grade_interpretation']}")
        print(f"  Nulls: {analysis['null_interpretation']}")
        
        print("\n" + "="*80)


__all__ = ['QualityReportComparator']