# File: fact_extractor.py
# Location: engines/fact_authority/filings_reader/fact_extractor.py

"""
Fact Extractor
==============

Extracts facts from XBRL instance documents.

Specialized component for parsing facts from both traditional XML and
inline XBRL (iXBRL) instance documents. Handles:
- Traditional XML fact extraction
- Inline XBRL (iXBRL) fact extraction
- Fact enrichment with context and unit data

Used by InstanceParser for clean separation of concerns.

Classes:
    FactExtractor: Extracts facts from instance documents
"""

from typing import Dict, List, Optional
import logging
from lxml import etree


logger = logging.getLogger(__name__)


class FactExtractor:
    """
    Extracts facts from XBRL instances.
    
    Specialized extractor for facts in both traditional XML and inline
    XBRL (iXBRL) formats. Handles:
    - Element iteration and filtering
    - Fact identification via contextRef
    - Value extraction
    - Fact enrichment with context/unit data
    """
    
    # XML namespaces
    NAMESPACES = {
        'xbrli': 'http://www.xbrl.org/2003/instance',
        'ix': 'http://www.xbrl.org/2013/inlineXBRL'
    }
    
    def __init__(self):
        """Initialize fact extractor."""
        pass
    
    def extract_facts_xml(
        self,
        root: etree.Element,
        contexts: Dict[str, Dict],
        units: Dict[str, Dict]
    ) -> List[Dict[str, any]]:
        """
        Extract facts from traditional XML XBRL instance.
        
        Iterates through all elements in the instance document and identifies
        facts by presence of contextRef attribute.
        
        Args:
            root: Instance root element
            contexts: Context definitions from ContextExtractor
            units: Unit definitions from ContextExtractor
            
        Returns:
            List of fact dictionaries with enriched context/unit data
        """
        facts = []
        
        # Elements to skip (metadata, not facts)
        skip_elements = {
            f'{{{self.NAMESPACES["xbrli"]}}}context',
            f'{{{self.NAMESPACES["xbrli"]}}}unit',
            f'{{{self.NAMESPACES["xbrli"]}}}xbrl',
            f'{{{self.NAMESPACES["xbrli"]}}}schemaRef'
        }
        
        # Iterate through all elements looking for facts
        for elem in root.iter():
            # Skip metadata elements
            if elem.tag in skip_elements:
                continue
            
            # Check if element has contextRef (indicates it's a fact)
            context_ref = elem.get('contextRef')
            if not context_ref:
                continue
            
            # Create fact dictionary
            fact = self._create_fact_from_element(
                elem,
                context_ref,
                contexts,
                units
            )
            
            if fact:
                facts.append(fact)
        
        logger.debug(f"Extracted {len(facts)} facts from XML instance")
        return facts
    
    def extract_facts_ixbrl(
        self,
        root: etree.Element,
        contexts: Dict[str, Dict],
        units: Dict[str, Dict]
    ) -> List[Dict[str, any]]:
        """
        Extract facts from inline XBRL (iXBRL) instance.
        
        Finds inline XBRL elements (ix:nonFraction, ix:nonNumeric) and
        extracts fact data.
        
        Args:
            root: Instance root element
            contexts: Context definitions from ContextExtractor
            units: Unit definitions from ContextExtractor
            
        Returns:
            List of fact dictionaries with enriched context/unit data
        """
        facts = []
        
        # Extract from ix:nonFraction elements (numeric facts)
        for elem in root.findall('.//ix:nonFraction', self.NAMESPACES):
            context_ref = elem.get('contextRef')
            if context_ref:
                fact = self._create_fact_from_element(
                    elem,
                    context_ref,
                    contexts,
                    units,
                    is_ixbrl=True
                )
                if fact:
                    facts.append(fact)
        
        # Extract from ix:nonNumeric elements (text facts)
        for elem in root.findall('.//ix:nonNumeric', self.NAMESPACES):
            context_ref = elem.get('contextRef')
            if context_ref:
                fact = self._create_fact_from_element(
                    elem,
                    context_ref,
                    contexts,
                    units,
                    is_ixbrl=True
                )
                if fact:
                    facts.append(fact)
        
        logger.debug(f"Extracted {len(facts)} facts from iXBRL instance")
        return facts
    
    def _create_fact_from_element(
        self,
        elem: etree.Element,
        context_ref: str,
        contexts: Dict[str, Dict],
        units: Dict[str, Dict],
        is_ixbrl: bool = False
    ) -> Optional[Dict[str, any]]:
        """
        Create fact dictionary from XML element.
        
        Extracts concept name, value, and references, then enriches with
        context and unit data if available.
        
        Args:
            elem: XML element representing the fact
            context_ref: Context reference ID
            contexts: Available contexts
            units: Available units
            is_ixbrl: Whether this is an inline XBRL element
            
        Returns:
            Complete fact dictionary or None if invalid
        """
        # Extract concept name (strip namespace prefix)
        concept = self._extract_concept_name(elem)
        if not concept:
            return None
        
        # Extract value
        value = self._extract_value(elem, is_ixbrl)
        
        # Extract unit reference
        unit_ref = elem.get('unitRef')
        
        # Extract decimals/precision
        decimals = elem.get('decimals')
        precision = elem.get('precision')
        
        # Build base fact dictionary
        fact_dict = {
            'concept': concept,
            'value': value,
            'context_ref': context_ref,
            'unit_ref': unit_ref,
            'decimals': decimals,
            'precision': precision
        }
        
        # Enrich with context data
        if context_ref in contexts:
            fact_dict['context'] = contexts[context_ref]
        else:
            logger.warning(f"Context {context_ref} not found for fact {concept}")
        
        # Enrich with unit data
        if unit_ref and unit_ref in units:
            fact_dict['unit'] = units[unit_ref]
        
        return fact_dict
    
    def _extract_concept_name(self, elem: etree.Element) -> Optional[str]:
        """
        Extract concept name from element tag.
        
        Strips namespace prefix to get clean concept name.
        
        Args:
            elem: XML element
            
        Returns:
            Concept name or None
        """
        tag = elem.tag
        
        # Strip namespace if present
        if '}' in tag:
            concept = tag.split('}')[1]
        else:
            concept = tag
        
        return concept if concept else None
    
    def _extract_value(self, elem: etree.Element, is_ixbrl: bool) -> Optional[str]:
        """
        Extract value from element.
        
        For iXBRL, may need to handle format attributes and transformations.
        
        Args:
            elem: XML element
            is_ixbrl: Whether this is inline XBRL
            
        Returns:
            Fact value as string or None
        """
        # Get text content
        value = elem.text
        
        if value:
            value = value.strip()
        
        # For iXBRL, check for format attribute
        if is_ixbrl:
            format_attr = elem.get('format')
            if format_attr:
                # Format attribute can indicate transformations needed
                # For now, we just extract the raw value
                pass
        
        return value
    
    def filter_facts_by_concept(
        self,
        facts: List[Dict[str, any]],
        concept_filter: str
    ) -> List[Dict[str, any]]:
        """
        Filter facts by concept name pattern.
        
        Args:
            facts: List of fact dictionaries
            concept_filter: Concept name or pattern to match
            
        Returns:
            Filtered list of facts
        """
        return [
            fact for fact in facts
            if concept_filter in fact.get('concept', '')
        ]
    
    def filter_facts_by_context(
        self,
        facts: List[Dict[str, any]],
        context_ref: str
    ) -> List[Dict[str, any]]:
        """
        Filter facts by context reference.
        
        Args:
            facts: List of fact dictionaries
            context_ref: Context reference to match
            
        Returns:
            Filtered list of facts
        """
        return [
            fact for fact in facts
            if fact.get('context_ref') == context_ref
        ]