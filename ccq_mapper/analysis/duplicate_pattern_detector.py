# File: engines/ccq_mapper/analysis/duplicate_pattern_detector.py

"""
Duplicate Pattern Detector
===========================

Detects patterns in duplicate distributions to identify systematic issues.

Pattern Types:
- Cross-statement: Same concepts appearing in multiple statements
- Temporal: Systematic temporal patterns (instant vs duration)
- Dimensional: Patterns in dimensional vs primary context duplicates
- Systematic: Concentration in specific statement types or sources

Used by DuplicateAnalyzer to enhance analysis reports.
"""

from typing import Dict, Any, List
from collections import defaultdict

from core.system_logger import get_logger

logger = get_logger(__name__)


class DuplicatePatternDetector:
    """
    Detects patterns in duplicate fact distributions.
    
    Responsibilities:
    - Identify cross-statement duplication patterns
    - Detect temporal patterns (instant vs duration)
    - Analyze dimensional patterns
    - Find systematic concentration patterns
    
    Does NOT:
    - Modify data
    - Make decisions about handling
    - Perform classification (that's done by DuplicateAnalyzer)
    """
    
    def __init__(self):
        """Initialize pattern detector."""
        self.logger = logger
    
    def detect_patterns(
        self,
        enriched_duplicates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect all patterns in duplicate distribution.
        
        Args:
            enriched_duplicates: List of enriched duplicate profiles
            
        Returns:
            Dictionary containing all detected patterns
        """
        self.logger.debug(f"Detecting patterns in {len(enriched_duplicates)} duplicate groups")
        
        patterns = {
            'cross_statement': self._detect_cross_statement_pattern(enriched_duplicates),
            'temporal': self._detect_temporal_pattern(enriched_duplicates),
            'dimensional': self._detect_dimensional_pattern(enriched_duplicates),
            'systematic': self._detect_systematic_pattern(enriched_duplicates)
        }
        
        return patterns
    
    def _detect_cross_statement_pattern(
        self,
        enriched_duplicates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect if same concepts appear in multiple statements.
        
        This could indicate data quality issues where concepts are
        incorrectly classified or appearing in multiple financial statements.
        
        Args:
            enriched_duplicates: List of enriched duplicate profiles
            
        Returns:
            Cross-statement pattern analysis
        """
        concept_statements = defaultdict(set)
        
        for dup in enriched_duplicates:
            concept = dup['concept']
            statement = dup['classification']['statement_type']
            concept_statements[concept].add(statement)
        
        # Find concepts appearing in multiple statements (excluding 'other')
        cross_statement_concepts = {
            concept: list(statements)
            for concept, statements in concept_statements.items()
            if len(statements) > 1 and 'other' not in statements
        }
        
        return {
            'detected': len(cross_statement_concepts) > 0,
            'count': len(cross_statement_concepts),
            'concepts': cross_statement_concepts,
            'concern_level': 'HIGH' if cross_statement_concepts else 'NONE',
            'description': (
                f'Found {len(cross_statement_concepts)} concepts appearing in multiple financial statements'
                if cross_statement_concepts else 'No cross-statement duplication detected'
            )
        }
    
    def _detect_temporal_pattern(
        self,
        enriched_duplicates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect if duplicates show temporal patterns.
        
        If duplicates are heavily concentrated in instant or duration facts,
        it might indicate systematic issues with temporal processing.
        
        Args:
            enriched_duplicates: List of enriched duplicate profiles
            
        Returns:
            Temporal pattern analysis
        """
        if not enriched_duplicates:
            return {
                'detected': False,
                'concern_level': 'NONE',
                'description': 'No duplicates to analyze'
            }
        
        # Count instant vs duration duplicates
        instant_count = sum(
            1 for dup in enriched_duplicates
            if dup['classification']['temporal_type'] == 'instant'
        )
        duration_count = sum(
            1 for dup in enriched_duplicates
            if dup['classification']['temporal_type'] == 'duration'
        )
        
        total = len(enriched_duplicates)
        instant_pct = (instant_count / total) * 100
        duration_pct = (duration_count / total) * 100
        
        # If one type dominates (>80%), it might be systematic
        is_systematic = instant_pct > 80 or duration_pct > 80
        
        dominant_type = 'instant' if instant_pct > duration_pct else 'duration'
        dominant_pct = max(instant_pct, duration_pct)
        
        return {
            'detected': is_systematic,
            'instant_duplicates': instant_count,
            'duration_duplicates': duration_count,
            'instant_percentage': round(instant_pct, 1),
            'duration_percentage': round(duration_pct, 1),
            'concern_level': 'MEDIUM' if is_systematic else 'LOW',
            'description': (
                f'{dominant_pct:.1f}% of duplicates are {dominant_type} facts - possible systematic pattern'
                if is_systematic
                else f'Balanced temporal distribution: {instant_pct:.1f}% instant, {duration_pct:.1f}% duration'
            )
        }
    
    def _detect_dimensional_pattern(
        self,
        enriched_duplicates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect patterns in dimensional vs primary context duplicates.
        
        Dimensional duplicates (with explicit dimensions) are often normal
        for segment reporting, whereas primary context duplicates might
        indicate more serious issues.
        
        Args:
            enriched_duplicates: List of enriched duplicate profiles
            
        Returns:
            Dimensional pattern analysis
        """
        if not enriched_duplicates:
            return {
                'detected': False,
                'concern_level': 'NONE',
                'description': 'No duplicates to analyze'
            }
        
        primary_count = sum(
            1 for dup in enriched_duplicates
            if dup['classification']['is_primary_context']
        )
        dimensional_count = sum(
            1 for dup in enriched_duplicates
            if not dup['classification']['is_primary_context']
        )
        
        total = len(enriched_duplicates)
        primary_pct = (primary_count / total) * 100
        dimensional_pct = (dimensional_count / total) * 100
        
        return {
            'detected': True,
            'primary_duplicates': primary_count,
            'dimensional_duplicates': dimensional_count,
            'primary_percentage': round(primary_pct, 1),
            'dimensional_percentage': round(dimensional_pct, 1),
            'concern_level': 'LOW',  # Dimensional duplicates are often normal
            'description': (
                f'Primary context: {primary_pct:.1f}%, Dimensional: {dimensional_pct:.1f}% '
                f'(dimensional duplicates are often expected for segment reporting)'
            )
        }
    
    def _detect_systematic_pattern(
        self,
        enriched_duplicates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect if duplicates show systematic concentration patterns.
        
        If a large percentage comes from one statement type or one source,
        it might indicate a systematic issue that needs investigation.
        
        Args:
            enriched_duplicates: List of enriched duplicate profiles
            
        Returns:
            Systematic pattern analysis
        """
        if not enriched_duplicates:
            return {
                'detected': False,
                'concern_level': 'NONE',
                'description': 'No duplicates to analyze'
            }
        
        # Count by statement type
        statement_counts = defaultdict(int)
        for dup in enriched_duplicates:
            statement_counts[dup['classification']['statement_type']] += 1
        
        # Count by source
        source_counts = defaultdict(int)
        for dup in enriched_duplicates:
            source_counts[dup['source']] += 1
        
        total = len(enriched_duplicates)
        
        # Calculate concentration percentages
        max_statement_count = max(statement_counts.values()) if statement_counts else 0
        max_source_count = max(source_counts.values()) if source_counts else 0
        
        max_statement_pct = (max_statement_count / total) * 100
        max_source_pct = (max_source_count / total) * 100
        
        # Check if one category dominates (>70%)
        is_systematic = max_statement_pct > 70 or max_source_pct > 70
        
        dominant_statement = max(statement_counts, key=statement_counts.get) if statement_counts else None
        dominant_source = max(source_counts, key=source_counts.get) if source_counts else None
        
        # Build description
        description_parts = []
        if max_statement_pct > 70:
            description_parts.append(
                f'{max_statement_pct:.1f}% concentrated in {dominant_statement}'
            )
        if max_source_pct > 70:
            description_parts.append(
                f'{max_source_pct:.1f}% from {dominant_source} source'
            )
        
        description = (
            'Systematic concentration detected: ' + ', '.join(description_parts)
            if is_systematic
            else 'Well-distributed across statements and sources'
        )
        
        return {
            'detected': is_systematic,
            'statement_concentration': round(max_statement_pct, 1),
            'source_concentration': round(max_source_pct, 1),
            'dominant_statement': dominant_statement,
            'dominant_source': dominant_source,
            'statement_distribution': dict(statement_counts),
            'source_distribution': dict(source_counts),
            'concern_level': 'MEDIUM' if is_systematic else 'LOW',
            'description': description
        }


__all__ = ['DuplicatePatternDetector']