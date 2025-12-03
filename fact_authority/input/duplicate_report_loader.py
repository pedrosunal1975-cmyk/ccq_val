# File: engines/fact_authority/input/duplicate_report_loader.py
# Path: engines/fact_authority/input/duplicate_report_loader.py

"""
Duplicate Report Loader
=======================

Loads and compares duplicate reports from both mappers.

Responsibilities:
- Load duplicates.json from Map Pro and CCQ
- Normalize different JSON structures
- Compare duplicate findings between mappers
- Generate comparison metrics
- Assess duplicate quality

Does NOT:
- Filter facts based on duplicates
- Make validation decisions
- Modify mapper outputs
"""

import json
from pathlib import Path
from typing import Dict, Any, Set, Tuple, Optional
from core.system_logger import get_logger
from core.name_normalizer import NameNormalizer

logger = get_logger(__name__)


class DuplicateReportLoader:
    """
    Loads and compares duplicate reports from both mappers.
    
    Handles format differences between Map Pro and CCQ duplicate reports,
    normalizing to a common comparison structure.
    """
    
    def __init__(self):
        """Initialize loader."""
        self.logger = logger
    
    def load_reports(
        self,
        map_pro_dir: Path,
        ccq_dir: Path,
        entity_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Load and compare duplicate reports from both mappers.
        
        Handles entity name variations between Map Pro and CCQ.
        For example: VISA_INC. (Map Pro) vs VISA_INC_ (CCQ)
        
        Args:
            map_pro_dir: Directory containing Map Pro output
            ccq_dir: Directory containing CCQ output
            entity_name: Entity name for trying variations if file not found
            
        Returns:
            {
                'map_pro_report': {...},
                'ccq_report': {...},
                'comparison': {...},
                'quality_assessment': {...}
            }
        """
        self.logger.info("Loading duplicate reports from both mappers")
        
        # Load Map Pro report (standard path)
        map_pro_data = self._load_single_report(map_pro_dir / 'duplicates.json', 'Map Pro')
        
        # Load CCQ report with name variation handling
        ccq_data = self._load_ccq_report_with_variations(ccq_dir, entity_name)
        
        # If either failed to load, return minimal structure
        if not map_pro_data or not ccq_data:
            return self._build_unavailable_report(map_pro_data, ccq_data)
        
        # Normalize both reports to common structure
        map_pro_normalized = self._normalize_report(map_pro_data, 'map_pro')
        ccq_normalized = self._normalize_report(ccq_data, 'ccq')
        
        # Compare reports
        comparison = self._compare_reports(map_pro_normalized, ccq_normalized)
        
        # Generate quality assessment
        quality_assessment = self._generate_quality_assessment(
            map_pro_normalized,
            ccq_normalized,
            comparison
        )
        
        self.logger.info(
            f"Duplicate comparison complete: {comparison['agreement_rate']:.1f}% agreement, "
            f"cleaner mapper: {comparison.get('cleaner_mapper', 'unknown')}"
        )
        
        return {
            'map_pro_report': map_pro_normalized,
            'ccq_report': ccq_normalized,
            'comparison': comparison,
            'quality_assessment': quality_assessment
        }
    
    def _load_single_report(
        self,
        file_path: Path,
        mapper_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load a single duplicate report JSON file.
        
        Args:
            file_path: Path to duplicates.json
            mapper_name: Name of mapper (for logging)
            
        Returns:
            Loaded JSON dict or None if failed
        """
        if not file_path.exists():
            self.logger.warning(f"{mapper_name} duplicate report not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.info(f"Loaded {mapper_name} duplicate report from {file_path}")
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse {mapper_name} duplicate report: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error loading {mapper_name} duplicate report: {e}")
            return None
    
    def _load_ccq_report_with_variations(
        self,
        ccq_dir: Path,
        entity_name: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Load CCQ duplicate report with entity name variation handling.
        
        Tries the standard path first, then tries variations if entity_name provided.
        Handles cases like VISA_INC. (Map Pro) vs VISA_INC_ (CCQ).
        
        Args:
            ccq_dir: CCQ directory path constructed with Map Pro entity name
            entity_name: Original entity name to generate variations
            
        Returns:
            Loaded JSON dict or None if not found
        """
        # Try standard path first
        standard_file = ccq_dir / 'duplicates.json'
        if standard_file.exists():
            return self._load_single_report(standard_file, 'CCQ')
        
        # If entity name provided, try variations
        if entity_name:
            self.logger.debug(
                f"CCQ duplicates not found at {standard_file}, "
                f"trying name variations for '{entity_name}'"
            )
            
            # Reconstruct path: ccq_dir should be .../market/entity_name/filing_type/filing_date
            # We need: .../market/{name_variation}/filing_type/filing_date/duplicates.json
            parts = ccq_dir.parts
            
            # Work backwards from end:
            # parts[-1] = filing_date (2025-11-06)
            # parts[-2] = filing_type (10-K)
            # parts[-3] = entity_name (VISA_INC.)
            # parts[-4] = market (sec)
            
            if len(parts) >= 4:
                # Reconstruct market directory (everything up to but not including entity_name)
                market_dir = Path(*parts[:-3])
                filing_type = parts[-2]
                filing_date = parts[-1]
                
                # Generate name variations
                variations = NameNormalizer.generate_variations(entity_name)
                
                for variation in variations:
                    variant_path = market_dir / variation / filing_type / filing_date / 'duplicates.json'
                    
                    if variant_path.exists():
                        self.logger.info(
                            f"Found CCQ duplicates using name variation: {variation}"
                        )
                        return self._load_single_report(variant_path, 'CCQ')
                
                self.logger.warning(
                    f"CCQ duplicate report not found at {ccq_dir / 'duplicates.json'} "
                    f"(tried {len(variations)} name variations)"
                )
            else:
                self.logger.error(f"Unexpected path structure: {ccq_dir}")
        else:
            self.logger.warning(f"CCQ duplicate report not found: {ccq_dir / 'duplicates.json'}")
        return None
    
    def _normalize_report(
        self,
        raw_data: Dict[str, Any],
        mapper: str
    ) -> Dict[str, Any]:
        """
        Normalize duplicate report to common structure.
        
        Extracts key information regardless of JSON format differences.
        
        Args:
            raw_data: Raw JSON data from duplicates.json
            mapper: 'map_pro' or 'ccq'
            
        Returns:
            Normalized report structure
        """
        # Extract summary metrics from top-level fields (not from 'summary' sub-object)
        normalized = {
            'mapper': mapper,
            'total_facts': raw_data.get('total_facts_analyzed', 0),
            'duplicate_facts': raw_data.get('total_duplicate_facts', 0),
            'duplicate_groups': raw_data.get('total_duplicate_groups', 0),
            'duplicate_percentage': raw_data.get('duplicate_percentage', 0.0),
            'severity_counts': raw_data.get('severity_counts', {}),
            
            # Extract duplicate keys by severity
            'critical_duplicates': self._extract_duplicate_keys(
                raw_data.get('critical_findings', [])
            ),
            'major_duplicates': self._extract_duplicate_keys(
                raw_data.get('major_findings', [])
            ),
            'minor_duplicates': self._extract_duplicate_keys(
                raw_data.get('minor_findings', [])
            ),
            'redundant_duplicates': self._extract_duplicate_keys(
                raw_data.get('redundant_findings', [])
            ),
            
            # All duplicates (union of all severities)
            'all_duplicate_keys': set(),
            
            # Flags
            'has_critical': raw_data.get('has_critical_duplicates', False),
            'has_major': raw_data.get('has_major_duplicates', False),
            
            # Quality assessment
            'quality_assessment': raw_data.get('quality_assessment', ''),
            
            # Raw findings for detailed analysis
            'critical_findings': raw_data.get('critical_findings', []),
            'major_findings': raw_data.get('major_findings', [])
        }
        
        # Compute all_duplicate_keys as union
        normalized['all_duplicate_keys'] = (
            normalized['critical_duplicates'] |
            normalized['major_duplicates'] |
            normalized['minor_duplicates'] |
            normalized['redundant_duplicates']
        )
        
        return normalized
    
    def _extract_duplicate_keys(
        self,
        findings: list
    ) -> Set[Tuple[str, str]]:
        """
        Extract (concept, context) keys from findings list.
        
        This is the universal identifier that works across both JSON formats.
        
        Args:
            findings: List of duplicate findings
            
        Returns:
            Set of (concept, context) tuples
        """
        keys = set()
        
        for finding in findings:
            concept = finding.get('concept', '')
            context = finding.get('context', '')
            
            if concept and context:
                keys.add((concept, context))
        
        return keys
    
    def _compare_reports(
        self,
        map_pro: Dict[str, Any],
        ccq: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare duplicate findings between mappers.
        
        Args:
            map_pro: Normalized Map Pro report
            ccq: Normalized CCQ report
            
        Returns:
            Comparison metrics
        """
        # Get all duplicate keys from both mappers
        mp_keys = map_pro['all_duplicate_keys']
        ccq_keys = ccq['all_duplicate_keys']
        
        # Compute set operations
        in_both = mp_keys & ccq_keys
        only_mp = mp_keys - ccq_keys
        only_ccq = ccq_keys - mp_keys
        all_duplicates = mp_keys | ccq_keys
        
        # Calculate agreement rate
        agreement_rate = 0.0
        if len(all_duplicates) > 0:
            agreement_rate = (len(in_both) / len(all_duplicates)) * 100
        
        # Determine cleaner mapper (lower duplicate percentage)
        mp_pct = map_pro['duplicate_percentage']
        ccq_pct = ccq['duplicate_percentage']
        
        if mp_pct < ccq_pct:
            cleaner_mapper = 'map_pro'
        elif ccq_pct < mp_pct:
            cleaner_mapper = 'ccq'
        else:
            cleaner_mapper = 'tie'
        
        # Compare severity classifications for shared duplicates
        severity_agreement = self._compare_severity_classifications(
            in_both,
            map_pro,
            ccq
        )
        
        return {
            'duplicates_in_both': len(in_both),
            'duplicates_only_map_pro': len(only_mp),
            'duplicates_only_ccq': len(only_ccq),
            'total_unique_duplicates': len(all_duplicates),
            
            'agreement_rate': round(agreement_rate, 1),
            'cleaner_mapper': cleaner_mapper,
            'duplicate_rate_difference': abs(mp_pct - ccq_pct),
            
            'severity_agreement': severity_agreement
        }
    
    def _compare_severity_classifications(
        self,
        shared_duplicates: Set[Tuple[str, str]],
        map_pro: Dict[str, Any],
        ccq: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare severity classifications for duplicates found by both mappers.
        
        Args:
            shared_duplicates: Set of (concept, context) tuples in both reports
            map_pro: Normalized Map Pro report
            ccq: Normalized CCQ report
            
        Returns:
            Severity comparison metrics
        """
        if not shared_duplicates:
            return {
                'severity_matches': 0,
                'severity_mismatches': 0,
                'severity_agreement_rate': 0.0
            }
        
        matches = 0
        mismatches = 0
        
        for key in shared_duplicates:
            mp_severity = self._get_severity_for_key(key, map_pro)
            ccq_severity = self._get_severity_for_key(key, ccq)
            
            if mp_severity == ccq_severity:
                matches += 1
            else:
                mismatches += 1
        
        agreement_rate = (matches / len(shared_duplicates)) * 100 if shared_duplicates else 0.0
        
        return {
            'severity_matches': matches,
            'severity_mismatches': mismatches,
            'severity_agreement_rate': round(agreement_rate, 1)
        }
    
    def _get_severity_for_key(
        self,
        key: Tuple[str, str],
        report: Dict[str, Any]
    ) -> str:
        """
        Get severity level for a duplicate key in a report.
        
        Args:
            key: (concept, context) tuple
            report: Normalized report
            
        Returns:
            'CRITICAL', 'MAJOR', 'MINOR', 'REDUNDANT', or 'UNKNOWN'
        """
        if key in report['critical_duplicates']:
            return 'CRITICAL'
        elif key in report['major_duplicates']:
            return 'MAJOR'
        elif key in report['minor_duplicates']:
            return 'MINOR'
        elif key in report['redundant_duplicates']:
            return 'REDUNDANT'
        else:
            return 'UNKNOWN'
    
    def _generate_quality_assessment(
        self,
        map_pro: Dict[str, Any],
        ccq: Dict[str, Any],
        comparison: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate overall quality assessment of duplicate findings.
        
        Args:
            map_pro: Normalized Map Pro report
            ccq: Normalized CCQ report
            comparison: Comparison metrics
            
        Returns:
            Quality assessment dictionary
        """
        flags = []
        recommendations = []
        
        # Check for critical duplicates
        if map_pro['has_critical'] or ccq['has_critical']:
            flags.append("⚠️ CRITICAL duplicates detected - manual review required")
            recommendations.append(
                "Exclude CRITICAL duplicates from analysis until source data is corrected"
            )
        
        # Check for major duplicates
        if map_pro['has_major'] or ccq['has_major']:
            flags.append("⚠️ MAJOR duplicates detected - review recommended")
            recommendations.append(
                "Review MAJOR duplicates for currency conversion or rounding issues"
            )
        
        # Check agreement rate
        agreement_rate = comparison['agreement_rate']
        if agreement_rate >= 95:
            flags.append(f"✓ High mapper agreement ({agreement_rate}%)")
        elif agreement_rate >= 85:
            flags.append(f"⚠️ Moderate mapper agreement ({agreement_rate}%)")
            recommendations.append(
                "Investigate why mappers disagree on ~15% of duplicate identification"
            )
        else:
            flags.append(f"✗ Low mapper agreement ({agreement_rate}%)")
            recommendations.append(
                "Significant disagreement between mappers - review parsing strategies"
            )
        
        # Check cleaner mapper
        cleaner_mapper = comparison['cleaner_mapper']
        if cleaner_mapper != 'tie':
            flags.append(f"✓ {cleaner_mapper.upper()} has lower duplicate rate")
            recommendations.append(
                f"Consider prioritizing {cleaner_mapper.upper()} results for ambiguous cases"
            )
        
        # Overall status
        if map_pro['has_critical'] or ccq['has_critical']:
            overall_status = 'CRITICAL_ISSUES'
        elif map_pro['has_major'] or ccq['has_major']:
            overall_status = 'MAJOR_ISSUES'
        elif agreement_rate < 85:
            overall_status = 'DISAGREEMENT'
        else:
            overall_status = 'ACCEPTABLE'
        
        # Generate summary message
        summary = self._generate_summary_message(map_pro, ccq, comparison)
        
        return {
            'overall_status': overall_status,
            'flags': flags,
            'recommendations': recommendations,
            'summary': summary
        }
    
    def _generate_summary_message(
        self,
        map_pro: Dict[str, Any],
        ccq: Dict[str, Any],
        comparison: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable summary message.
        
        Args:
            map_pro: Normalized Map Pro report
            ccq: Normalized CCQ report
            comparison: Comparison metrics
            
        Returns:
            Summary message string
        """
        parts = []
        
        # Duplicate rates
        parts.append(
            f"Map Pro: {map_pro['duplicate_percentage']:.1f}% duplicates "
            f"({map_pro['duplicate_groups']} groups), "
            f"CCQ: {ccq['duplicate_percentage']:.1f}% duplicates "
            f"({ccq['duplicate_groups']} groups)"
        )
        
        # Agreement
        parts.append(
            f"Mappers agree on {comparison['agreement_rate']:.1f}% of duplicate identification"
        )
        
        # Cleaner mapper
        cleaner = comparison['cleaner_mapper']
        if cleaner != 'tie':
            parts.append(
                f"{cleaner.upper()} has lower duplicate rate (cleaner mapping)"
            )
        
        # Critical warnings
        if map_pro['has_critical'] or ccq['has_critical']:
            parts.append("⚠️ CRITICAL duplicates detected - manual review required")
        
        return "; ".join(parts)
    
    def _build_unavailable_report(
        self,
        map_pro_data: Optional[Dict],
        ccq_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        Build minimal report when one or both duplicate files are unavailable.
        
        Args:
            map_pro_data: Map Pro data or None
            ccq_data: CCQ data or None
            
        Returns:
            Minimal report structure
        """
        # Create empty normalized structure for missing reports
        empty_report = {
            'mapper': 'unknown',
            'total_facts': 0,
            'duplicate_facts': 0,
            'duplicate_groups': 0,
            'duplicate_percentage': 0.0,
            'severity_counts': {},
            'critical_duplicates': set(),
            'major_duplicates': set(),
            'minor_duplicates': set(),
            'redundant_duplicates': set(),
            'all_duplicate_keys': set(),
            'has_critical': False,
            'has_major': False,
            'quality_assessment': 'No duplicate report available',
            'critical_findings': [],
            'major_findings': [],
            'available': False
        }
        
        map_pro_report = map_pro_data if map_pro_data else empty_report.copy()
        ccq_report = ccq_data if ccq_data else empty_report.copy()
        
        # Normalize available reports
        if map_pro_data:
            map_pro_report = self._normalize_report(map_pro_data, 'map_pro')
        if ccq_data:
            ccq_report = self._normalize_report(ccq_data, 'ccq')
        
        return {
            'map_pro_report': map_pro_report,
            'ccq_report': ccq_report,
            'comparison': {
                'available': False,
                'message': 'One or both duplicate reports not available',
                'duplicates_in_both': 0,
                'duplicates_only_map_pro': 0,
                'duplicates_only_ccq': 0,
                'total_unique_duplicates': 0,
                'agreement_rate': 0.0,
                'cleaner_mapper': 'unknown',
                'duplicate_rate_difference': 0.0,
                'severity_agreement': {
                    'severity_matches': 0,
                    'severity_mismatches': 0,
                    'severity_agreement_rate': 0.0
                }
            },
            'quality_assessment': {
                'overall_status': 'UNAVAILABLE',
                'flags': ['Duplicate reports not available from one or both mappers'],
                'recommendations': ['Ensure both mappers generate duplicates.json'],
                'summary': 'Duplicate analysis unavailable'
            }
        }


__all__ = ['DuplicateReportLoader']