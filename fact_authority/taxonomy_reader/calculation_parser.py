"""
Calculation Linkbase Parser
============================

Parses XBRL calculation linkbases to extract mathematical relationships.

Calculation linkbases define summation rules like:
- Assets = AssetsCurrent + AssetsNoncurrent
- NetIncome = Revenues - Expenses

This enables validation of accounting equations and statement math.

Classes:
    CalculationParser: Parses calculation linkbase files
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET
import logging


logger = logging.getLogger(__name__)


class CalculationParser:
    """
    Parses XBRL calculation linkbase files.
    
    Extracts calculation relationships that define how concepts sum together.
    These relationships are organized by role (typically statement type).
    
    Example calculation in linkbase:
        <calculationLink xlink:role="http://fasb.org/.../BalanceSheet">
          <calculationArc xlink:from="Assets" xlink:to="AssetsCurrent"
                          order="1.0" weight="1.0"/>
          <calculationArc xlink:from="Assets" xlink:to="AssetsNoncurrent"
                          order="2.0" weight="1.0"/>
        </calculationLink>
        
        Meaning: Assets = AssetsCurrent + AssetsNoncurrent
    """
    
    # Standard XML namespaces
    NAMESPACES = {
        'link': 'http://www.xbrl.org/2003/linkbase',
        'xlink': 'http://www.w3.org/1999/xlink',
        'xbrli': 'http://www.xbrl.org/2003/instance',
    }
    
    def __init__(self):
        """Initialize calculation parser."""
        pass
    
    def parse(self, calculation_file: Path) -> Dict[str, Dict[str, any]]:
        """
        Parse a calculation linkbase file.
        
        Args:
            calculation_file: Path to *_cal.xml file
            
        Returns:
            Dictionary organized by role, then by parent concept:
            {
                'http://fasb.org/.../BalanceSheet': {
                    'us-gaap:Assets': {
                        'role': 'http://fasb.org/.../BalanceSheet',
                        'children': [
                            {
                                'concept': 'us-gaap:AssetsCurrent',
                                'weight': 1.0,
                                'order': 1.0
                            },
                            {
                                'concept': 'us-gaap:AssetsNoncurrent',
                                'weight': 1.0,
                                'order': 2.0
                            }
                        ]
                    }
                }
            }
            
        Raises:
            FileNotFoundError: If calculation file doesn't exist
        """
        if not calculation_file.exists():
            raise FileNotFoundError(f"Calculation file not found: {calculation_file}")
        
        calculations = {}
        
        try:
            tree = ET.parse(calculation_file)
            root = tree.getroot()
            
            # Find all calculationLink elements
            for calc_link in root.findall('.//link:calculationLink', self.NAMESPACES):
                role = calc_link.get('{http://www.w3.org/1999/xlink}role', '')
                
                if role:
                    # Parse this calculation link
                    role_calcs = self._parse_calculation_link(calc_link)
                    
                    if role_calcs:
                        calculations[role] = role_calcs
            
            logger.debug(
                f"Parsed {len(calculations)} calculation roles from {calculation_file.name}"
            )
            
        except ET.ParseError as e:
            logger.warning(f"Failed to parse calculation file {calculation_file}: {e}")
            return {}
        
        return calculations
    
    def _parse_calculation_link(
        self,
        calc_link: ET.Element
    ) -> Dict[str, Dict[str, any]]:
        """
        Parse a single calculationLink element.
        
        Args:
            calc_link: calculationLink XML element
            
        Returns:
            Dictionary mapping parent concepts to their calculation rules
        """
        role_calcs = {}
        
        # First, collect all locs (concept locators)
        locs = self._collect_locators(calc_link)
        
        # Then, collect all arcs (relationships)
        arcs = self._collect_arcs(calc_link)
        
        # Build parent-child relationships
        for arc in arcs:
            from_label = arc['from']
            to_label = arc['to']
            weight = arc['weight']
            order = arc['order']
            
            # Resolve labels to concept names
            parent_concept = locs.get(from_label, from_label)
            child_concept = locs.get(to_label, to_label)
            
            # Add to parent's children
            if parent_concept not in role_calcs:
                role_calcs[parent_concept] = {
                    'children': []
                }
            
            role_calcs[parent_concept]['children'].append({
                'concept': child_concept,
                'weight': weight,
                'order': order
            })
        
        # Sort children by order
        for parent_data in role_calcs.values():
            parent_data['children'].sort(key=lambda x: x['order'])
        
        return role_calcs
    
    def _collect_locators(self, calc_link: ET.Element) -> Dict[str, str]:
        """
        Collect all loc elements (concept locators).
        
        Locators map labels to concept hrefs.
        
        Args:
            calc_link: calculationLink XML element
            
        Returns:
            Dictionary mapping labels to concept names
        """
        locs = {}
        
        for loc in calc_link.findall('.//link:loc', self.NAMESPACES):
            label = loc.get('{http://www.w3.org/1999/xlink}label', '')
            href = loc.get('{http://www.w3.org/1999/xlink}href', '')
            
            if label and href:
                # Extract concept name from href
                # Example href: "us-gaap-2025.xsd#us-gaap_Assets"
                concept = self._extract_concept_from_href(href)
                if concept:
                    locs[label] = concept
        
        return locs
    
    def _collect_arcs(self, calc_link: ET.Element) -> List[Dict[str, any]]:
        """
        Collect all calculationArc elements (relationships).
        
        Args:
            calc_link: calculationLink XML element
            
        Returns:
            List of arc dictionaries
        """
        arcs = []
        
        for arc in calc_link.findall('.//link:calculationArc', self.NAMESPACES):
            from_label = arc.get('{http://www.w3.org/1999/xlink}from', '')
            to_label = arc.get('{http://www.w3.org/1999/xlink}to', '')
            order = arc.get('order', '1.0')
            weight = arc.get('weight', '1.0')
            
            if from_label and to_label:
                arcs.append({
                    'from': from_label,
                    'to': to_label,
                    'weight': float(weight),
                    'order': float(order)
                })
        
        return arcs
    
    def _extract_concept_from_href(self, href: str) -> Optional[str]:
        """
        Extract concept name from href.
        
        Args:
            href: Href string (e.g., "us-gaap-2025.xsd#us-gaap_Assets")
            
        Returns:
            Concept name (e.g., "us-gaap:Assets") or None
        """
        if '#' not in href:
            return None
        
        # Split on '#' and take the anchor part
        anchor = href.split('#')[1]
        
        # Convert underscore to colon
        # "us-gaap_Assets" -> "us-gaap:Assets"
        if '_' in anchor:
            return anchor.replace('_', ':', 1)
        
        return anchor
    
    def parse_multiple(
        self,
        calculation_files: List[Path]
    ) -> Dict[str, Dict[str, Dict[str, any]]]:
        """
        Parse multiple calculation linkbase files.
        
        Args:
            calculation_files: List of calculation file paths
            
        Returns:
            Combined dictionary of all calculation relationships
        """
        all_calculations = {}
        
        for calc_file in calculation_files:
            try:
                calcs = self.parse(calc_file)
                
                # Merge into all_calculations
                for role, role_calcs in calcs.items():
                    if role not in all_calculations:
                        all_calculations[role] = {}
                    
                    # Merge parent concepts
                    for parent, parent_data in role_calcs.items():
                        if parent not in all_calculations[role]:
                            all_calculations[role][parent] = parent_data
                        else:
                            # Merge children (avoid duplicates)
                            existing_children = {
                                c['concept']: c
                                for c in all_calculations[role][parent]['children']
                            }
                            
                            for child in parent_data['children']:
                                existing_children[child['concept']] = child
                            
                            all_calculations[role][parent]['children'] = list(
                                existing_children.values()
                            )
                            
                            # Re-sort by order
                            all_calculations[role][parent]['children'].sort(
                                key=lambda x: x['order']
                            )
                
            except FileNotFoundError:
                logger.warning(f"Calculation file not found: {calc_file}")
                continue
            except Exception as e:
                logger.error(f"Error parsing {calc_file}: {e}")
                continue
        
        logger.info(
            f"Parsed {len(all_calculations)} calculation roles from "
            f"{len(calculation_files)} files"
        )
        
        return all_calculations
    
    def get_calculation_formula(
        self,
        parent: str,
        children: List[Dict[str, any]]
    ) -> str:
        """
        Generate human-readable calculation formula.
        
        Args:
            parent: Parent concept
            children: List of child dictionaries with concept and weight
            
        Returns:
            Formula string (e.g., "Assets = AssetsCurrent + AssetsNoncurrent")
        """
        if not children:
            return f"{parent} = ?"
        
        terms = []
        for child in children:
            concept = child['concept']
            weight = child['weight']
            
            # Simplify concept name (remove namespace)
            if ':' in concept:
                simple_name = concept.split(':')[1]
            else:
                simple_name = concept
            
            # Add sign
            if weight >= 0:
                terms.append(f"+ {simple_name}")
            else:
                terms.append(f"- {simple_name}")
        
        # Join terms
        formula_parts = ' '.join(terms)
        
        # Remove leading '+' if present
        if formula_parts.startswith('+ '):
            formula_parts = formula_parts[2:]
        
        # Simplify parent name
        if ':' in parent:
            simple_parent = parent.split(':')[1]
        else:
            simple_parent = parent
        
        return f"{simple_parent} = {formula_parts}"
    
    def validate_calculation(
        self,
        parent_value: float,
        children_values: List[Tuple[float, float]],
        tolerance: float = 0.01
    ) -> Tuple[bool, float]:
        """
        Validate a calculation relationship.
        
        Args:
            parent_value: Parent concept value
            children_values: List of (value, weight) tuples for children
            tolerance: Acceptable difference (default 0.01 for rounding)
            
        Returns:
            Tuple of (is_valid, difference)
        """
        # Calculate expected parent value
        expected = sum(value * weight for value, weight in children_values)
        
        # Check if within tolerance
        difference = abs(parent_value - expected)
        is_valid = difference <= tolerance
        
        return is_valid, difference
    
    def get_statistics(
        self,
        calculations: Dict[str, Dict[str, Dict[str, any]]]
    ) -> Dict[str, int]:
        """
        Get statistics about parsed calculations.
        
        Args:
            calculations: Dictionary of calculation relationships
            
        Returns:
            Dictionary of statistics
        """
        stats = {
            'total_roles': len(calculations),
            'total_parent_concepts': 0,
            'total_relationships': 0,
            'additive_relationships': 0,
            'subtractive_relationships': 0,
        }
        
        for role_calcs in calculations.values():
            stats['total_parent_concepts'] += len(role_calcs)
            
            for parent_data in role_calcs.values():
                children = parent_data.get('children', [])
                stats['total_relationships'] += len(children)
                
                for child in children:
                    if child['weight'] > 0:
                        stats['additive_relationships'] += 1
                    else:
                        stats['subtractive_relationships'] += 1
        
        return stats