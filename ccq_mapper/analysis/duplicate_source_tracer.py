# File: engines/ccq_mapper/analysis/duplicate_source_tracer.py

"""
CCQ Duplicate Source Tracer
============================

Tracks the SOURCE of duplicate facts by comparing:
1. Parsed facts JSON (Map Pro's extraction from XBRL/iXBRL)
2. Mapper output (CCQ mapper's processing)

Provides breakdown of WHERE duplicates originate:
- SOURCE_DATA: Duplicates exist in parsed_facts.json (Map Pro preserved them from source)
- MAPPING_INTRODUCED: Mapper process created duplicates
- UNKNOWN: Cannot determine source

This is CRITICAL for "no mappable data is lost" principle - we need to know
if we're preserving source duplicates (correct) or creating new ones (incorrect).

Architecture: Market-agnostic duplicate source tracking.
"""

from typing import Dict, Any, List, Tuple, Set
from collections import defaultdict
from pathlib import Path
import json

from core.system_logger import get_logger

logger = get_logger(__name__)


# Source classifications
SOURCE_DATA = 'SOURCE_DATA'  # Duplicates exist in parsed_facts.json
SOURCE_MAPPING = 'MAPPING_INTRODUCED'  # Mapper created duplicates
SOURCE_UNKNOWN = 'UNKNOWN'  # Cannot determine

# Separator for logging
SEPARATOR = "=" * 80


