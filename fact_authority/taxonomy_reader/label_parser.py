"""
Label Linkbase Parser
=====================

Parses XBRL label linkbases to extract human-readable concept labels.

Label linkbases provide human-readable names for concepts in multiple
languages and styles:
- Standard labels: "Cash and Cash Equivalents"
- Terse labels: "Cash"
- Verbose labels: "Cash and Cash Equivalents at Carrying Value"
- Documentation: Detailed concept descriptions

This enables readable reports and multi-language support.

Classes:
    LabelParser: Parses label linkbase files
"""

from pathlib import Path
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET
import logging


logger = logging.getLogger(__name__)


class LabelParser:
    """
    Parses XBRL label linkbase files.
    
    Extracts labels (human-readable names) for concepts in various
    languages and styles. These labels are used for display and reporting.
    
    Example label in linkbase:
        <label xlink:type="resource"
               xlink:label="us-gaap_Cash_label"
               xlink:role="http://www.xbrl.org/2003/role/label"
               xml:lang="en-US">
          Cash and Cash Equivalents
        </label>
    """
    
    # Standard XML namespaces
    NAMESPACES = {
        'link': 'http://www.xbrl.org/2003/linkbase',
        'xlink': 'http://www.w3.org/1999/xlink',
        'xml': 'http://www.w3.org/XML/1998/namespace',
    }
    
    # Standard label roles
    LABEL_ROLE = 'http://www.xbrl.org/2003/role/label'
    TERSE_LABEL_ROLE = 'http://www.xbrl.org/2003/role/terseLabel'
    VERBOSE_LABEL_ROLE = 'http://www.xbrl.org/2003/role/verboseLabel'
    DOCUMENTATION_ROLE = 'http://www.xbrl.org/2003/role/documentation'
    TOTAL_LABEL_ROLE = 'http://www.xbrl.org/2003/role/totalLabel'
    PERIOD_START_LABEL_ROLE = 'http://www.xbrl.org/2003/role/periodStartLabel'
    PERIOD_END_LABEL_ROLE = 'http://www.xbrl.org/2003/role/periodEndLabel'
    NEGATED_LABEL_ROLE = 'http://www.xbrl.org/2009/role/negatedLabel'
    
    # Role type mapping for simpler keys
    ROLE_TYPE_MAP = {
        LABEL_ROLE: 'standard',
        TERSE_LABEL_ROLE: 'terse',
        VERBOSE_LABEL_ROLE: 'verbose',
        DOCUMENTATION_ROLE: 'documentation',
        TOTAL_LABEL_ROLE: 'total',
        PERIOD_START_LABEL_ROLE: 'period_start',
        PERIOD_END_LABEL_ROLE: 'period_end',
        NEGATED_LABEL_ROLE: 'negated',
    }
    
    def __init__(self):
        """Initialize label parser."""
        pass
    
    def parse(self, label_file: Path) -> Dict[str, Dict[str, Dict[str, str]]]:
        """
        Parse a label linkbase file.
        
        Args:
            label_file: Path to *_lab.xml file
            
        Returns:
            Dictionary organized by concept, then label type, then language:
            {
                'us-gaap:Cash': {
                    'standard': {
                        'en-US': 'Cash and Cash Equivalents',
                        'en': 'Cash and Cash Equivalents'
                    },
                    'terse': {
                        'en-US': 'Cash'
                    },
                    'documentation': {
                        'en-US': 'Amount of currency on hand...'
                    }
                }
            }
            
        Raises:
            FileNotFoundError: If label file doesn't exist
        """
        if not label_file.exists():
            raise FileNotFoundError(f"Label file not found: {label_file}")
        
        labels = {}
        
        try:
            tree = ET.parse(label_file)
            root = tree.getroot()
            
            # Find all labelLink elements
            for label_link in root.findall('.//link:labelLink', self.NAMESPACES):
                # Collect locators and labels
                locs = self._collect_locators(label_link)
                label_resources = self._collect_labels(label_link)
                arcs = self._collect_arcs(label_link)
                
                # Build concept → label mappings
                self._build_label_mappings(locs, label_resources, arcs, labels)
            
            logger.debug(f"Parsed labels for {len(labels)} concepts from {label_file.name}")
            
        except ET.ParseError as e:
            logger.warning(f"Failed to parse label file {label_file}: {e}")
            return {}
        
        return labels
    
    def _collect_locators(self, label_link: ET.Element) -> Dict[str, str]:
        """
        Collect all loc elements (concept locators).
        
        Args:
            label_link: labelLink XML element
            
        Returns:
            Dictionary mapping labels to concept names
        """
        locs = {}
        
        for loc in label_link.findall('.//link:loc', self.NAMESPACES):
            label = loc.get('{http://www.w3.org/1999/xlink}label', '')
            href = loc.get('{http://www.w3.org/1999/xlink}href', '')
            
            if label and href:
                concept = self._extract_concept_from_href(href)
                if concept:
                    locs[label] = concept
        
        return locs
    
    def _collect_labels(
        self,
        label_link: ET.Element
    ) -> Dict[str, Dict[str, any]]:
        """
        Collect all label elements (text resources).
        
        Args:
            label_link: labelLink XML element
            
        Returns:
            Dictionary mapping label IDs to label data
        """
        label_resources = {}
        
        for label in label_link.findall('.//link:label', self.NAMESPACES):
            label_id = label.get('{http://www.w3.org/1999/xlink}label', '')
            role = label.get('{http://www.w3.org/1999/xlink}role', self.LABEL_ROLE)
            lang = label.get('{http://www.w3.org/XML/1998/namespace}lang', 'en')
            text = label.text or ''
            
            if label_id:
                # Classify label type
                label_type = self._classify_label_type(role)
                
                label_resources[label_id] = {
                    'text': text.strip(),
                    'type': label_type,
                    'language': lang,
                    'role': role
                }
        
        return label_resources
    
    def _collect_arcs(self, label_link: ET.Element) -> List[Dict[str, str]]:
        """
        Collect all labelArc elements (relationships).
        
        Args:
            label_link: labelLink XML element
            
        Returns:
            List of arc dictionaries
        """
        arcs = []
        
        for arc in label_link.findall('.//link:labelArc', self.NAMESPACES):
            from_label = arc.get('{http://www.w3.org/1999/xlink}from', '')
            to_label = arc.get('{http://www.w3.org/1999/xlink}to', '')
            
            if from_label and to_label:
                arcs.append({
                    'from': from_label,
                    'to': to_label
                })
        
        return arcs
    
    def _build_label_mappings(
        self,
        locs: Dict[str, str],
        label_resources: Dict[str, Dict[str, any]],
        arcs: List[Dict[str, str]],
        labels: Dict[str, Dict[str, Dict[str, str]]]
    ):
        """
        Build concept → label mappings from arcs.
        
        Args:
            locs: Locator mappings
            label_resources: Label resource data
            arcs: Arc relationships
            labels: Output dictionary to populate
        """
        for arc in arcs:
            concept = locs.get(arc['from'])
            label_data = label_resources.get(arc['to'])
            
            if concept and label_data:
                # Initialize concept entry
                if concept not in labels:
                    labels[concept] = {}
                
                label_type = label_data['type']
                language = label_data['language']
                text = label_data['text']
                
                # Initialize label type entry
                if label_type not in labels[concept]:
                    labels[concept][label_type] = {}
                
                # Store label text by language
                labels[concept][label_type][language] = text
    
    def _extract_concept_from_href(self, href: str) -> Optional[str]:
        """
        Extract concept name from href.
        
        Args:
            href: Href string (e.g., "us-gaap-2025.xsd#us-gaap_Cash")
            
        Returns:
            Concept name (e.g., "us-gaap:Cash") or None
        """
        if '#' not in href:
            return None
        
        anchor = href.split('#')[1]
        
        # Convert underscore to colon
        if '_' in anchor:
            return anchor.replace('_', ':', 1)
        
        return anchor
    
    def _classify_label_type(self, role: str) -> str:
        """
        Classify label role into a simpler type.
        
        Args:
            role: Label role URI
            
        Returns:
            Label type ('standard', 'terse', 'verbose', etc.)
        """
        return self.ROLE_TYPE_MAP.get(role, 'other')
    
    def parse_multiple(
        self,
        label_files: List[Path]
    ) -> Dict[str, Dict[str, Dict[str, str]]]:
        """
        Parse multiple label linkbase files.
        
        Args:
            label_files: List of label file paths
            
        Returns:
            Combined dictionary of all labels
        """
        all_labels = {}
        
        for label_file in label_files:
            try:
                labels = self.parse(label_file)
                
                # Merge labels
                for concept, concept_labels in labels.items():
                    if concept not in all_labels:
                        all_labels[concept] = {}
                    
                    for label_type, type_labels in concept_labels.items():
                        if label_type not in all_labels[concept]:
                            all_labels[concept][label_type] = {}
                        
                        # Merge language variants
                        all_labels[concept][label_type].update(type_labels)
                
            except FileNotFoundError:
                logger.warning(f"Label file not found: {label_file}")
                continue
            except Exception as e:
                logger.error(f"Error parsing {label_file}: {e}")
                continue
        
        logger.info(
            f"Parsed labels for {len(all_labels)} concepts from "
            f"{len(label_files)} files"
        )
        
        return all_labels
    
    def get_label(
        self,
        labels: Dict[str, Dict[str, Dict[str, str]]],
        concept: str,
        label_type: str = 'standard',
        language: str = 'en-US'
    ) -> Optional[str]:
        """
        Get a specific label for a concept.
        
        Args:
            labels: Labels dictionary
            concept: Concept QName
            label_type: Type of label ('standard', 'terse', 'verbose', etc.)
            language: Language code ('en-US', 'en', etc.)
            
        Returns:
            Label text or None if not found
        """
        concept_labels = labels.get(concept, {})
        type_labels = concept_labels.get(label_type, {})
        
        # Try exact language match
        if language in type_labels:
            return type_labels[language]
        
        # Try fallback to base language (e.g., 'en' if 'en-US' not found)
        if '-' in language:
            base_lang = language.split('-')[0]
            if base_lang in type_labels:
                return type_labels[base_lang]
        
        # Try any available language for this type
        if type_labels:
            return next(iter(type_labels.values()))
        
        return None
    
    def get_statistics(
        self,
        labels: Dict[str, Dict[str, Dict[str, str]]]
    ) -> Dict[str, int]:
        """
        Get statistics about parsed labels.
        
        Args:
            labels: Dictionary of labels
            
        Returns:
            Dictionary of statistics
        """
        stats = {
            'total_concepts': len(labels),
            'concepts_with_standard': 0,
            'concepts_with_terse': 0,
            'concepts_with_verbose': 0,
            'concepts_with_documentation': 0,
            'total_labels': 0,
            'languages': set(),
        }
        
        for concept_labels in labels.values():
            # Count by label type
            if 'standard' in concept_labels:
                stats['concepts_with_standard'] += 1
            if 'terse' in concept_labels:
                stats['concepts_with_terse'] += 1
            if 'verbose' in concept_labels:
                stats['concepts_with_verbose'] += 1
            if 'documentation' in concept_labels:
                stats['concepts_with_documentation'] += 1
            
            # Count total labels and languages
            for type_labels in concept_labels.values():
                stats['total_labels'] += len(type_labels)
                stats['languages'].update(type_labels.keys())
        
        # Convert set to count
        stats['unique_languages'] = len(stats['languages'])
        del stats['languages']
        
        return stats