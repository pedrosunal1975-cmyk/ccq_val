"""
XBRL Loader
===========

Loads raw XBRL filing for context analysis.

CRITICAL: Loads STRUCTURE (contexts, units), not concepts.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import xml.etree.ElementTree as ET

from core.system_logger import get_logger

logger = get_logger(__name__)


class XBRLLoader:
    """
    Load raw XBRL filing for context and structural analysis.
    
    Extracts:
    - Contexts (periods, entities, dimensions)
    - Units (currencies, shares)
    - Relationships (for validation)
    
    Does NOT extract or index concepts.
    """
    
    # Common XBRL namespaces
    NAMESPACES = {
        'xbrli': 'http://www.xbrl.org/2003/instance',
        'xbrldi': 'http://xbrl.org/2006/xbrldi',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'link': 'http://www.xbrl.org/2003/linkbase',
        'xlink': 'http://www.w3.org/1999/xlink'
    }
    
    def load_contexts(self, xbrl_path: Path) -> Dict[str, Any]:
        """
        Load contexts from XBRL filing.
        
        Args:
            xbrl_path: Path to XBRL instance document
            
        Returns:
            Dictionary mapping context IDs to context information
        """
        logger.info(f"Loading contexts from: {xbrl_path}")
        
        if not xbrl_path.exists():
            logger.warning(f"XBRL file not found: {xbrl_path}")
            return {}
        
        try:
            tree = ET.parse(xbrl_path)
            root = tree.getroot()
            
            contexts = {}
            
            # Find all context elements
            for context_elem in root.findall('.//xbrli:context', self.NAMESPACES):
                context_id = context_elem.get('id')
                if not context_id:
                    continue
                
                context_data = self._parse_context(context_elem)
                contexts[context_id] = context_data
            
            logger.info(f"Loaded {len(contexts)} contexts")
            
            return contexts
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse XBRL: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load contexts: {e}")
            return {}
    
    def _parse_context(self, context_elem: ET.Element) -> Dict[str, Any]:
        """Parse a single context element."""
        context_data = {
            'id': context_elem.get('id'),
            'entity': self._parse_entity(context_elem),
            'period': self._parse_period(context_elem),
            'scenario': self._parse_scenario(context_elem)
        }
        
        return context_data
    
    def _parse_entity(self, context_elem: ET.Element) -> Dict[str, Any]:
        """Parse entity information from context."""
        entity_elem = context_elem.find('xbrli:entity', self.NAMESPACES)
        if entity_elem is None:
            return {}
        
        entity_data = {}
        
        # Parse identifier
        identifier_elem = entity_elem.find('xbrli:identifier', self.NAMESPACES)
        if identifier_elem is not None:
            entity_data['identifier'] = {
                'scheme': identifier_elem.get('scheme'),
                'value': identifier_elem.text
            }
        
        # Parse segment (dimensions)
        segment_elem = entity_elem.find('xbrli:segment', self.NAMESPACES)
        if segment_elem is not None:
            entity_data['segment'] = self._parse_dimensions(segment_elem)
        
        return entity_data
    
    def _parse_period(self, context_elem: ET.Element) -> Dict[str, Any]:
        """Parse period information from context."""
        period_elem = context_elem.find('xbrli:period', self.NAMESPACES)
        if period_elem is None:
            return {}
        
        period_data = {}
        
        # Check for instant
        instant_elem = period_elem.find('xbrli:instant', self.NAMESPACES)
        if instant_elem is not None:
            period_data['instant'] = instant_elem.text
            period_data['type'] = 'instant'
            return period_data
        
        # Check for duration
        start_elem = period_elem.find('xbrli:startDate', self.NAMESPACES)
        end_elem = period_elem.find('xbrli:endDate', self.NAMESPACES)
        
        if start_elem is not None and end_elem is not None:
            period_data['start'] = start_elem.text
            period_data['end'] = end_elem.text
            period_data['type'] = 'duration'
        
        return period_data
    
    def _parse_scenario(self, context_elem: ET.Element) -> Dict[str, Any]:
        """Parse scenario information from context."""
        scenario_elem = context_elem.find('xbrli:scenario', self.NAMESPACES)
        if scenario_elem is None:
            return {}
        
        return self._parse_dimensions(scenario_elem)
    
    def _parse_dimensions(self, container_elem: ET.Element) -> Dict[str, Any]:
        """Parse dimensions from segment or scenario."""
        dimensions = {
            'explicitMember': [],
            'typedMember': []
        }
        
        # Parse explicit members
        for member_elem in container_elem.findall('.//xbrldi:explicitMember', self.NAMESPACES):
            dimensions['explicitMember'].append({
                'dimension': member_elem.get('dimension'),
                'value': member_elem.text
            })
        
        # Parse typed members
        for member_elem in container_elem.findall('.//xbrldi:typedMember', self.NAMESPACES):
            # Typed members have child elements with actual values
            typed_data = {
                'dimension': member_elem.get('dimension'),
                'value': self._extract_typed_value(member_elem)
            }
            dimensions['typedMember'].append(typed_data)
        
        return dimensions
    
    def _extract_typed_value(self, typed_elem: ET.Element) -> Any:
        """Extract value from typed member element."""
        # Typed members can have complex structures
        # For simplicity, extract text content
        children = list(typed_elem)
        if children:
            # If has children, take first child's text
            return children[0].text
        return typed_elem.text
    
    def load_units(self, xbrl_path: Path) -> Dict[str, Any]:
        """
        Load units from XBRL filing.
        
        Args:
            xbrl_path: Path to XBRL instance document
            
        Returns:
            Dictionary mapping unit IDs to unit information
        """
        logger.info(f"Loading units from: {xbrl_path}")
        
        if not xbrl_path.exists():
            logger.warning(f"XBRL file not found: {xbrl_path}")
            return {}
        
        try:
            tree = ET.parse(xbrl_path)
            root = tree.getroot()
            
            units = {}
            
            # Find all unit elements
            for unit_elem in root.findall('.//xbrli:unit', self.NAMESPACES):
                unit_id = unit_elem.get('id')
                if not unit_id:
                    continue
                
                unit_data = self._parse_unit(unit_elem)
                units[unit_id] = unit_data
            
            logger.info(f"Loaded {len(units)} units")
            
            return units
            
        except Exception as e:
            logger.error(f"Failed to load units: {e}")
            return {}
    
    def load_facts(self, xbrl_path: Path) -> List[Dict[str, Any]]:
        """
        Load fact elements from XBRL filing for duplicate source analysis.
        
        MARKET-AGNOSTIC: Handles both:
        - Traditional XBRL (XML files)
        - Inline XBRL / iXBRL (HTML files with embedded XBRL)
        
        CRITICAL: This method is ONLY for duplicate source tracing.
        It does NOT affect the mapping process which uses parsed_facts.json.
        
        Args:
            xbrl_path: Path to XBRL instance document (XML or HTML)
            
        Returns:
            List of fact dictionaries with concept, context, value
        """
        logger.info(f"Loading facts from XBRL for source tracing: {xbrl_path}")
        
        if not xbrl_path.exists():
            logger.warning(f"XBRL file not found: {xbrl_path}")
            return []
        
        # Determine file type by extension
        file_ext = xbrl_path.suffix.lower()
        
        if file_ext in ['.htm', '.html', '.xhtml']:
            # Inline XBRL (iXBRL) - embedded in HTML
            logger.info("Detected iXBRL format (inline XBRL in HTML)")
            return self._load_facts_from_ixbrl(xbrl_path)
        elif file_ext == '.xml':
            # Traditional XBRL
            logger.info("Detected traditional XBRL format (XML)")
            return self._load_facts_from_xml(xbrl_path)
        else:
            logger.warning(f"Unknown XBRL file type: {file_ext}")
            return []
    
    def _load_facts_from_xml(self, xbrl_path: Path) -> List[Dict[str, Any]]:
        """Load facts from traditional XBRL XML file."""
        try:
            tree = ET.parse(xbrl_path)
            root = tree.getroot()
            
            facts = []
            
            # Get all namespaces from the root element
            nsmap = {}
            for prefix, uri in root.attrib.items():
                if prefix.startswith('{http://www.w3.org/2000/xmlns/}'):
                    prefix_name = prefix.replace('{http://www.w3.org/2000/xmlns/}', '')
                    nsmap[prefix_name] = uri
            
            # Find all elements that are facts (not structural elements)
            for elem in root:
                tag_local = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                
                # Skip XBRL structural elements
                if tag_local in ['context', 'unit', 'schemaRef', 'roleRef', 'arcroleRef', 'footnoteLink']:
                    continue
                
                # Extract concept
                if '}' in elem.tag:
                    namespace_uri = elem.tag.split('}')[0][1:]
                    local_name = elem.tag.split('}')[1]
                    
                    # Find prefix for this namespace
                    concept_prefix = None
                    for prefix, uri in nsmap.items():
                        if uri == namespace_uri:
                            concept_prefix = prefix
                            break
                    
                    concept = f"{concept_prefix}:{local_name}" if concept_prefix else local_name
                else:
                    concept = elem.tag
                
                context_ref = elem.get('contextRef')
                value = elem.text
                unit_ref = elem.get('unitRef')
                decimals = elem.get('decimals')
                
                if concept and context_ref:
                    facts.append({
                        'concept': concept,
                        'concept_qname': concept,
                        'context_ref': context_ref,
                        'contextRef': context_ref,
                        'value': value,
                        'fact_value': value,
                        'unit_ref': unit_ref,
                        'decimals': decimals
                    })
            
            logger.info(f"Loaded {len(facts)} facts from traditional XBRL")
            return facts
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to load facts from XML: {e}")
            return []
    
    def _load_facts_from_ixbrl(self, xbrl_path: Path) -> List[Dict[str, Any]]:
        """
        Load facts from iXBRL (inline XBRL embedded in HTML).
        
        iXBRL embeds XBRL facts in HTML using special tags like:
        <ix:nonFraction>, <ix:nonNumeric>, <ix:fraction>
        
        We need to parse the HTML and extract these tagged elements.
        """
        try:
            tree = ET.parse(xbrl_path, ET.HTMLParser())
            root = tree.getroot()
            
            facts = []
            
            # Inline XBRL namespaces
            ix_namespaces = [
                '{http://www.xbrl.org/2013/inlineXBRL}',
                '{http://www.xbrl.org/2008/inlineXBRL}',
            ]
            
            # Find all inline XBRL fact elements
            for ix_ns in ix_namespaces:
                # Look for numeric facts
                for elem in root.iter(f'{ix_ns}nonFraction'):
                    fact = self._parse_ixbrl_element(elem, ix_ns)
                    if fact:
                        facts.append(fact)
                
                # Look for non-numeric facts
                for elem in root.iter(f'{ix_ns}nonNumeric'):
                    fact = self._parse_ixbrl_element(elem, ix_ns)
                    if fact:
                        facts.append(fact)
                
                # Look for fraction facts (rare)
                for elem in root.iter(f'{ix_ns}fraction'):
                    fact = self._parse_ixbrl_element(elem, ix_ns)
                    if fact:
                        facts.append(fact)
            
            logger.info(f"Loaded {len(facts)} facts from iXBRL")
            return facts
            
        except Exception as e:
            logger.error(f"Failed to load facts from iXBRL: {e}")
            return []
    
    def _parse_ixbrl_element(self, elem: ET.Element, ix_ns: str) -> Optional[Dict[str, Any]]:
        """Parse an inline XBRL fact element."""
        try:
            # Get concept name
            concept = elem.get('name')
            if not concept:
                return None
            
            # Get context reference
            context_ref = elem.get('contextRef')
            if not context_ref:
                return None
            
            # Get value (text content)
            value = elem.text
            
            # Get other attributes
            unit_ref = elem.get('unitRef')
            decimals = elem.get('decimals')
            
            return {
                'concept': concept,
                'concept_qname': concept,
                'context_ref': context_ref,
                'contextRef': context_ref,
                'value': value,
                'fact_value': value,
                'unit_ref': unit_ref,
                'decimals': decimals
            }
        except Exception:
            return None
    
    def _parse_unit(self, unit_elem: ET.Element) -> Dict[str, Any]:
        """Parse a single unit element."""
        unit_data = {
            'id': unit_elem.get('id'),
            'measures': []
        }
        
        # Parse measures
        for measure_elem in unit_elem.findall('.//xbrli:measure', self.NAMESPACES):
            if measure_elem.text:
                unit_data['measures'].append(measure_elem.text)
        
        # Determine unit type
        if len(unit_data['measures']) == 1:
            measure = unit_data['measures'][0]
            if 'iso4217' in measure.lower() or any(curr in measure.lower() 
                                                    for curr in ['usd', 'eur', 'gbp']):
                unit_data['type'] = 'currency'
            elif 'shares' in measure.lower():
                unit_data['type'] = 'shares'
            else:
                unit_data['type'] = 'other'
        else:
            unit_data['type'] = 'complex'
        
        return unit_data


__all__ = ['XBRLLoader']