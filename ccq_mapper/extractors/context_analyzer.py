"""
Context Analyzer
================

Analyzes XBRL context structures to extract temporal and dimensional information.

CRITICAL: This analyzes STRUCTURE, not SEMANTICS.
We extract periods, segments, scenarios - not concept relationships.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date


class ContextAnalyzer:
    """
    Analyze XBRL context structures for property extraction.
    
    Extracts:
    - Period information (instant vs duration, dates)
    - Entity information
    - Segment/scenario dimensions
    - Context relationships
    """
    
    def analyze_context(
        self,
        context_ref: Optional[str],
        contexts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a context structure.
        
        Args:
            context_ref: Context reference ID
            contexts: Dictionary of all contexts
            
        Returns:
            Dictionary of context properties
        """
        if not context_ref or not contexts:
            return self._empty_context()
        
        context = contexts.get(context_ref)
        if not context:
            return self._empty_context()
        
        return {
            'context_id': context_ref,
            'period': self._extract_period_info(context),
            'entity': self._extract_entity_info(context),
            'dimensions': self._extract_dimensions(context),
            'is_default': self._is_default_context(context),
            'has_segments': self._has_segments(context),
            'has_scenarios': self._has_scenarios(context)
        }
    
    def _extract_period_info(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract period information from context.
        
        Returns period type, start date, end date, instant date.
        """
        period = context.get('period', {})
        
        # Check for instant
        instant = period.get('instant')
        if instant:
            return {
                'type': 'instant',
                'instant': self._parse_date(instant),
                'start': None,
                'end': None,
                'duration_days': 0
            }
        
        # Check for duration
        start = period.get('startDate') or period.get('start')
        end = period.get('endDate') or period.get('end')
        
        if start and end:
            start_date = self._parse_date(start)
            end_date = self._parse_date(end)
            
            duration_days = 0
            if start_date and end_date:
                duration_days = (end_date - start_date).days
            
            return {
                'type': 'duration',
                'instant': None,
                'start': start_date,
                'end': end_date,
                'duration_days': duration_days
            }
        
        return {
            'type': 'unknown',
            'instant': None,
            'start': None,
            'end': None,
            'duration_days': 0
        }
    
    def _extract_entity_info(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract entity identifier information."""
        entity = context.get('entity', {})
        
        identifier = entity.get('identifier', {})
        if isinstance(identifier, dict):
            return {
                'scheme': identifier.get('scheme'),
                'value': identifier.get('value') or identifier.get('content')
            }
        elif isinstance(identifier, str):
            return {
                'scheme': None,
                'value': identifier
            }
        
        return {
            'scheme': None,
            'value': None
        }
    
    def _extract_dimensions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract dimensional information (segments/scenarios).
        
        Dimensions are used for disaggregation (by segment, product, etc.)
        """
        dimensions = []
        
        # Check entity segment
        entity = context.get('entity', {})
        segment = entity.get('segment', {})
        
        if segment:
            dimensions.extend(self._parse_dimension_container(segment, 'segment'))
        
        # Check scenario
        scenario = context.get('scenario', {})
        if scenario:
            dimensions.extend(self._parse_dimension_container(scenario, 'scenario'))
        
        return dimensions
    
    def _parse_dimension_container(
        self,
        container: Dict[str, Any],
        container_type: str
    ) -> List[Dict[str, Any]]:
        """Parse dimensions from a segment or scenario container."""
        dimensions = []
        
        # Look for explicit members
        explicit_members = container.get('explicitMember', [])
        if not isinstance(explicit_members, list):
            explicit_members = [explicit_members]
        
        for member in explicit_members:
            if member:
                dimensions.append({
                    'type': 'explicit',
                    'container': container_type,
                    'dimension': member.get('dimension'),
                    'member': member.get('value') or member.get('content')
                })
        
        # Look for typed members
        typed_members = container.get('typedMember', [])
        if not isinstance(typed_members, list):
            typed_members = [typed_members]
        
        for member in typed_members:
            if member:
                dimensions.append({
                    'type': 'typed',
                    'container': container_type,
                    'dimension': member.get('dimension'),
                    'value': member.get('value') or member.get('content')
                })
        
        return dimensions
    
    def _is_default_context(self, context: Dict[str, Any]) -> bool:
        """Check if this is a default/primary context (no dimensions)."""
        entity = context.get('entity', {})
        scenario = context.get('scenario', {})
        
        has_segment = bool(entity.get('segment'))
        has_scenario = bool(scenario)
        
        return not (has_segment or has_scenario)
    
    def _has_segments(self, context: Dict[str, Any]) -> bool:
        """Check if context has segment dimensions."""
        entity = context.get('entity', {})
        return bool(entity.get('segment'))
    
    def _has_scenarios(self, context: Dict[str, Any]) -> bool:
        """Check if context has scenario dimensions."""
        return bool(context.get('scenario'))
    
    def _parse_date(self, date_str: Any) -> Optional[date]:
        """
        Parse date string into date object.
        
        Handles common XBRL date formats.
        """
        if not date_str:
            return None
        
        if isinstance(date_str, (date, datetime)):
            return date_str if isinstance(date_str, date) else date_str.date()
        
        if not isinstance(date_str, str):
            return None
        
        # Try common formats
        formats = [
            '%Y-%m-%d',
            '%Y%m%d',
            '%m/%d/%Y',
            '%d/%m/%Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None
    
    def _empty_context(self) -> Dict[str, Any]:
        """Return empty context info structure."""
        return {
            'context_id': None,
            'period': {
                'type': 'unknown',
                'instant': None,
                'start': None,
                'end': None,
                'duration_days': 0
            },
            'entity': {
                'scheme': None,
                'value': None
            },
            'dimensions': [],
            'is_default': True,
            'has_segments': False,
            'has_scenarios': False
        }
    
    def compare_contexts(
        self,
        context_ref1: str,
        context_ref2: str,
        contexts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare two contexts for similarity.
        
        Used in clustering to group facts with similar contexts.
        """
        ctx1 = self.analyze_context(context_ref1, contexts)
        ctx2 = self.analyze_context(context_ref2, contexts)
        
        return {
            'same_period_type': ctx1['period']['type'] == ctx2['period']['type'],
            'same_entity': ctx1['entity']['value'] == ctx2['entity']['value'],
            'same_dimensions': len(ctx1['dimensions']) == len(ctx2['dimensions']),
            'both_default': ctx1['is_default'] and ctx2['is_default'],
            'similarity_score': self._calculate_similarity(ctx1, ctx2)
        }
    
    def _calculate_similarity(self, ctx1: Dict[str, Any], ctx2: Dict[str, Any]) -> float:
        """Calculate similarity score between two contexts (0.0 to 1.0)."""
        score = 0.0
        weights = {
            'period_type': 0.3,
            'entity': 0.2,
            'dimensions': 0.3,
            'default': 0.2
        }
        
        # Period type match
        if ctx1['period']['type'] == ctx2['period']['type']:
            score += weights['period_type']
        
        # Entity match
        if ctx1['entity']['value'] == ctx2['entity']['value']:
            score += weights['entity']
        
        # Dimension match
        if len(ctx1['dimensions']) == len(ctx2['dimensions']) == 0:
            score += weights['dimensions']
        elif len(ctx1['dimensions']) == len(ctx2['dimensions']):
            score += weights['dimensions'] * 0.5
        
        # Default context match
        if ctx1['is_default'] == ctx2['is_default']:
            score += weights['default']
        
        return score


__all__ = ['ContextAnalyzer']