class DuplicateSourceTracer:
    """
    Traces duplicate facts to their origin in the data pipeline.
    
    Responsibilities:
    - Compare parsed_facts.json vs mapper output
    - Identify where duplicates originate
    - Generate source attribution report
    
    Does NOT:
    - Modify any data
    - Make decisions about duplicate handling
    - Access database
    - Parse XBRL/iXBRL directly (Map Pro already did that)
    """
    
    def __init__(self):
        """Initialize duplicate source tracer."""
        self.logger = logger
        self.logger.info("Duplicate source tracer initialized")
    
    def trace_duplicate_sources(
        self,
        xbrl_path: Path,
        parsed_facts_path: Path,
        parsed_facts: List[Dict[str, Any]],
        duplicate_groups: Dict[Tuple[str, str], List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Trace duplicate facts to their source.
        
        STRATEGY:
        Compare parsed_facts.json (Map Pro's extraction) vs mapper output.
        
        If duplicates exist in parsed_facts.json:
          → SOURCE_DATA (duplicates were in the original data that Map Pro extracted)
        
        If duplicates only appear in mapper output:
          → MAPPING_INTRODUCED (CCQ mapper created them during processing)
        
        Args:
            xbrl_path: Path to XBRL file (not used in this strategy)
            parsed_facts_path: Path to parsed facts JSON
            parsed_facts: List of parsed facts (already loaded)
            duplicate_groups: Groups of duplicate facts by (concept, context)
            
        Returns:
            Source attribution report dictionary
        """
        self.logger.info(f"="*80)
        self.logger.info(f"DUPLICATE SOURCE TRACER")
        self.logger.info(f"="*80)
        self.logger.info(f"Parsed facts path: {parsed_facts_path}")
        self.logger.info(f"Duplicate groups to trace: {len(duplicate_groups)}")
        self.logger.info(f"Strategy: Compare parsed_facts.json vs mapper output")
        self.logger.info(f"="*80)
        
        # Build index of parsed_facts for quick lookup
        parsed_facts_index = self._build_parsed_facts_index(parsed_facts)
        
        # Analyze each duplicate group
        source_attributions = []
        
        for (concept, context), facts in duplicate_groups.items():
            attribution = self._trace_duplicate_from_parsed_facts(
                concept,
                context,
                facts,
                parsed_facts_index
            )
            source_attributions.append(attribution)
        
        # Build summary report
        report = self._build_source_report(
            source_attributions,
            len(parsed_facts),
            xbrl_path,
            parsed_facts_path
        )
        
        self._log_source_summary(report)
        
        return report
    
    def _build_parsed_facts_index(
        self,
        parsed_facts: List[Dict[str, Any]]
    ) -> Dict[Tuple[str, str], List[Dict[str, Any]]]:
        """
        Build an index of parsed_facts grouped by (concept, context).
        
        This allows us to quickly check if duplicates exist in the source data.
        
        Args:
            parsed_facts: List of parsed fact dictionaries
            
        Returns:
            Dictionary mapping (concept, context) to list of facts
        """
        from collections import defaultdict
        
        index = defaultdict(list)
        
        for fact in parsed_facts:
            # Get concept
            concept = (
                fact.get('concept_qname') or
                fact.get('concept') or
                fact.get('qname')
            )
            
            # Get context
            context = (
                fact.get('context_ref') or
                fact.get('contextRef') or
                fact.get('context')
            )
            
            if concept and context:
                key = (concept, context)
                index[key].append(fact)
        
        return dict(index)
    
    def _trace_duplicate_from_parsed_facts(
        self,
        concept: str,
        context: str,
        duplicate_facts: List[Dict[str, Any]],
        parsed_facts_index: Dict[Tuple[str, str], List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Determine if duplicates exist in parsed_facts.json (source data)
        or were introduced during mapping.
        
        Args:
            concept: Concept name
            context: Context reference
            duplicate_facts: List of duplicate facts from mapper output
            parsed_facts_index: Index of parsed_facts by (concept, context)
            
        Returns:
            Attribution dictionary with source determination
        """
        key = (concept, context)
        
        # Check if this (concept, context) has duplicates in parsed_facts
        source_facts = parsed_facts_index.get(key, [])
        
        if len(source_facts) > 1:
            # Duplicates exist in source data (parsed_facts.json)
            source = 'SOURCE_DATA'
            explanation = f"Found {len(source_facts)} facts in parsed_facts.json"
        elif len(source_facts) == 1:
            # Only one fact in source, but we have duplicates in mapper output
            # This means mapper created the duplicates
            source = 'MAPPING_INTRODUCED'
            explanation = f"Only 1 fact in parsed_facts.json, but {len(duplicate_facts)} in mapper output"
        else:
            # No facts found in source (shouldn't happen, but handle gracefully)
            source = 'UNKNOWN'
            explanation = "Fact not found in parsed_facts.json"
        
        return {
            'concept': concept,
            'context': context,
            'duplicate_count': len(duplicate_facts),
            'source_count': len(source_facts),
            'source': source,
            'explanation': explanation
        }
    
    def _load_xbrl_facts(self, xbrl_path: Path) -> List[Dict[str, Any]]:
        """
        Load facts from raw XBRL file.
        
        Args:
            xbrl_path: Path to XBRL instance file
            
        Returns:
            List of fact dictionaries from raw XBRL
        """
        if not xbrl_path or not xbrl_path.exists():
            self.logger.warning("Raw XBRL file not found - cannot trace to source")
            return []
        
        try:
            # Import XBRLLoader from loaders directory (sibling to analysis)
            from ..loaders.xbrl_loader import XBRLLoader
            
            loader = XBRLLoader()
            facts = loader.load_facts(xbrl_path)
            
            self.logger.info(f"Loaded {len(facts)} facts from raw XBRL")
            return facts
            
        except Exception as e:
            self.logger.error(f"Failed to load raw XBRL: {e}")
            return []
    
    def _trace_single_duplicate(
        self,
        concept: str,
        context: str,
        duplicate_facts: List[Dict[str, Any]],
        all_parsed_facts: List[Dict[str, Any]],
        xbrl_facts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Trace a single duplicate group to its source.
        
        Args:
            concept: Concept identifier
            context: Context identifier
            duplicate_facts: List of duplicate facts
            all_parsed_facts: All parsed facts from JSON
            xbrl_facts: Facts from raw XBRL (may be empty)
            
        Returns:
            Attribution dictionary with source determination
        """
        # Extract unique values from duplicates
        unique_values = list(set(
            str(f.get('value') or f.get('fact_value'))
            for f in duplicate_facts
        ))
        
        # Check if duplicates exist in raw XBRL
        xbrl_matches = self._find_matches_in_xbrl(
            concept, context, xbrl_facts
        )
        
        # Check if duplicates exist in parsed JSON
        parsed_matches = self._find_matches_in_parsed(
            concept, context, all_parsed_facts
        )
        
        # Determine source
        source = self._determine_duplicate_source(
            len(duplicate_facts),
            len(xbrl_matches),
            len(parsed_matches),
            unique_values,
            xbrl_matches,
            parsed_matches
        )
        
        return {
            'concept': concept,
            'context': context[:60] + '...' if len(context) > 60 else context,
            'duplicate_count': len(duplicate_facts),
            'unique_values': unique_values,
            'xbrl_matches': len(xbrl_matches),
            'parsed_matches': len(parsed_matches),
            'source': source,
            'explanation': self._get_source_explanation(source),
            'xbrl_values': self._extract_values(xbrl_matches) if xbrl_matches else None,
            'parsed_values': self._extract_values(parsed_matches) if parsed_matches else None
        }
    
    def _find_matches_in_xbrl(
        self,
        concept: str,
        context: str,
        xbrl_facts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Find matching facts in raw XBRL.
        
        Args:
            concept: Concept to match
            context: Context to match
            xbrl_facts: List of XBRL facts
            
        Returns:
            List of matching facts
        """
        if not xbrl_facts:
            return []
        
        matches = []
        
        for fact in xbrl_facts:
            # Try multiple field names for concept
            fact_concept = (
                fact.get('concept') or
                fact.get('concept_qname') or
                fact.get('name') or
                ''
            )
            
            # Try multiple field names for context
            fact_context = (
                fact.get('context_ref') or
                fact.get('contextRef') or
                fact.get('context_id') or
                ''
            )
            
            if fact_concept == concept and fact_context == context:
                matches.append(fact)
        
        return matches
    
    def _find_matches_in_parsed(
        self,
        concept: str,
        context: str,
        parsed_facts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Find matching facts in parsed JSON.
        
        Args:
            concept: Concept to match
            context: Context to match
            parsed_facts: List of parsed facts
            
        Returns:
            List of matching facts
        """
        matches = []
        
        for fact in parsed_facts:
            fact_concept = (
                fact.get('concept_qname') or
                fact.get('concept') or
                ''
            )
            
            fact_context = (
                fact.get('context_ref') or
                fact.get('contextRef') or
                ''
            )
            
            if fact_concept == concept and fact_context == context:
                matches.append(fact)
        
        return matches
    
    def _extract_values(self, facts: List[Dict[str, Any]]) -> List[str]:
        """Extract unique values from facts."""
        values = []
        for fact in facts:
            value = fact.get('value') or fact.get('fact_value')
            if value is not None:
                values.append(str(value))
        return list(set(values))
    
    def _determine_duplicate_source(
        self,
        mapping_count: int,
        xbrl_count: int,
        parsed_count: int,
        unique_values: List[str],
        xbrl_matches: List[Dict],
        parsed_matches: List[Dict]
    ) -> str:
        """
        Determine where the duplicate originated.
        
        Logic:
        - If XBRL has duplicates with same values → XBRL_SOURCE
        - If XBRL is clean but parsed has duplicates → PARSING_INTRODUCED
        - If both clean but mapping has duplicates → MAPPING_INTRODUCED
        - If cannot determine → UNKNOWN
        
        Args:
            mapping_count: Number of duplicates in mapping output
            xbrl_count: Number of matches in raw XBRL
            parsed_count: Number of matches in parsed JSON
            unique_values: Unique values in duplicates
            xbrl_matches: Actual XBRL facts
            parsed_matches: Actual parsed facts
            
        Returns:
            Source classification
        """
        # No raw XBRL data available
        if not xbrl_matches:
            if parsed_count > 1:
                # Duplicates exist in parsed data
                parsed_values = self._extract_values(parsed_matches)
                if len(parsed_values) > 1:
                    # Different values - cannot determine if from XBRL or parsing
                    return SOURCE_UNKNOWN
                else:
                    # Same value - likely harmless redundancy
                    return SOURCE_UNKNOWN
            else:
                # Mapping introduced the duplicate
                return SOURCE_MAPPING
        
        # Raw XBRL available
        xbrl_values = self._extract_values(xbrl_matches)
        
        # Check if XBRL has the duplicate
        if xbrl_count > 1:
            if len(xbrl_values) > 1:
                # XBRL has conflicting values - source is XBRL
                return SOURCE_XBRL
            else:
                # XBRL has redundant copies - source is XBRL
                return SOURCE_XBRL
        
        # XBRL is clean (only 1 or 0 facts)
        if parsed_count > 1:
            # Parsing created the duplicate
            return SOURCE_PARSING
        
        # Both XBRL and parsed are clean, but mapping has duplicate
        if mapping_count > 1:
            return SOURCE_MAPPING
        
        return SOURCE_UNKNOWN
    
    def _get_source_explanation(self, source: str) -> str:
        """Get human-readable explanation of source."""
        explanations = {
            SOURCE_XBRL: "Duplicate exists in original XBRL filing (data quality issue)",
            SOURCE_PARSING: "Parsing process introduced duplicate (review parser)",
            SOURCE_MAPPING: "Mapping process created duplicate (review mapper logic)",
            SOURCE_UNKNOWN: "Cannot determine source (insufficient data)"
        }
        return explanations.get(source, "Unknown source")
    
    def _build_source_report(
        self,
        attributions: List[Dict[str, Any]],
        total_facts: int,
        xbrl_path: Path,
        parsed_path: Path
    ) -> Dict[str, Any]:
        """
        Build comprehensive source attribution report.
        
        Args:
            attributions: List of attribution dictionaries
            total_facts: Total number of facts
            xbrl_path: Path to XBRL file
            parsed_path: Path to parsed JSON
            
        Returns:
            Source report dictionary
        """
        # Count by source
        source_counts = defaultdict(int)
        duplicate_fact_counts = defaultdict(int)
        
        for attr in attributions:
            source = attr['source']
            source_counts[source] += 1
            duplicate_fact_counts[source] += attr['duplicate_count']
        
        # Calculate statistics
        total_duplicate_groups = len(attributions)
        total_duplicate_facts = sum(attr['duplicate_count'] for attr in attributions)
        
        return {
            'total_facts': total_facts,
            'total_duplicate_groups': total_duplicate_groups,
            'total_duplicate_facts': total_duplicate_facts,
            'source_breakdown': {
                'source_data': {
                    'groups': source_counts[SOURCE_DATA],
                    'facts': duplicate_fact_counts[SOURCE_DATA],
                    'percentage': round(duplicate_fact_counts[SOURCE_DATA] / total_duplicate_facts * 100, 1) if total_duplicate_facts > 0 else 0.0
                },
                'mapping_introduced': {
                    'groups': source_counts[SOURCE_MAPPING],
                    'facts': duplicate_fact_counts[SOURCE_MAPPING],
                    'percentage': round(duplicate_fact_counts[SOURCE_MAPPING] / total_duplicate_facts * 100, 1) if total_duplicate_facts > 0 else 0.0
                },
                'unknown': {
                    'groups': source_counts[SOURCE_UNKNOWN],
                    'facts': duplicate_fact_counts[SOURCE_UNKNOWN],
                    'percentage': round(duplicate_fact_counts[SOURCE_UNKNOWN] / total_duplicate_facts * 100, 1) if total_duplicate_facts > 0 else 0.0
                }
            },
            'attributions': attributions,
            'files_analyzed': {
                'xbrl_path': str(xbrl_path) if xbrl_path else None,
                'parsed_path': str(parsed_path) if parsed_path else None
            }
        }
    
    def _log_source_summary(self, report: Dict[str, Any]) -> None:
        """
        Log source attribution summary.
        
        Args:
            report: Source report dictionary
        """
        breakdown = report['source_breakdown']
        
        self.logger.info(f"\n{SEPARATOR}")
        self.logger.info("DUPLICATE SOURCE ATTRIBUTION")
        self.logger.info(SEPARATOR)
        
        self.logger.info(f"Total duplicate facts: {report['total_duplicate_facts']}")
        self.logger.info(f"Total duplicate groups: {report['total_duplicate_groups']}")
        
        self.logger.info(f"\nSource Breakdown:")
        
        source_data = breakdown['source_data']
        if source_data['facts'] > 0:
            self.logger.warning(
                f"  Source Data (parsed_facts.json): {source_data['facts']} facts ({source_data['percentage']:.1f}%) "
                f"in {source_data['groups']} groups"
            )
        
        mapping = breakdown['mapping_introduced']
        if mapping['facts'] > 0:
            self.logger.error(
                f"  Mapping Introduced: {mapping['facts']} facts ({mapping['percentage']:.1f}%) "
                f"in {mapping['groups']} groups"
            )
        
        unknown = breakdown['unknown']
        if unknown['facts'] > 0:
            self.logger.warning(
                f"  Unknown: {unknown['facts']} facts ({unknown['percentage']:.1f}%) "
                f"in {unknown['groups']} groups"
            )
        
        self.logger.info(f"\n{SEPARATOR}\n")


__all__ = ['DuplicateSourceTracer']