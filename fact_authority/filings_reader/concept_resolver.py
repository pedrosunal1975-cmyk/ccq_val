"""
Concept Resolver for XBRL Filing Reader.

Resolves concept references between extension and standard taxonomies,
enabling fact_authority to trace concepts across taxonomy boundaries.

Market-agnostic: Works with SEC, FCA, ESMA taxonomies.
"""

from pathlib import Path
from typing import Dict, List, Set, Optional
import logging


logger = logging.getLogger(__name__)


class ConceptResolver:
    """
    Resolve concept references across extension and standard taxonomies.
    
    Key features:
    - Maps extension concepts to their base taxonomy equivalents
    - Identifies concept relationships (substitution groups)
    - Resolves namespaces between taxonomies
    - Market-agnostic resolution logic
    
    Used by fact_authority engine to understand how company-specific
    concepts relate to standard taxonomy concepts.
    """
    
    def __init__(self):
        """Initialize concept resolver."""
        self.extension_namespace = None
        self.extension_elements = {}
        self.standard_imports = []
        self.concept_map = {}
        
    def load_extension_schema(self, parsed_schema: Dict) -> None:
        """
        Load extension schema data for resolution.
        
        Args:
            parsed_schema: Parsed extension schema from ExtensionSchemaParser
        """
        logger.debug(f"Loading extension schema with {parsed_schema.get('element_count', 0)} elements")
        
        self.extension_namespace = parsed_schema.get('namespace')
        self.extension_elements = {
            elem['name']: elem 
            for elem in parsed_schema.get('elements', [])
        }
        self.standard_imports = parsed_schema.get('imports', [])
        
        # Build concept map
        self._build_concept_map()
        
        logger.info(f"Loaded {len(self.extension_elements)} extension concepts")
    
    def _build_concept_map(self) -> None:
        """
        Build mapping between extension concepts and standard taxonomy.
        
        Maps extension elements to their substitution groups, which indicate
        the standard taxonomy concept they're based on.
        """
        self.concept_map = {}
        
        for name, element in self.extension_elements.items():
            substitution_group = element.get('substitution_group')
            if substitution_group:
                # Extract base concept from substitution group
                # Format: namespace:ConceptName
                if ':' in substitution_group:
                    namespace_prefix, base_concept = substitution_group.split(':', 1)
                    self.concept_map[name] = {
                        'base_concept': base_concept,
                        'namespace_prefix': namespace_prefix,
                        'element_type': element.get('type'),
                        'period_type': element.get('period_type'),
                        'balance': element.get('balance')
                    }
                    
        logger.debug(f"Built concept map with {len(self.concept_map)} mappings")
    
    def resolve_concept(self, concept_name: str) -> Optional[Dict]:
        """
        Resolve a concept to its base taxonomy information.
        
        Args:
            concept_name: Name of concept to resolve
            
        Returns:
            Dict with resolution info, or None if not resolvable
        """
        # Check if it's an extension concept
        if concept_name in self.concept_map:
            return self.concept_map[concept_name]
        
        # Not an extension concept
        return None
    
    def is_extension_concept(self, concept_name: str) -> bool:
        """
        Check if concept is from extension taxonomy.
        
        Args:
            concept_name: Name of concept
            
        Returns:
            True if extension concept, False otherwise
        """
        return concept_name in self.extension_elements
    
    def get_concept_type(self, concept_name: str) -> Optional[str]:
        """
        Get the type of a concept.
        
        Args:
            concept_name: Name of concept
            
        Returns:
            Concept type (e.g., 'xbrli:monetaryItemType'), or None
        """
        if concept_name in self.extension_elements:
            return self.extension_elements[concept_name].get('type')
        return None
    
    def get_concept_properties(self, concept_name: str) -> Dict:
        """
        Get all properties of a concept.
        
        Args:
            concept_name: Name of concept
            
        Returns:
            Dict with concept properties
        """
        if concept_name in self.extension_elements:
            element = self.extension_elements[concept_name]
            return {
                'name': concept_name,
                'type': element.get('type'),
                'substitution_group': element.get('substitution_group'),
                'period_type': element.get('period_type'),
                'balance': element.get('balance'),
                'abstract': element.get('abstract', False),
                'nillable': element.get('nillable', True)
            }
        return {}
    
    def get_monetary_concepts(self) -> Set[str]:
        """
        Get all monetary concepts from extension.
        
        Returns:
            Set of monetary concept names
        """
        monetary = set()
        for name, element in self.extension_elements.items():
            element_type = element.get('type', '')
            if 'monetary' in element_type.lower():
                monetary.add(name)
        return monetary
    
    def get_abstract_concepts(self) -> Set[str]:
        """
        Get all abstract concepts from extension.
        
        Returns:
            Set of abstract concept names
        """
        abstract = set()
        for name, element in self.extension_elements.items():
            if element.get('abstract', False):
                abstract.add(name)
        return abstract
    
    def get_concepts_by_period_type(self, period_type: str) -> Set[str]:
        """
        Get concepts filtered by period type.
        
        Args:
            period_type: 'instant' or 'duration'
            
        Returns:
            Set of concept names
        """
        concepts = set()
        for name, element in self.extension_elements.items():
            if element.get('period_type') == period_type:
                concepts.add(name)
        return concepts
    
    def get_concepts_by_balance(self, balance: str) -> Set[str]:
        """
        Get concepts filtered by balance type.
        
        Args:
            balance: 'debit' or 'credit'
            
        Returns:
            Set of concept names
        """
        concepts = set()
        for name, element in self.extension_elements.items():
            if element.get('balance') == balance:
                concepts.add(name)
        return concepts
    
    def get_standard_imports(self) -> List[Dict]:
        """
        Get list of standard taxonomy imports.
        
        Returns:
            List of import dicts with namespace and schema_location
        """
        return self.standard_imports
    
    def get_extension_namespace(self) -> Optional[str]:
        """
        Get extension taxonomy namespace.
        
        Returns:
            Extension namespace URI
        """
        return self.extension_namespace
    
    def get_extension_concepts(self) -> Set[str]:
        """
        Get all extension concept names.
        
        Returns:
            Set of extension concept names
        """
        return set(self.extension_elements.keys())
    
    def get_concept_count(self) -> int:
        """
        Get total number of extension concepts.
        
        Returns:
            Count of extension concepts
        """
        return len(self.extension_elements)
    
    def get_statistics(self) -> Dict:
        """
        Get resolution statistics.
        
        Returns:
            Dict with statistics
        """
        return {
            'total_concepts': len(self.extension_elements),
            'mapped_concepts': len(self.concept_map),
            'monetary_concepts': len(self.get_monetary_concepts()),
            'abstract_concepts': len(self.get_abstract_concepts()),
            'instant_concepts': len(self.get_concepts_by_period_type('instant')),
            'duration_concepts': len(self.get_concepts_by_period_type('duration')),
            'standard_imports': len(self.standard_imports),
            'extension_namespace': self.extension_namespace
        }