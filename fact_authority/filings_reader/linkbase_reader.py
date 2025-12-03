# File: linkbase_reader.py
# Location: engines/fact_authority/filings_reader/linkbase_reader.py

"""
Linkbase Reader
===============

Reads XBRL linkbase files (presentation, calculation, definition, label).

Parses all four types of XBRL linkbase files to extract:
- Presentation hierarchies
- Calculation relationships
- Definition relationships (dimensional)
- Label relationships (human-readable labels)

Supports both standard taxonomy and extension linkbases.

Classes:
    LinkbaseReader: Universal linkbase parser
"""

from pathlib import Path
from typing import Dict, List, Optional
import logging
from lxml import etree


logger = logging.getLogger(__name__)


class LinkbaseReader:
    """
    Reads and parses XBRL linkbase files.
    
    Handles all four linkbase types:
    - Presentation: Display hierarchies
    - Calculation: Mathematical relationships
    - Definition: Dimensional relationships
    - Label: Human-readable text
    
    Works universally across SEC, FCA, and ESMA linkbases.
    """
    
    # XML namespaces
    NAMESPACES = {
        'link': 'http://www.xbrl.org/2003/linkbase',
        'xlink': 'http://www.w3.org/1999/xlink',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'gen': 'http://xbrl.org/2008/generic',
        'label': 'http://xbrl.org/2008/label'
    }
    
    def __init__(self):
        """Initialize linkbase reader."""
        pass
    
    def parse_presentation(self, linkbase_path: Path) -> Dict[str, any]:
        """
        Parse presentation linkbase.
        
        Args:
            linkbase_path: Path to _pre.xml file
            
        Returns:
            Dictionary with presentation data:
            {
                'roles': List of role URIs,
                'hierarchies': Dict mapping roles to hierarchies,
                'arc_count': Total number of arcs
            }
        """
        if not linkbase_path.exists():
            raise FileNotFoundError(f"Linkbase not found: {linkbase_path}")
        
        logger.debug(f"Parsing presentation linkbase: {linkbase_path.name}")
        
        tree = etree.parse(str(linkbase_path))
        root = tree.getroot()
        
        hierarchies = {}
        total_arcs = 0
        
        # Find all presentation links
        for link in root.findall('.//link:presentationLink', self.NAMESPACES):
            role = link.get('{http://www.w3.org/1999/xlink}role')
            
            if role:
                arcs = self._extract_arcs(link, 'presentationArc')
                hierarchies[role] = arcs
                total_arcs += len(arcs)
        
        return {
            'roles': list(hierarchies.keys()),
            'hierarchies': hierarchies,
            'arc_count': total_arcs
        }
    
    def parse_calculation(self, linkbase_path: Path) -> Dict[str, any]:
        """
        Parse calculation linkbase.
        
        Args:
            linkbase_path: Path to _cal.xml file
            
        Returns:
            Dictionary with calculation data:
            {
                'roles': List of role URIs,
                'calculations': Dict mapping roles to calc relationships,
                'arc_count': Total number of arcs
            }
        """
        if not linkbase_path.exists():
            raise FileNotFoundError(f"Linkbase not found: {linkbase_path}")
        
        logger.debug(f"Parsing calculation linkbase: {linkbase_path.name}")
        
        tree = etree.parse(str(linkbase_path))
        root = tree.getroot()
        
        calculations = {}
        total_arcs = 0
        
        # Find all calculation links
        for link in root.findall('.//link:calculationLink', self.NAMESPACES):
            role = link.get('{http://www.w3.org/1999/xlink}role')
            
            if role:
                arcs = self._extract_arcs(link, 'calculationArc')
                calculations[role] = arcs
                total_arcs += len(arcs)
        
        return {
            'roles': list(calculations.keys()),
            'calculations': calculations,
            'arc_count': total_arcs
        }
    
    def parse_definition(self, linkbase_path: Path) -> Dict[str, any]:
        """
        Parse definition linkbase.
        
        Args:
            linkbase_path: Path to _def.xml file
            
        Returns:
            Dictionary with definition data:
            {
                'roles': List of role URIs,
                'dimensions': Dict mapping roles to dimensional relationships,
                'arc_count': Total number of arcs
            }
        """
        if not linkbase_path.exists():
            raise FileNotFoundError(f"Linkbase not found: {linkbase_path}")
        
        logger.debug(f"Parsing definition linkbase: {linkbase_path.name}")
        
        tree = etree.parse(str(linkbase_path))
        root = tree.getroot()
        
        dimensions = {}
        total_arcs = 0
        
        # Find all definition links
        for link in root.findall('.//link:definitionLink', self.NAMESPACES):
            role = link.get('{http://www.w3.org/1999/xlink}role')
            
            if role:
                arcs = self._extract_arcs(link, 'definitionArc')
                dimensions[role] = arcs
                total_arcs += len(arcs)
        
        return {
            'roles': list(dimensions.keys()),
            'dimensions': dimensions,
            'arc_count': total_arcs
        }
    
    def parse_label(self, linkbase_path: Path) -> Dict[str, any]:
        """
        Parse label linkbase.
        
        Args:
            linkbase_path: Path to _lab.xml file
            
        Returns:
            Dictionary with label data:
            {
                'labels': Dict mapping concept names to labels,
                'label_count': Total number of labels,
                'languages': Set of languages found
            }
        """
        if not linkbase_path.exists():
            raise FileNotFoundError(f"Linkbase not found: {linkbase_path}")
        
        logger.debug(f"Parsing label linkbase: {linkbase_path.name}")
        
        tree = etree.parse(str(linkbase_path))
        root = tree.getroot()
        
        labels = {}
        languages = set()
        
        # Find all label resources
        for label_elem in root.findall('.//link:label', self.NAMESPACES):
            label_text = label_elem.text
            label_role = label_elem.get('{http://www.w3.org/1999/xlink}role')
            lang = label_elem.get('{http://www.w3.org/XML/1998/namespace}lang')
            label_id = label_elem.get('{http://www.w3.org/1999/xlink}label')
            
            if label_text and label_id:
                labels[label_id] = {
                    'text': label_text.strip(),
                    'role': label_role,
                    'language': lang
                }
                
                if lang:
                    languages.add(lang)
        
        # Map labels to concepts via labelArcs
        concept_labels = self._map_labels_to_concepts(root, labels)
        
        return {
            'labels': concept_labels,
            'label_count': len(concept_labels),
            'languages': list(languages)
        }
    
    def _extract_arcs(self, link_element: etree.Element, arc_type: str) -> List[Dict[str, any]]:
        """
        Extract arcs from a link element.
        
        Args:
            link_element: Link XML element
            arc_type: Type of arc to extract
            
        Returns:
            List of arc data dictionaries
        """
        arcs = []
        
        # Find all arcs of specified type
        for arc in link_element.findall(f'.//link:{arc_type}', self.NAMESPACES):
            from_ref = arc.get('{http://www.w3.org/1999/xlink}from')
            to_ref = arc.get('{http://www.w3.org/1999/xlink}to')
            order = arc.get('order')
            
            arc_data = {
                'from': from_ref,
                'to': to_ref,
                'order': float(order) if order else None,
                'arcrole': arc.get('{http://www.w3.org/1999/xlink}arcrole')
            }
            
            # Add weight for calculation arcs
            if arc_type == 'calculationArc':
                weight = arc.get('weight')
                arc_data['weight'] = float(weight) if weight else None
            
            # Add priority
            priority = arc.get('priority')
            if priority:
                arc_data['priority'] = int(priority)
            
            arcs.append(arc_data)
        
        return arcs
    
    def _map_labels_to_concepts(
        self,
        root: etree.Element,
        labels: Dict[str, Dict[str, str]]
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Map label resources to concept names.
        
        Args:
            root: Linkbase root element
            labels: Dictionary of label resources
            
        Returns:
            Dictionary mapping concept names to their labels
        """
        concept_labels = {}
        
        # Find all labelArcs
        for arc in root.findall('.//link:labelArc', self.NAMESPACES):
            from_ref = arc.get('{http://www.w3.org/1999/xlink}from')
            to_ref = arc.get('{http://www.w3.org/1999/xlink}to')
            
            # Find the concept locator
            for loc in root.findall('.//link:loc', self.NAMESPACES):
                loc_label = loc.get('{http://www.w3.org/1999/xlink}label')
                
                if loc_label == from_ref:
                    href = loc.get('{http://www.w3.org/1999/xlink}href')
                    
                    if href and '#' in href:
                        concept_name = href.split('#')[1]
                        
                        if concept_name not in concept_labels:
                            concept_labels[concept_name] = []
                        
                        if to_ref in labels:
                            concept_labels[concept_name].append(labels[to_ref])
        
        return concept_labels
    
    def parse_all(
        self,
        presentation_path: Optional[Path] = None,
        calculation_path: Optional[Path] = None,
        definition_path: Optional[Path] = None,
        label_path: Optional[Path] = None
    ) -> Dict[str, any]:
        """
        Parse all provided linkbase files.
        
        Args:
            presentation_path: Optional presentation linkbase path
            calculation_path: Optional calculation linkbase path
            definition_path: Optional definition linkbase path
            label_path: Optional label linkbase path
            
        Returns:
            Combined dictionary with all linkbase data
        """
        result = {
            'presentation': None,
            'calculation': None,
            'definition': None,
            'label': None
        }
        
        if presentation_path and presentation_path.exists():
            try:
                result['presentation'] = self.parse_presentation(presentation_path)
            except Exception as e:
                logger.error(f"Error parsing presentation linkbase: {e}")
        
        if calculation_path and calculation_path.exists():
            try:
                result['calculation'] = self.parse_calculation(calculation_path)
            except Exception as e:
                logger.error(f"Error parsing calculation linkbase: {e}")
        
        if definition_path and definition_path.exists():
            try:
                result['definition'] = self.parse_definition(definition_path)
            except Exception as e:
                logger.error(f"Error parsing definition linkbase: {e}")
        
        if label_path and label_path.exists():
            try:
                result['label'] = self.parse_label(label_path)
            except Exception as e:
                logger.error(f"Error parsing label linkbase: {e}")
        
        return result