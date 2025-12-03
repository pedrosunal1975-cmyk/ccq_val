"""
Definition Linkbase Parser
==========================

Parses XBRL definition linkbases to extract dimensional relationships.

Definition linkbases define dimensional structures like:
- Axes (dimensions): Geographic, Product, Segment
- Domains: Categories within each axis
- Members: Specific values (US, Europe, Asia)
- Hypercubes: Tables defining which dimensions apply to which concepts

This enables understanding of segmented data like "Revenue[Asia]" vs "Revenue[US]".

Classes:
    DefinitionParser: Parses definition linkbase files
"""

from pathlib import Path
from typing import Dict, List, Optional, Set
import xml.etree.ElementTree as ET
import logging


logger = logging.getLogger(__name__)


class DefinitionParser:
    """
    Parses XBRL definition linkbase files.
    
    Extracts dimensional relationships including axes, domains, members,
    and hypercube structures. These define how concepts can be broken down
    into segments (by geography, product line, time period, etc.).
    
    Example dimension in linkbase:
        <definitionLink xlink:role="...">
          <definitionArc xlink:arcrole="dimension-domain"
                         xlink:from="GeographicAxis" 
                         xlink:to="GeographicDomain"/>
          <definitionArc xlink:arcrole="domain-member"
                         xlink:from="GeographicDomain"
                         xlink:to="USMember"/>
        </definitionLink>
    """
    
    # Standard XML namespaces
    NAMESPACES = {
        'link': 'http://www.xbrl.org/2003/linkbase',
        'xlink': 'http://www.w3.org/1999/xlink',
        'xbrldt': 'http://xbrl.org/2005/xbrldt',
    }
    
    # Arc roles for dimensional relationships
    DIMENSION_DOMAIN = 'http://xbrl.org/int/dim/arcrole/dimension-domain'
    DOMAIN_MEMBER = 'http://xbrl.org/int/dim/arcrole/domain-member'
    HYPERCUBE_DIMENSION = 'http://xbrl.org/int/dim/arcrole/hypercube-dimension'
    ALL = 'http://xbrl.org/int/dim/arcrole/all'
    NOTALL = 'http://xbrl.org/int/dim/arcrole/notAll'
    
    def __init__(self):
        """Initialize definition parser."""
        pass
    
    def parse(self, definition_file: Path) -> Dict[str, any]:
        """
        Parse a definition linkbase file.
        
        Args:
            definition_file: Path to *_def.xml file
            
        Returns:
            Dictionary containing:
            {
                'axes': {
                    'us-gaap:StatementGeographicalAxis': {
                        'domain': 'us-gaap:StatementGeographicalDomain',
                        'default_member': 'us-gaap:ConsolidatedMember',
                        'members': ['us-gaap:USMember', 'us-gaap:EuropeMember', ...]
                    }
                },
                'hypercubes': {
                    'us-gaap:RevenueByGeographyTable': {
                        'dimensions': ['us-gaap:StatementGeographicalAxis'],
                        'primary_items': ['us-gaap:Revenues']
                    }
                }
            }
            
        Raises:
            FileNotFoundError: If definition file doesn't exist
        """
        if not definition_file.exists():
            raise FileNotFoundError(f"Definition file not found: {definition_file}")
        
        dimensions = {
            'axes': {},
            'hypercubes': {},
        }
        
        try:
            tree = ET.parse(definition_file)
            root = tree.getroot()
            
            # Find all definitionLink elements
            for def_link in root.findall('.//link:definitionLink', self.NAMESPACES):
                # Collect locators and arcs
                locs = self._collect_locators(def_link)
                arcs = self._collect_arcs(def_link)
                
                # Parse dimensional relationships
                self._parse_dimension_domain(arcs, locs, dimensions)
                self._parse_domain_member(arcs, locs, dimensions)
                self._parse_hypercubes(arcs, locs, dimensions)
            
            logger.debug(
                f"Parsed {len(dimensions['axes'])} axes and "
                f"{len(dimensions['hypercubes'])} hypercubes from {definition_file.name}"
            )
            
        except ET.ParseError as e:
            logger.warning(f"Failed to parse definition file {definition_file}: {e}")
            return {'axes': {}, 'hypercubes': {}}
        
        return dimensions
    
    def _collect_locators(self, def_link: ET.Element) -> Dict[str, str]:
        """
        Collect all loc elements (concept locators).
        
        Args:
            def_link: definitionLink XML element
            
        Returns:
            Dictionary mapping labels to concept names
        """
        locs = {}
        
        for loc in def_link.findall('.//link:loc', self.NAMESPACES):
            label = loc.get('{http://www.w3.org/1999/xlink}label', '')
            href = loc.get('{http://www.w3.org/1999/xlink}href', '')
            
            if label and href:
                concept = self._extract_concept_from_href(href)
                if concept:
                    locs[label] = concept
        
        return locs
    
    def _collect_arcs(self, def_link: ET.Element) -> List[Dict[str, any]]:
        """
        Collect all definitionArc elements (relationships).
        
        Args:
            def_link: definitionLink XML element
            
        Returns:
            List of arc dictionaries
        """
        arcs = []
        
        for arc in def_link.findall('.//link:definitionArc', self.NAMESPACES):
            from_label = arc.get('{http://www.w3.org/1999/xlink}from', '')
            to_label = arc.get('{http://www.w3.org/1999/xlink}to', '')
            arcrole = arc.get('{http://www.w3.org/1999/xlink}arcrole', '')
            order = arc.get('order', '1.0')
            
            if from_label and to_label and arcrole:
                arcs.append({
                    'from': from_label,
                    'to': to_label,
                    'arcrole': arcrole,
                    'order': float(order)
                })
        
        return arcs
    
    def _parse_dimension_domain(
        self,
        arcs: List[Dict[str, any]],
        locs: Dict[str, str],
        dimensions: Dict[str, any]
    ):
        """
        Parse dimension-domain relationships.
        
        Links axes to their domains (e.g., GeographicAxis → GeographicDomain).
        
        Args:
            arcs: List of arc dictionaries
            locs: Locator mappings
            dimensions: Dimensions dictionary to populate
        """
        for arc in arcs:
            if arc['arcrole'] == self.DIMENSION_DOMAIN:
                axis = locs.get(arc['from'], arc['from'])
                domain = locs.get(arc['to'], arc['to'])
                
                if axis not in dimensions['axes']:
                    dimensions['axes'][axis] = {
                        'domain': domain,
                        'members': [],
                        'default_member': None
                    }
                else:
                    dimensions['axes'][axis]['domain'] = domain
    
    def _parse_domain_member(
        self,
        arcs: List[Dict[str, any]],
        locs: Dict[str, str],
        dimensions: Dict[str, any]
    ):
        """
        Parse domain-member relationships.
        
        Links domains to their members (e.g., GeographicDomain → USMember).
        
        Args:
            arcs: List of arc dictionaries
            locs: Locator mappings
            dimensions: Dimensions dictionary to populate
        """
        # Build domain to members mapping
        domain_members = {}
        
        for arc in arcs:
            if arc['arcrole'] == self.DOMAIN_MEMBER:
                domain = locs.get(arc['from'], arc['from'])
                member = locs.get(arc['to'], arc['to'])
                
                if domain not in domain_members:
                    domain_members[domain] = []
                
                domain_members[domain].append({
                    'member': member,
                    'order': arc['order']
                })
        
        # Sort members by order
        for domain, members in domain_members.items():
            members.sort(key=lambda x: x['order'])
        
        # Map members to their axes
        for axis, axis_data in dimensions['axes'].items():
            domain = axis_data.get('domain')
            if domain and domain in domain_members:
                axis_data['members'] = [
                    m['member'] for m in domain_members[domain]
                ]
    
    def _parse_hypercubes(
        self,
        arcs: List[Dict[str, any]],
        locs: Dict[str, str],
        dimensions: Dict[str, any]
    ):
        """
        Parse hypercube structures.
        
        Hypercubes define which dimensions apply to which concepts.
        
        Args:
            arcs: List of arc dictionaries
            locs: Locator mappings
            dimensions: Dimensions dictionary to populate
        """
        # Find hypercube-dimension relationships
        hypercube_dims = {}
        
        for arc in arcs:
            if arc['arcrole'] == self.HYPERCUBE_DIMENSION:
                hypercube = locs.get(arc['from'], arc['from'])
                dimension = locs.get(arc['to'], arc['to'])
                
                if hypercube not in hypercube_dims:
                    hypercube_dims[hypercube] = []
                
                hypercube_dims[hypercube].append({
                    'dimension': dimension,
                    'order': arc['order']
                })
        
        # Sort dimensions by order
        for hypercube, dims in hypercube_dims.items():
            dims.sort(key=lambda x: x['order'])
        
        # Find primary items (concepts) for each hypercube
        hypercube_items = {}
        
        for arc in arcs:
            if arc['arcrole'] == self.ALL:
                item = locs.get(arc['from'], arc['from'])
                hypercube = locs.get(arc['to'], arc['to'])
                
                if hypercube not in hypercube_items:
                    hypercube_items[hypercube] = []
                
                hypercube_items[hypercube].append(item)
        
        # Build hypercube structures
        for hypercube in set(hypercube_dims.keys()) | set(hypercube_items.keys()):
            dimensions['hypercubes'][hypercube] = {
                'dimensions': [
                    d['dimension'] for d in hypercube_dims.get(hypercube, [])
                ],
                'primary_items': hypercube_items.get(hypercube, [])
            }
    
    def _extract_concept_from_href(self, href: str) -> Optional[str]:
        """
        Extract concept name from href.
        
        Args:
            href: Href string (e.g., "us-gaap-2025.xsd#us-gaap_GeographicAxis")
            
        Returns:
            Concept name (e.g., "us-gaap:GeographicAxis") or None
        """
        if '#' not in href:
            return None
        
        anchor = href.split('#')[1]
        
        # Convert underscore to colon
        if '_' in anchor:
            return anchor.replace('_', ':', 1)
        
        return anchor
    
    def parse_multiple(
        self,
        definition_files: List[Path]
    ) -> Dict[str, any]:
        """
        Parse multiple definition linkbase files.
        
        Args:
            definition_files: List of definition file paths
            
        Returns:
            Combined dictionary of all dimensional relationships
        """
        all_dimensions = {
            'axes': {},
            'hypercubes': {},
        }
        
        for def_file in definition_files:
            try:
                dims = self.parse(def_file)
                
                # Merge axes
                for axis, axis_data in dims.get('axes', {}).items():
                    if axis not in all_dimensions['axes']:
                        all_dimensions['axes'][axis] = axis_data
                    else:
                        # Merge members (avoid duplicates)
                        existing_members = set(all_dimensions['axes'][axis]['members'])
                        new_members = set(axis_data['members'])
                        all_dimensions['axes'][axis]['members'] = list(
                            existing_members | new_members
                        )
                
                # Merge hypercubes
                for hypercube, hypercube_data in dims.get('hypercubes', {}).items():
                    if hypercube not in all_dimensions['hypercubes']:
                        all_dimensions['hypercubes'][hypercube] = hypercube_data
                    else:
                        # Merge dimensions and items
                        existing_dims = set(
                            all_dimensions['hypercubes'][hypercube]['dimensions']
                        )
                        new_dims = set(hypercube_data['dimensions'])
                        all_dimensions['hypercubes'][hypercube]['dimensions'] = list(
                            existing_dims | new_dims
                        )
                        
                        existing_items = set(
                            all_dimensions['hypercubes'][hypercube]['primary_items']
                        )
                        new_items = set(hypercube_data['primary_items'])
                        all_dimensions['hypercubes'][hypercube]['primary_items'] = list(
                            existing_items | new_items
                        )
                
            except FileNotFoundError:
                logger.warning(f"Definition file not found: {def_file}")
                continue
            except Exception as e:
                logger.error(f"Error parsing {def_file}: {e}")
                continue
        
        logger.info(
            f"Parsed {len(all_dimensions['axes'])} axes and "
            f"{len(all_dimensions['hypercubes'])} hypercubes from "
            f"{len(definition_files)} files"
        )
        
        return all_dimensions
    
    def get_statistics(self, dimensions: Dict[str, any]) -> Dict[str, int]:
        """
        Get statistics about parsed dimensions.
        
        Args:
            dimensions: Dictionary of dimensional relationships
            
        Returns:
            Dictionary of statistics
        """
        stats = {
            'total_axes': len(dimensions.get('axes', {})),
            'total_hypercubes': len(dimensions.get('hypercubes', {})),
            'total_members': 0,
            'axes_with_members': 0,
        }
        
        for axis_data in dimensions.get('axes', {}).values():
            members = axis_data.get('members', [])
            stats['total_members'] += len(members)
            if members:
                stats['axes_with_members'] += 1
        
        return stats