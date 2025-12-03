# File: context_extractor.py
# Location: engines/fact_authority/filings_reader/context_extractor.py

"""
Context Extractor
=================

Extracts contexts, units, and entity information from XBRL instances.

Specialized component for parsing XBRL context and unit definitions from
instance documents. Handles:
- Context extraction (entity, period, dimensions)
- Unit extraction (monetary, shares, pure)
- Entity identifier extraction

Used by InstanceParser for clean separation of concerns.

Classes:
    ContextExtractor: Extracts contexts and units from instances
"""

from typing import Dict, Optional
import logging
from lxml import etree


logger = logging.getLogger(__name__)


class ContextExtractor:
    """
    Extracts contexts and units from XBRL instances.
    
    Specialized extractor for context and unit definitions in XBRL
    instance documents. Parses:
    - Entity identifiers
    - Period information (instant or duration)
    - Dimensional information (segments)
    - Unit definitions (monetary, shares, pure)
    """
    
    # XML namespaces
    NAMESPACES = {
        'xbrli': 'http://www.xbrl.org/2003/instance',
        'xbrldi': 'http://xbrl.org/2006/xbrldi',
        'iso4217': 'http://www.xbrl.org/2003/iso4217'
    }
    
    def __init__(self):
        """Initialize context extractor."""
        pass
    
    def extract_contexts(self, root: etree.Element) -> Dict[str, Dict[str, any]]:
        """
        Extract all context definitions from instance.
        
        Args:
            root: Instance root element
            
        Returns:
            Dictionary mapping context IDs to context data:
            {
                'context_id': {
                    'id': 'context_id',
                    'entity': {'scheme': 'http://...', 'value': '0001234'},
                    'period': {'type': 'instant', 'instant': '2024-12-31'},
                    'dimensions': {'dimension_name': 'member_value'}
                }
            }
        """
        contexts = {}
        
        for context in root.findall('.//xbrli:context', self.NAMESPACES):
            context_id = context.get('id')
            
            if not context_id:
                continue
            
            context_data = {
                'id': context_id,
                'entity': None,
                'period': None,
                'dimensions': {}
            }
            
            # Extract entity
            entity_data = self._extract_entity(context)
            if entity_data:
                context_data['entity'] = entity_data
            
            # Extract period
            period_data = self._extract_period(context)
            if period_data:
                context_data['period'] = period_data
            
            # Extract dimensions
            dimensions = self._extract_dimensions(context)
            if dimensions:
                context_data['dimensions'] = dimensions
            
            contexts[context_id] = context_data
        
        logger.debug(f"Extracted {len(contexts)} contexts")
        return contexts
    
    def _extract_entity(self, context: etree.Element) -> Optional[Dict[str, str]]:
        """
        Extract entity information from context.
        
        Args:
            context: Context element
            
        Returns:
            Entity data dictionary or None
        """
        entity = context.find('.//xbrli:entity', self.NAMESPACES)
        if entity is None:
            return None
        
        identifier = entity.find('.//xbrli:identifier', self.NAMESPACES)
        if identifier is None:
            return None
        
        return {
            'scheme': identifier.get('scheme'),
            'value': identifier.text
        }
    
    def _extract_period(self, context: etree.Element) -> Optional[Dict[str, str]]:
        """
        Extract period information from context.
        
        Args:
            context: Context element
            
        Returns:
            Period data dictionary or None
        """
        period = context.find('.//xbrli:period', self.NAMESPACES)
        if period is None:
            return None
        
        # Check for instant period
        instant = period.find('.//xbrli:instant', self.NAMESPACES)
        if instant is not None:
            return {
                'type': 'instant',
                'instant': instant.text
            }
        
        # Check for duration period
        start = period.find('.//xbrli:startDate', self.NAMESPACES)
        end = period.find('.//xbrli:endDate', self.NAMESPACES)
        
        if start is not None and end is not None:
            return {
                'type': 'duration',
                'start': start.text,
                'end': end.text
            }
        
        return None
    
    def _extract_dimensions(self, context: etree.Element) -> Dict[str, str]:
        """
        Extract dimensional information from context.
        
        Args:
            context: Context element
            
        Returns:
            Dictionary mapping dimension names to member values
        """
        dimensions = {}
        
        # Check segment for dimensions
        segment = context.find('.//xbrli:segment', self.NAMESPACES)
        if segment is not None:
            for dim in segment.findall('.//xbrldi:explicitMember', self.NAMESPACES):
                dim_name = dim.get('dimension')
                if dim_name and dim.text:
                    dimensions[dim_name] = dim.text
        
        # Also check scenario for dimensions
        scenario = context.find('.//xbrli:scenario', self.NAMESPACES)
        if scenario is not None:
            for dim in scenario.findall('.//xbrldi:explicitMember', self.NAMESPACES):
                dim_name = dim.get('dimension')
                if dim_name and dim.text:
                    dimensions[dim_name] = dim.text
        
        return dimensions
    
    def extract_units(self, root: etree.Element) -> Dict[str, Dict[str, str]]:
        """
        Extract all unit definitions from instance.
        
        Args:
            root: Instance root element
            
        Returns:
            Dictionary mapping unit IDs to unit data:
            {
                'unit_id': {
                    'id': 'unit_id',
                    'measure': 'iso4217:USD'
                }
            }
        """
        units = {}
        
        for unit in root.findall('.//xbrli:unit', self.NAMESPACES):
            unit_id = unit.get('id')
            
            if not unit_id:
                continue
            
            # Find measure
            measure = unit.find('.//xbrli:measure', self.NAMESPACES)
            if measure is not None and measure.text:
                units[unit_id] = {
                    'id': unit_id,
                    'measure': measure.text
                }
            else:
                # Handle divide units (for ratios)
                numerator = unit.find('.//xbrli:divide/xbrli:unitNumerator/xbrli:measure', 
                                     self.NAMESPACES)
                denominator = unit.find('.//xbrli:divide/xbrli:unitDenominator/xbrli:measure', 
                                       self.NAMESPACES)
                
                if numerator is not None and denominator is not None:
                    units[unit_id] = {
                        'id': unit_id,
                        'measure': f"{numerator.text}/{denominator.text}"
                    }
        
        logger.debug(f"Extracted {len(units)} units")
        return units
    
    def extract_entity_identifier(self, root: etree.Element) -> Optional[str]:
        """
        Extract entity identifier from first context.
        
        Args:
            root: Instance root element
            
        Returns:
            Entity identifier string or None
        """
        context = root.find('.//xbrli:context', self.NAMESPACES)
        if context is None:
            return None
        
        identifier = context.find('.//xbrli:identifier', self.NAMESPACES)
        if identifier is None:
            return None
        
        return identifier.text