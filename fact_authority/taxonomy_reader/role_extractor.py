"""
Role Extractor
==============

Extracts roleType definitions from XBRL schema files.

Roles define statement types (balance sheet, income statement, etc.)
and are critical for understanding where concepts belong.

Classes:
    RoleExtractor: Extracts roleType definitions from XSD files
"""

from pathlib import Path
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET


class RoleExtractor:
    """
    Extracts roleType definitions from XBRL schema files.
    
    Role types define the purpose of presentation links, typically
    corresponding to financial statement types.
    
    Example roleType in schema:
        <link:roleType roleURI="http://fasb.org/.../StatementOfFinancialPosition">
          <link:definition>Statement of Financial Position</link:definition>
          <link:usedOn>link:presentationLink</link:usedOn>
        </link:roleType>
    """
    
    # Standard XML namespaces
    NAMESPACES = {
        'xsd': 'http://www.w3.org/2001/XMLSchema',
        'link': 'http://www.xbrl.org/2003/linkbase',
        'xlink': 'http://www.w3.org/1999/xlink',
    }
    
    # Statement type keywords for classification
    STATEMENT_KEYWORDS = {
        'balance': 'balance_sheet',
        'financial position': 'balance_sheet',
        'statement of financial position': 'balance_sheet',
        'income': 'income_statement',
        'operations': 'income_statement',
        'statement of income': 'income_statement',
        'comprehensive income': 'comprehensive_income',
        'cash flow': 'cash_flow',
        'statement of cash flows': 'cash_flow',
        'equity': 'equity',
        'stockholders equity': 'equity',
        'shareholders equity': 'equity',
        'changes in equity': 'equity',
    }
    
    def __init__(self):
        """Initialize role extractor."""
        pass
    
    def extract_from_file(self, schema_path: Path) -> Dict[str, Dict[str, any]]:
        """
        Extract all roleType definitions from a schema file.
        
        Args:
            schema_path: Path to .xsd schema file
            
        Returns:
            Dictionary mapping role URIs to role information:
            {
                'http://fasb.org/.../StatementOfFinancialPosition': {
                    'type': 'balance_sheet',
                    'definition': 'Statement of Financial Position',
                    'used_on': ['presentationLink'],
                    'source_schema': 'us-gaap-2025.xsd'
                }
            }
            
        Raises:
            FileNotFoundError: If schema file doesn't exist
        """
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        roles = {}
        
        try:
            tree = ET.parse(schema_path)
            root = tree.getroot()
            
            # Find all roleType elements
            for role_elem in root.findall('.//link:roleType', self.NAMESPACES):
                role_uri = role_elem.get('roleURI')
                
                if role_uri:
                    role_info = self._extract_role_info(role_elem, schema_path)
                    roles[role_uri] = role_info
            
        except ET.ParseError:
            # If parsing fails, return empty (non-fatal)
            return {}
        
        return roles
    
    def _extract_role_info(
        self,
        role_elem: ET.Element,
        schema_path: Path
    ) -> Dict[str, any]:
        """
        Extract information from a roleType element.
        
        Args:
            role_elem: roleType XML element
            schema_path: Source schema file path
            
        Returns:
            Dictionary with role information
        """
        # Extract definition
        definition_elem = role_elem.find('link:definition', self.NAMESPACES)
        definition = definition_elem.text.strip() if definition_elem is not None else ''
        
        # Extract usedOn elements
        used_on = []
        for used_elem in role_elem.findall('link:usedOn', self.NAMESPACES):
            if used_elem.text:
                used_on.append(used_elem.text.strip())
        
        # Classify statement type
        statement_type = self._classify_statement_type(definition)
        
        return {
            'type': statement_type,
            'definition': definition,
            'used_on': used_on,
            'source_schema': schema_path.name
        }
    
    def _classify_statement_type(self, definition: str) -> str:
        """
        Classify a role definition into a statement type.
        
        Uses keyword matching to determine statement type from
        the role definition text.
        
        Args:
            definition: Role definition text
            
        Returns:
            Statement type (e.g., 'balance_sheet', 'income_statement')
            or 'other' if cannot classify
        """
        if not definition:
            return 'other'
        
        definition_lower = definition.lower()
        
        # Check keywords (ordered by specificity)
        for keyword, stmt_type in self.STATEMENT_KEYWORDS.items():
            if keyword in definition_lower:
                return stmt_type
        
        return 'other'
    
    def extract_from_multiple_files(
        self,
        schema_paths: List[Path]
    ) -> Dict[str, Dict[str, any]]:
        """
        Extract roleType definitions from multiple schema files.
        
        Args:
            schema_paths: List of schema file paths
            
        Returns:
            Combined dictionary of all roles found
        """
        all_roles = {}
        
        for schema_path in schema_paths:
            try:
                roles = self.extract_from_file(schema_path)
                all_roles.update(roles)
            except FileNotFoundError:
                # Skip missing files
                continue
        
        return all_roles
    
    def filter_presentation_roles(
        self,
        roles: Dict[str, Dict[str, any]]
    ) -> Dict[str, Dict[str, any]]:
        """
        Filter roles to only those used for presentation.
        
        Args:
            roles: Dictionary of all roles
            
        Returns:
            Dictionary containing only presentation roles
        """
        return {
            uri: info
            for uri, info in roles.items()
            if 'presentationLink' in info.get('used_on', [])
        }
    
    def get_statement_roles(
        self,
        roles: Dict[str, Dict[str, any]]
    ) -> Dict[str, str]:
        """
        Get simplified mapping of role URIs to statement types.
        
        Args:
            roles: Dictionary of all roles
            
        Returns:
            Dictionary mapping role URI to statement type
        """
        return {
            uri: info['type']
            for uri, info in roles.items()
            if info.get('type') != 'other'
        }
    
    def get_roles_by_type(
        self,
        roles: Dict[str, Dict[str, any]],
        statement_type: str
    ) -> List[str]:
        """
        Get all role URIs for a specific statement type.
        
        Args:
            roles: Dictionary of all roles
            statement_type: Statement type to filter by
            
        Returns:
            List of role URIs matching the statement type
        """
        return [
            uri
            for uri, info in roles.items()
            if info.get('type') == statement_type
        ]