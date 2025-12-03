# File: engines/ccq_mapper/analysis/duplicate_risk_assessor.py

"""
Duplicate Risk Assessor
========================

Assesses risk levels based on duplicate characteristics and patterns.

Risk Factors:
- High-significance duplicates with material variance
- Mapping-introduced duplicates
- Cross-statement duplication
- Systematic concentration patterns

Generates actionable recommendations for addressing identified risks.
"""

from typing import Dict, Any, List

from core.system_logger import get_logger

logger = get_logger(__name__)


# Risk levels
RISK_CRITICAL = 'CRITICAL'
RISK_HIGH = 'HIGH'
RISK_MEDIUM = 'MEDIUM'
RISK_LOW = 'LOW'

# Significance levels (imported for reference)
SIGNIFICANCE_HIGH = 'HIGH'
SIGNIFICANCE_MEDIUM = 'MEDIUM'
SIGNIFICANCE_LOW = 'LOW'


class DuplicateRiskAssessor:
    """
    Assesses risk levels and generates recommendations.
    
    Responsibilities:
    - Calculate risk scores based on duplicate characteristics
    - Identify specific concerns
    - Generate actionable recommendations
    - Prioritize issues by severity
    
    Does NOT:
    - Modify data
    - Make decisions about handling duplicates
    - Implement fixes
    """
    
    def __init__(self):
        """Initialize risk assessor."""
        self.logger = logger
    
    def assess_risk(
        self,
        enriched_duplicates: List[Dict[str, Any]],
        patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess overall risk level based on duplicates and patterns.
        
        Args:
            enriched_duplicates: List of enriched duplicate profiles
            patterns: Detected patterns from DuplicatePatternDetector
            
        Returns:
            Comprehensive risk assessment dictionary
        """
        self.logger.debug(f"Assessing risk for {len(enriched_duplicates)} duplicate groups")
        
        concerns = []
        risk_score = 0
        
        # Check for high-significance duplicates with material variance
        high_sig_concern, high_sig_score = self._assess_high_significance_risk(
            enriched_duplicates
        )
        if high_sig_concern:
            concerns.append(high_sig_concern)
            risk_score += high_sig_score
        
        # Check for mapping-introduced duplicates
        mapping_concern, mapping_score = self._assess_mapping_introduced_risk(
            enriched_duplicates
        )
        if mapping_concern:
            concerns.append(mapping_concern)
            risk_score += mapping_score
        
        # Check for cross-statement pattern
        cross_stmt_concern, cross_stmt_score = self._assess_cross_statement_risk(
            patterns
        )
        if cross_stmt_concern:
            concerns.append(cross_stmt_concern)
            risk_score += cross_stmt_score
        
        # Check for systematic pattern
        systematic_concern, systematic_score = self._assess_systematic_risk(
            patterns
        )
        if systematic_concern:
            concerns.append(systematic_concern)
            risk_score += systematic_score
        
        # Determine overall risk level
        overall_risk = self._calculate_overall_risk(risk_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(concerns, enriched_duplicates)
        
        return {
            'overall_risk': overall_risk,
            'risk_score': risk_score,
            'concerns': concerns,
            'recommendations': recommendations,
            'summary': self._generate_risk_summary(overall_risk, risk_score, len(concerns))
        }
    
    def _assess_high_significance_risk(
        self,
        enriched_duplicates: List[Dict[str, Any]]
    ) -> tuple:
        """
        Assess risk from high-significance duplicates with material variance.
        
        Returns:
            Tuple of (concern_dict or None, risk_score)
        """
        high_sig_material = [
            dup for dup in enriched_duplicates
            if dup['significance']['level'] == SIGNIFICANCE_HIGH
            and dup['variance_percentage'] > 1.0
        ]
        
        if not high_sig_material:
            return None, 0
        
        # Higher variance = higher risk
        max_variance = max(dup['variance_percentage'] for dup in high_sig_material)
        
        # Base score + variance multiplier
        if max_variance > 10:
            risk_score = 40
        elif max_variance > 5:
            risk_score = 35
        else:
            risk_score = 30
        
        concern = {
            'level': 'HIGH',
            'type': 'high_significance_material_variance',
            'count': len(high_sig_material),
            'max_variance': round(max_variance, 2),
            'message': (
                f'{len(high_sig_material)} core financial concepts with material variance '
                f'(max: {max_variance:.1f}%)'
            ),
            'examples': [
                {
                    'concept': dup['concept'],
                    'variance': dup['variance_percentage'],
                    'statement': dup['classification']['statement_type']
                }
                for dup in sorted(
                    high_sig_material,
                    key=lambda x: x['variance_percentage'],
                    reverse=True
                )[:5]
            ]
        }
        
        return concern, risk_score
    
    def _assess_mapping_introduced_risk(
        self,
        enriched_duplicates: List[Dict[str, Any]]
    ) -> tuple:
        """
        Assess risk from mapping-introduced duplicates.
        
        Returns:
            Tuple of (concern_dict or None, risk_score)
        """
        mapping_introduced = [
            dup for dup in enriched_duplicates
            if dup['source'] == 'MAPPING_INTRODUCED'
        ]
        
        if not mapping_introduced:
            return None, 0
        
        # Calculate percentage of total
        total = len(enriched_duplicates)
        mapping_pct = (len(mapping_introduced) / total) * 100 if total > 0 else 0
        
        # Higher percentage = higher risk
        if mapping_pct > 50:
            risk_score = 25
        elif mapping_pct > 25:
            risk_score = 20
        else:
            risk_score = 15
        
        concern = {
            'level': 'MEDIUM',
            'type': 'mapping_introduced_duplicates',
            'count': len(mapping_introduced),
            'percentage': round(mapping_pct, 1),
            'message': (
                f'{len(mapping_introduced)} duplicates ({mapping_pct:.1f}%) '
                f'created by mapper processing'
            ),
            'examples': [dup['concept'] for dup in mapping_introduced[:5]]
        }
        
        return concern, risk_score
    
    def _assess_cross_statement_risk(
        self,
        patterns: Dict[str, Any]
    ) -> tuple:
        """
        Assess risk from cross-statement duplication pattern.
        
        Returns:
            Tuple of (concern_dict or None, risk_score)
        """
        cross_statement = patterns.get('cross_statement', {})
        
        if not cross_statement.get('detected'):
            return None, 0
        
        count = cross_statement.get('count', 0)
        
        # More cross-statement duplicates = higher risk
        if count > 10:
            risk_score = 30
        elif count > 5:
            risk_score = 25
        else:
            risk_score = 20
        
        concern = {
            'level': 'HIGH',
            'type': 'cross_statement_duplicates',
            'count': count,
            'message': (
                f'{count} concepts appearing in multiple financial statements - '
                f'possible classification issues'
            ),
            'examples': list(cross_statement.get('concepts', {}).items())[:5]
        }
        
        return concern, risk_score
    
    def _assess_systematic_risk(
        self,
        patterns: Dict[str, Any]
    ) -> tuple:
        """
        Assess risk from systematic concentration pattern.
        
        Returns:
            Tuple of (concern_dict or None, risk_score)
        """
        systematic = patterns.get('systematic', {})
        
        if not systematic.get('detected'):
            return None, 0
        
        concentration = max(
            systematic.get('statement_concentration', 0),
            systematic.get('source_concentration', 0)
        )
        
        # Higher concentration = higher risk
        if concentration > 85:
            risk_score = 20
        elif concentration > 75:
            risk_score = 15
        else:
            risk_score = 10
        
        concern = {
            'level': 'MEDIUM',
            'type': 'systematic_duplication',
            'concentration': round(concentration, 1),
            'dominant_statement': systematic.get('dominant_statement'),
            'dominant_source': systematic.get('dominant_source'),
            'message': (
                f'Systematic duplication detected: {concentration:.1f}% concentrated '
                f'in {systematic.get("dominant_statement", "unknown")} '
                f'from {systematic.get("dominant_source", "unknown")} source'
            ),
            'distribution': {
                'by_statement': systematic.get('statement_distribution', {}),
                'by_source': systematic.get('source_distribution', {})
            }
        }
        
        return concern, risk_score
    
    def _calculate_overall_risk(self, risk_score: int) -> str:
        """
        Calculate overall risk level from risk score.
        
        Args:
            risk_score: Cumulative risk score
            
        Returns:
            Risk level string
        """
        if risk_score >= 50:
            return RISK_CRITICAL
        elif risk_score >= 30:
            return RISK_HIGH
        elif risk_score >= 15:
            return RISK_MEDIUM
        else:
            return RISK_LOW
    
    def _generate_recommendations(
        self,
        concerns: List[Dict[str, Any]],
        enriched_duplicates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate actionable recommendations based on concerns.
        
        Args:
            concerns: List of identified concerns
            enriched_duplicates: List of enriched duplicate profiles
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        # Recommendations for high-significance variance
        high_sig_concern = next(
            (c for c in concerns if c['type'] == 'high_significance_material_variance'),
            None
        )
        
        if high_sig_concern:
            for example in high_sig_concern.get('examples', [])[:3]:
                recommendations.append({
                    'priority': 'URGENT',
                    'category': 'data_quality',
                    'action': f"Review {example['concept']}",
                    'reason': (
                        f"{example['variance']:.1f}% variance in "
                        f"{example['statement']}"
                    ),
                    'steps': [
                        'Compare values across duplicate facts',
                        'Verify source data accuracy',
                        'Check for unit or scale inconsistencies',
                        'Review context dimensions'
                    ]
                })
        
        # Recommendations for mapping issues
        if any(c['type'] == 'mapping_introduced_duplicates' for c in concerns):
            recommendations.append({
                'priority': 'HIGH',
                'category': 'mapper_logic',
                'action': 'Investigate mapper duplicate creation',
                'reason': 'Duplicates being introduced during processing',
                'steps': [
                    'Review mapper transformation logic',
                    'Check for duplicate concept mappings',
                    'Verify context handling in mapper',
                    'Consider adding deduplication step'
                ]
            })
        
        # Recommendations for cross-statement issues
        if any(c['type'] == 'cross_statement_duplicates' for c in concerns):
            recommendations.append({
                'priority': 'HIGH',
                'category': 'classification',
                'action': 'Review statement classification logic',
                'reason': 'Concepts appearing in multiple statements',
                'steps': [
                    'Audit statement classifier rules',
                    'Review concept-to-statement mappings',
                    'Check for ambiguous concept classifications',
                    'Consider stricter classification criteria'
                ]
            })
        
        # General recommendation for source data issues
        source_data_count = sum(
            1 for dup in enriched_duplicates
            if dup['source'] == 'SOURCE_DATA'
        )
        
        total = len(enriched_duplicates)
        source_pct = (source_data_count / total) * 100 if total > 0 else 0
        
        if source_pct > 80:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'source_data',
                'action': 'Assess filing data quality',
                'reason': f'{source_pct:.1f}% of duplicates exist in source data',
                'steps': [
                    'Review filing for duplicate facts',
                    'Contact filer if data quality issues persist',
                    'Document known source data issues',
                    'Consider source-specific handling rules'
                ]
            })
        
        return recommendations
    
    def _generate_risk_summary(
        self,
        overall_risk: str,
        risk_score: int,
        concern_count: int
    ) -> str:
        """
        Generate human-readable risk summary.
        
        Args:
            overall_risk: Overall risk level
            risk_score: Risk score
            concern_count: Number of concerns identified
            
        Returns:
            Summary string
        """
        if overall_risk == RISK_CRITICAL:
            return (
                f'CRITICAL RISK (score: {risk_score}): '
                f'{concern_count} major concerns identified. '
                f'Immediate investigation required.'
            )
        elif overall_risk == RISK_HIGH:
            return (
                f'HIGH RISK (score: {risk_score}): '
                f'{concern_count} concerns identified. '
                f'Prompt review recommended.'
            )
        elif overall_risk == RISK_MEDIUM:
            return (
                f'MEDIUM RISK (score: {risk_score}): '
                f'{concern_count} concerns identified. '
                f'Review during normal QA process.'
            )
        else:
            return (
                f'LOW RISK (score: {risk_score}): '
                f'Duplicates within acceptable parameters. '
                f'Standard monitoring sufficient.'
            )


__all__ = [
    'DuplicateRiskAssessor',
    'RISK_CRITICAL',
    'RISK_HIGH',
    'RISK_MEDIUM',
    'RISK_LOW'
]