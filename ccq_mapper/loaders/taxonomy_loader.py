"""
Taxonomy Loader
===============

Loads taxonomy files for VALIDATION, not matching.

CRITICAL: Taxonomies loaded AFTER construction for validation.
NO concept index building.
"""

from typing import Dict, Any, List
from pathlib import Path
import xml.etree.ElementTree as ET

from core.system_logger import get_logger

logger = get_logger(__name__)


class TaxonomyLoader:
    """
    Load taxonomies for post-construction validation.
    
    Loads:
    - Concept definitions
    - Balance types
    - Period types
    - Labels
    
    Does NOT build search indexes or matching structures.
    """
    
    NAMESPACES = {
        'xsd': 'http://www.w3.org/2001/XMLSchema',
        'xbrli': 'http://www.xbrl.org/2003/instance',
        'link': 'http://www.xbrl.org/2003/linkbase',
        'xlink': 'http://www.w3.org/1999/xlink',
        'label': 'http://www.xbrl.org/2003/label'
    }
    
    def load_taxonomies(self, taxonomy_paths: List[Path]) -> Dict[str, Any]:
        """
        Load taxonomy files.
        
        Args:
            taxonomy_paths: List of paths to taxonomy directories or files
            
        Returns:
            Dictionary with taxonomy information
        """
        logger.info(f"Loading {len(taxonomy_paths)} taxonomy paths")
        
        taxonomies = {
            'concepts': {},
            'labels': {},
            'references': {},
            'presentations': {}
        }
        
        for path in taxonomy_paths:
            try:
                if path.is_dir():
                    self._load_taxonomy_directory(path, taxonomies)
                elif path.is_file() and path.suffix == '.xsd':
                    self._load_schema_file(path, taxonomies)
            except Exception as e:
                logger.error(f"Failed to load taxonomy from {path}: {e}")
                continue
        
        logger.info(
            f"Loaded {len(taxonomies['concepts'])} concepts, "
            f"{len(taxonomies['labels'])} labels"
        )
        
        return taxonomies
    
    def _load_taxonomy_directory(self, directory: Path, taxonomies: Dict[str, Any]):
        """
        Load all taxonomy files from a directory using recursive search.
        
        Searches ALL subdirectories (up to 5 levels) and loads files from ALL locations.
        Does NOT stop at first level - collects elements from all XSD files found.
        """
        if not directory.exists():
            logger.warning(f"Taxonomy directory does not exist: {directory}")
            return
        
        # Collect all XSD and label files at ALL depths (0-5 levels)
        xsd_files = []
        linkbase_files = []
        
        for depth in range(6):  # 0 to 5 levels
            xsd_pattern = '/'.join(['*'] * depth) + '/*.xsd' if depth > 0 else '*.xsd'
            lab_pattern = '/'.join(['*'] * depth) + '/*_lab.xml' if depth > 0 else '*_lab.xml'
            
            # Find files at this depth
            found_xsd = list(directory.glob(xsd_pattern))
            found_lab = list(directory.glob(lab_pattern))
            
            xsd_files.extend(found_xsd)
            linkbase_files.extend(found_lab)
            
            if found_xsd:
                logger.debug(
                    f"Found {len(found_xsd)} .xsd files at depth {depth} in {directory}"
                )
            if found_lab:
                logger.debug(
                    f"Found {len(found_lab)} label files at depth {depth} in {directory}"
                )
        
        # Log summary
        logger.info(
            f"Collected {len(xsd_files)} .xsd files and {len(linkbase_files)} label files "
            f"from {directory} (searched 0-5 levels deep)"
        )
        
        # Load all found schema files
        for xsd_file in xsd_files:
            self._load_schema_file(xsd_file, taxonomies)
        
        # Load all found linkbase files
        for linkbase_file in linkbase_files:
            self._load_label_linkbase(linkbase_file, taxonomies)
        
        if not xsd_files and not linkbase_files:
            logger.warning(
                f"No taxonomy files found in {directory} "
                f"(searched up to 5 levels deep)"
            )
    
    def _load_schema_file(self, schema_path: Path, taxonomies: Dict[str, Any]):
        """
        Load concept definitions from schema file.
        
        Extracts: element names, types, balance, period type
        """
        logger.debug(f"Loading schema: {schema_path}")
        
        try:
            tree = ET.parse(schema_path)
            root = tree.getroot()
            
            # Get target namespace from root for proper qname construction
            target_namespace = root.get('targetNamespace', '')
            
            # Find all element definitions
            for element in root.findall('.//xsd:element', self.NAMESPACES):
                concept_data = self._parse_element(element, schema_path, target_namespace)
                if concept_data:
                    qname = concept_data['qname']
                    taxonomies['concepts'][qname] = concept_data
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse schema {schema_path}: {e}")
        except Exception as e:
            logger.error(f"Error loading schema {schema_path}: {e}")
    
    def _parse_element(self, element: ET.Element, source_file: Path, target_namespace: str = '') -> Dict[str, Any]:
        """Parse an element definition."""
        name = element.get('name')
        if not name:
            return {}
        
        # Extract namespace prefix from target namespace URI
        namespace_prefix = self._get_namespace_prefix(target_namespace)
        qname = f"{namespace_prefix}:{name}" if namespace_prefix else name
        
        concept_data = {
            'qname': qname,
            'name': name,
            'namespace': namespace_prefix,
            'type': element.get('type'),
            'substitution_group': element.get('substitutionGroup'),
            'abstract': element.get('abstract') == 'true',
            'nillable': element.get('nillable') == 'true',
            'source_file': str(source_file)
        }
        
        # Extract XBRL-specific attributes
        balance = element.get('{http://www.xbrl.org/2003/instance}balance')
        period_type = element.get('{http://www.xbrl.org/2003/instance}periodType')
        
        if balance:
            concept_data['balance_type'] = balance
        if period_type:
            concept_data['period_type'] = period_type
        
        return concept_data
    
    def _get_namespace_prefix(self, target_namespace: str) -> str:
        """
        Convert target namespace URI to standard prefix.
        
        Maps full namespace URIs to their conventional prefixes.
        """
        # Map of namespace URIs to standard prefixes
        namespace_map = {
            'http://fasb.org/us-gaap/2024': 'us-gaap',
            'http://fasb.org/us-gaap/2023': 'us-gaap',
            'http://fasb.org/us-gaap/2022': 'us-gaap',
            'http://fasb.org/us-gaap/2021': 'us-gaap',
            'http://fasb.org/us-gaap/2020': 'us-gaap',
            'http://xbrl.sec.gov/dei/2024': 'dei',
            'http://xbrl.sec.gov/dei/2023': 'dei',
            'http://xbrl.sec.gov/dei/2022': 'dei',
            'http://xbrl.sec.gov/dei/2021': 'dei',
            'http://xbrl.sec.gov/dei/2020': 'dei',
            'http://fasb.org/srt/2024': 'srt',
            'http://fasb.org/srt/2023': 'srt',
            'http://fasb.org/srt/2022': 'srt',
            'http://fasb.org/srt/2021': 'srt',
            'http://fasb.org/srt/2020': 'srt',
        }
        
        # Direct lookup
        if target_namespace in namespace_map:
            return namespace_map[target_namespace]
        
        # Pattern matching for unknown versions
        if 'us-gaap' in target_namespace:
            return 'us-gaap'
        elif 'dei' in target_namespace or 'xbrl.sec.gov/dei' in target_namespace:
            return 'dei'
        elif 'srt' in target_namespace:
            return 'srt'
        elif 'ecd' in target_namespace:
            return 'ecd'
        
        # Default: return empty (no prefix)
        return ''
    
    def _load_label_linkbase(self, linkbase_path: Path, taxonomies: Dict[str, Any]):
        """
        Load labels from label linkbase.
        
        Maps concept names to human-readable labels.
        """
        logger.debug(f"Loading labels: {linkbase_path}")
        
        try:
            tree = ET.parse(linkbase_path)
            root = tree.getroot()
            
            # Find all labels
            for label_elem in root.findall('.//label:label', self.NAMESPACES):
                label_data = self._parse_label(label_elem)
                if label_data:
                    concept_ref = label_data['concept']
                    role = label_data['role']
                    
                    if concept_ref not in taxonomies['labels']:
                        taxonomies['labels'][concept_ref] = {}
                    
                    taxonomies['labels'][concept_ref][role] = label_data['text']
            
        except Exception as e:
            logger.error(f"Error loading labels {linkbase_path}: {e}")
    
    def _parse_label(self, label_elem: ET.Element) -> Dict[str, Any]:
        """Parse a label element."""
        label_text = label_elem.text
        if not label_text:
            return {}
        
        return {
            'concept': label_elem.get('{http://www.w3.org/1999/xlink}label'),
            'role': label_elem.get('{http://www.w3.org/1999/xlink}role', 'standard'),
            'lang': label_elem.get('{http://www.w3.org/XML/1998/namespace}lang', 'en'),
            'text': label_text.strip()
        }
    
    def get_concept_info(
        self,
        qname: str,
        taxonomies: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get information about a concept from loaded taxonomies.
        
        Used for validation, not matching.
        """
        concept = taxonomies['concepts'].get(qname, {})
        labels = taxonomies['labels'].get(qname, {})
        
        return {
            'qname': qname,
            'exists': bool(concept),
            'concept_data': concept,
            'labels': labels,
            'balance_type': concept.get('balance_type'),
            'period_type': concept.get('period_type'),
            'abstract': concept.get('abstract', False)
        }
    
    def validate_concept(
        self,
        qname: str,
        expected_properties: Dict[str, Any],
        taxonomies: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate that a concept exists and has expected properties.
        
        This is VALIDATION, not MATCHING.
        """
        concept_info = self.get_concept_info(qname, taxonomies)
        
        if not concept_info['exists']:
            return {
                'valid': False,
                'reason': f"Concept {qname} not found in taxonomy",
                'concept_info': concept_info
            }
        
        # Check properties
        mismatches = []
        
        expected_balance = expected_properties.get('balance_type')
        actual_balance = concept_info.get('balance_type')
        if expected_balance and actual_balance and expected_balance != actual_balance:
            mismatches.append(f"Balance type: expected {expected_balance}, got {actual_balance}")
        
        expected_period = expected_properties.get('period_type')
        actual_period = concept_info.get('period_type')
        if expected_period and actual_period and expected_period != actual_period:
            mismatches.append(f"Period type: expected {expected_period}, got {actual_period}")
        
        if mismatches:
            return {
                'valid': False,
                'reason': 'Property mismatches',
                'mismatches': mismatches,
                'concept_info': concept_info
            }
        
        return {
            'valid': True,
            'concept_info': concept_info
        }


__all__ = ['TaxonomyLoader']