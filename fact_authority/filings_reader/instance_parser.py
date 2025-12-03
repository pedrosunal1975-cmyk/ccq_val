# File: instance_parser.py
# Location: engines/fact_authority/filings_reader/instance_parser.py

"""
Instance Parser
===============

Parses XBRL instance documents to extract facts.

Main coordinator for parsing XBRL instance documents. Delegates to:
- ContextExtractor for contexts and units
- FactExtractor for fact extraction

Handles both traditional XML and inline XBRL (iXBRL) formats.

Classes:
    InstanceParser: Main parser coordinating instance document parsing
"""

from pathlib import Path
from typing import Dict, Optional
import logging
from lxml import etree

from engines.fact_authority.filings_reader.context_extractor import ContextExtractor
from engines.fact_authority.filings_reader.fact_extractor import FactExtractor


logger = logging.getLogger(__name__)


class InstanceParser:
    """
    Parses XBRL instance documents.
    
    Main coordinator for instance parsing. Detects format (XML or iXBRL)
    and delegates to specialized extractors for:
    - Contexts and units (ContextExtractor)
    - Facts (FactExtractor)
    
    Returns complete instance data structure with facts, contexts, and units.
    """
    
    # XML namespaces for format detection
    NAMESPACES = {
        'xbrli': 'http://www.xbrl.org/2003/instance',
        'ix': 'http://www.xbrl.org/2013/inlineXBRL'
    }
    
    def __init__(self):
        """Initialize instance parser with helper extractors."""
        self.context_extractor = ContextExtractor()
        self.fact_extractor = FactExtractor()
    
    def parse(self, instance_path: Path) -> Dict[str, any]:
        """
        Parse XBRL instance document.
        
        Auto-detects format (XML or iXBRL) and extracts:
        - Contexts (entity, period, dimensions)
        - Units (monetary, shares, pure)
        - Facts with values
        - Entity identifier
        
        Args:
            instance_path: Path to instance file (.xml or .xhtml)
            
        Returns:
            Dictionary with instance data:
            {
                'format': 'xml' or 'ixbrl',
                'facts': List of fact dictionaries,
                'contexts': Dict mapping context IDs to context data,
                'units': Dict mapping unit IDs to unit data,
                'entity_identifier': Entity identifier string,
                'fact_count': Number of facts,
                'context_count': Number of contexts,
                'unit_count': Number of units
            }
            
        Raises:
            FileNotFoundError: If instance file not found
            ValueError: If instance cannot be parsed
        """
        if not instance_path.exists():
            raise FileNotFoundError(f"Instance file not found: {instance_path}")
        
        logger.info(f"Parsing instance document: {instance_path.name}")
        
        try:
            # Parse XML
            tree = etree.parse(str(instance_path))
            root = tree.getroot()
            
            # Detect format
            format_type = self._detect_format(root, instance_path)
            logger.debug(f"Detected format: {format_type}")
            
            # Extract contexts and units using ContextExtractor
            contexts = self.context_extractor.extract_contexts(root)
            units = self.context_extractor.extract_units(root)
            entity_id = self.context_extractor.extract_entity_identifier(root)
            
            # Extract facts using FactExtractor
            if format_type == 'ixbrl':
                facts = self.fact_extractor.extract_facts_ixbrl(root, contexts, units)
            else:
                facts = self.fact_extractor.extract_facts_xml(root, contexts, units)
            
            # Build result
            result = {
                'format': format_type,
                'facts': facts,
                'contexts': contexts,
                'units': units,
                'entity_identifier': entity_id,
                'fact_count': len(facts),
                'context_count': len(contexts),
                'unit_count': len(units)
            }
            
            logger.info(
                f"Parsed instance: {result['fact_count']} facts, "
                f"{result['context_count']} contexts, "
                f"{result['unit_count']} units, "
                f"format: {format_type}"
            )
            
            return result
        
        except etree.XMLSyntaxError as e:
            raise ValueError(f"Invalid XML in instance {instance_path}: {e}")
        
        except Exception as e:
            logger.error(f"Error parsing instance {instance_path}: {e}")
            raise
    
    def _detect_format(self, root: etree.Element, path: Path) -> str:
        """
        Detect instance format (XML or iXBRL).
        
        Checks file extension and XML content to determine format.
        
        Args:
            root: Instance root element
            path: Instance file path
            
        Returns:
            'xml' for traditional XBRL or 'ixbrl' for inline XBRL
        """
        # Check file extension first
        if path.suffix.lower() in ['.xhtml', '.htm', '.html']:
            return 'ixbrl'
        
        # Check for inline XBRL namespace in document
        # Look at first 2000 bytes for performance
        doc_string = etree.tostring(root, encoding='unicode')[:2000]
        
        if 'http://www.xbrl.org/2013/inlineXBRL' in doc_string:
            return 'ixbrl'
        
        # Check for ix: prefix in root or children
        if root.tag.startswith('{http://www.xbrl.org/2013/inlineXBRL}'):
            return 'ixbrl'
        
        for child in root.iterchildren():
            if child.tag.startswith('{http://www.xbrl.org/2013/inlineXBRL}'):
                return 'ixbrl'
        
        return 'xml'
    
    def get_facts_by_concept(
        self,
        parsed_instance: Dict[str, any],
        concept_name: str
    ) -> list:
        """
        Get all facts for a specific concept.
        
        Args:
            parsed_instance: Result from parse()
            concept_name: Concept name to filter by
            
        Returns:
            List of facts matching the concept
        """
        return self.fact_extractor.filter_facts_by_concept(
            parsed_instance.get('facts', []),
            concept_name
        )
    
    def get_facts_by_context(
        self,
        parsed_instance: Dict[str, any],
        context_ref: str
    ) -> list:
        """
        Get all facts for a specific context.
        
        Args:
            parsed_instance: Result from parse()
            context_ref: Context reference ID
            
        Returns:
            List of facts with the specified context
        """
        return self.fact_extractor.filter_facts_by_context(
            parsed_instance.get('facts', []),
            context_ref
        )
    
    def get_monetary_facts(self, parsed_instance: Dict[str, any]) -> list:
        """
        Get all monetary facts from instance.
        
        Filters facts that have a monetary unit.
        
        Args:
            parsed_instance: Result from parse()
            
        Returns:
            List of monetary facts
        """
        facts = parsed_instance.get('facts', [])
        monetary_facts = []
        
        for fact in facts:
            unit = fact.get('unit')
            if unit:
                measure = unit.get('measure', '')
                # Check if measure contains currency code
                if 'iso4217' in measure.lower() or 'usd' in measure.lower():
                    monetary_facts.append(fact)
        
        return monetary_facts