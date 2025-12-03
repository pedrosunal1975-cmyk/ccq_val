# File: engines/fact_authority/process/extension_inheritance_tracer.py
# Path: engines/fact_authority/process/extension_inheritance_tracer.py

"""
Extension Inheritance Tracer
=============================

Traces company extension concept inheritance to base taxonomy.

Uses filings_reader to parse extension schema and map extension
concepts to their base taxonomy parents through substitutionGroup.

Responsibilities:
    - Parse company extension schema
    - Extract substitutionGroup attributes
    - Map extension concepts to base concepts
    - Validate extension inheritance
    - Provide concept definitions

Does NOT:
    - Parse base taxonomy (taxonomy_reader does that)
    - Make validation decisions (reconciler does that)
    - Write output (output_writer does that)
"""

from typing import Dict, Any, Set, Optional
from pathlib import Path

from core.system_logger import get_logger
from core.data_paths import CCQPaths

logger = get_logger(__name__)


class ExtensionInheritanceTracer:
    """
    Traces extension concept inheritance using filings_reader.
    
    Analyzes company extension schemas to understand how custom
    concepts relate to standard taxonomy concepts.
    """
    
    def __init__(self, ccq_paths: CCQPaths):
        """
        Initialize tracer with CCQPaths.
        
        Args:
            ccq_paths: CCQPaths instance for path resolution
        """
        self.logger = logger
        self.ccq_paths = ccq_paths
    
    def trace_extensions(
        self,
        filing_data: Dict[str, Any],
        taxonomy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Trace extension concept inheritance.
        
        Args:
            filing_data: Filing data from filings_reader
            taxonomy_data: Taxonomy data from taxonomy_reader
            
        Returns:
            {
                'extension_concepts': {...},
                'inheritance_map': {...},
                'validation_results': {...}
            }
        """
        self.logger.info("Tracing extension concept inheritance")
        
        # Extract extension concepts from filing
        extension_concepts = self._extract_extension_concepts(filing_data)
        
        # Build inheritance map
        inheritance_map = self._build_inheritance_map(
            extension_concepts,
            taxonomy_data
        )
        
        # Validate inheritance
        validation_results = self._validate_inheritance(
            inheritance_map,
            taxonomy_data
        )
        
        return {
            'extension_concepts': extension_concepts,
            'inheritance_map': inheritance_map,
            'validation_results': validation_results,
            'statistics': {
                'total_extensions': len(extension_concepts),
                'mapped_to_base': len(inheritance_map),
                'valid_inheritance': validation_results['valid_count'],
                'invalid_inheritance': validation_results['invalid_count']
            }
        }
    
    def _extract_extension_concepts(
        self,
        filing_data: Dict[str, Any]
    ) -> Dict[str, Dict]:
        """
        Extract extension concepts from filing data.
        
        ROBUST EXTRACTION - Handles multiple data formats:
        1. ExtensionSchemaParser format: 'elements' as list
        2. Legacy format: 'concepts' as dict
        3. Future formats: attempts intelligent extraction
        
        Market agnostic - works with any company's extension structure.
        
        Args:
            filing_data: Filing data with extension schema
            
        Returns:
            Dict mapping extension concept to its properties
        """
        extension_concepts = {}
        
        # Get extension schema from filing data
        extension_schema = filing_data.get('extension_schema', {})
        
        if not extension_schema:
            self.logger.warning("No extension schema found in filing data")
            return extension_concepts
        
        # METHOD 1: Try 'concepts' dict format (legacy/alternative format)
        if 'concepts' in extension_schema:
            concepts_dict = extension_schema.get('concepts', {})
            for concept_qname, concept_data in concepts_dict.items():
                if self._is_extension_concept(concept_qname):
                    # Handle both naming conventions
                    substitution_group = (
                        concept_data.get('substitutionGroup') or
                        concept_data.get('substitution_group')
                    )
                    period_type = (
                        concept_data.get('periodType') or
                        concept_data.get('period_type')
                    )
                    
                    extension_concepts[concept_qname] = {
                        'type': concept_data.get('type'),
                        'substitutionGroup': substitution_group,
                        'periodType': period_type,
                        'balance': concept_data.get('balance'),
                        'abstract': concept_data.get('abstract', False),
                        'nillable': concept_data.get('nillable', True)
                    }
            
            if extension_concepts:
                self.logger.info(
                    f"Extracted {len(extension_concepts)} extension concepts "
                    f"from 'concepts' dict format"
                )
                return extension_concepts
        
        # METHOD 2: Try 'elements' list format (ExtensionSchemaParser format)
        if 'elements' in extension_schema:
            elements = extension_schema.get('elements', [])
            namespace_prefix = extension_schema.get('namespace_prefix', '')
            
            for element_data in elements:
                # Build qualified name
                name = element_data.get('name', '')
                if not name:
                    continue
                
                concept_qname = f"{namespace_prefix}:{name}" if namespace_prefix else name
                
                # Only include extension concepts (not standard taxonomy)
                if self._is_extension_concept(concept_qname):
                    # Handle both snake_case and camelCase naming conventions
                    # (different parsers may use different conventions)
                    substitution_group = (
                        element_data.get('substitutionGroup') or  # camelCase
                        element_data.get('substitution_group')     # snake_case
                    )
                    period_type = (
                        element_data.get('periodType') or         # camelCase
                        element_data.get('period_type')           # snake_case
                    )
                    
                    extension_concepts[concept_qname] = {
                        'type': element_data.get('type'),
                        'substitutionGroup': substitution_group,
                        'periodType': period_type,
                        'balance': element_data.get('balance'),
                        'abstract': element_data.get('abstract', False),
                        'nillable': element_data.get('nillable', True)
                    }
            
            if extension_concepts:
                self.logger.info(
                    f"Extracted {len(extension_concepts)} extension concepts "
                    f"from 'elements' list format"
                )
                return extension_concepts
        
        # No recognized format found
        self.logger.warning(
            f"Extension schema found but no recognizable format. "
            f"Available keys: {list(extension_schema.keys())}"
        )
        
        return extension_concepts
    
    def _build_inheritance_map(
        self,
        extension_concepts: Dict[str, Dict],
        taxonomy_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Build inheritance map from extensions to base concepts.
        
        Args:
            extension_concepts: Extension concepts with properties
            taxonomy_data: Base taxonomy data
            
        Returns:
            Dict mapping extension_concept to base_concept
        """
        inheritance_map = {}
        
        for ext_concept, ext_props in extension_concepts.items():
            substitution_group = ext_props.get('substitutionGroup')
            
            if not substitution_group:
                # No inheritance specified
                continue
            
            # substitutionGroup points to base concept
            # Format: namespace:ConceptName
            base_concept = self._resolve_substitution_group(
                substitution_group,
                taxonomy_data
            )
            
            if base_concept:
                inheritance_map[ext_concept] = base_concept
        
        self.logger.info(
            f"Built inheritance map with {len(inheritance_map)} mappings"
        )
        
        return inheritance_map
    
    def _validate_inheritance(
        self,
        inheritance_map: Dict[str, str],
        taxonomy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate extension inheritance against taxonomy.
        
        Args:
            inheritance_map: Extension to base concept mappings
            taxonomy_data: Base taxonomy data
            
        Returns:
            Validation results dict
        """
        valid_mappings = []
        invalid_mappings = []
        
        # Get base concepts from taxonomy
        base_concepts = self._get_base_concepts(taxonomy_data)
        
        for ext_concept, base_concept in inheritance_map.items():
            if base_concept in base_concepts:
                valid_mappings.append({
                    'extension_concept': ext_concept,
                    'base_concept': base_concept,
                    'status': 'valid'
                })
            else:
                invalid_mappings.append({
                    'extension_concept': ext_concept,
                    'base_concept': base_concept,
                    'status': 'invalid',
                    'reason': 'Base concept not found in taxonomy'
                })
        
        return {
            'valid_mappings': valid_mappings,
            'invalid_mappings': invalid_mappings,
            'valid_count': len(valid_mappings),
            'invalid_count': len(invalid_mappings)
        }
    
    def _is_extension_concept(self, concept_qname: str) -> bool:
        """
        Check if concept is an extension (not standard taxonomy).
        
        Args:
            concept_qname: Concept qualified name
            
        Returns:
            True if extension concept, False if standard
        """
        if not concept_qname or ':' not in concept_qname:
            return False
        
        namespace = concept_qname.split(':')[0]
        
        # Standard taxonomy namespaces
        standard_namespaces = [
            'us-gaap',
            'ifrs-full',
            'ifrs',
            'dei',
            'srt',
            'country',
            'currency',
            'exch',
            'stpr',
            'naics',
            'sic',
            'uk-gaap',
            'esef'
        ]
        
        # Remove year suffix for comparison
        base_namespace = namespace.split('-')[0] if '-' in namespace else namespace
        
        return base_namespace not in [ns.split('-')[0] for ns in standard_namespaces]
    
    def _resolve_substitution_group(
        self,
        substitution_group: str,
        taxonomy_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Resolve substitutionGroup to actual base concept.
        
        Args:
            substitution_group: substitutionGroup attribute value
            taxonomy_data: Taxonomy data
            
        Returns:
            Base concept qname or None
        """
        # substitutionGroup typically is the qname itself
        # Just return it for now
        # TODO: May need more sophisticated resolution if format is different
        
        return substitution_group
    
    def _get_base_concepts(self, taxonomy_data: Dict[str, Any]) -> Set[str]:
        """
        Get set of base concepts from taxonomy.
        
        Extracts concepts from TaxonomyProfile's elements dictionary.
        Market agnostic - works with any taxonomy structure.
        
        Args:
            taxonomy_data: Taxonomy data (TaxonomyProfile object or dict)
            
        Returns:
            Set of base concept qnames
        """
        base_concepts = set()
        
        # Handle both TaxonomyProfile object and dict
        if hasattr(taxonomy_data, 'to_dict'):
            # TaxonomyProfile object - convert to dict
            taxonomy_dict = taxonomy_data.to_dict()
        elif isinstance(taxonomy_data, dict):
            # Already a dict
            taxonomy_dict = taxonomy_data
        else:
            self.logger.warning(
                f"Unexpected taxonomy_data type: {type(taxonomy_data)} - "
                "extension validation may be limited"
            )
            return base_concepts
        
        # Extract from TaxonomyProfile elements
        elements = taxonomy_dict.get('elements', {})
        
        if not elements:
            self.logger.warning(
                "No elements found in taxonomy data - "
                "extension validation may be limited"
            )
            return base_concepts
        
        # All element keys are concept qnames
        base_concepts = set(elements.keys())
        
        self.logger.info(
            f"Extracted {len(base_concepts)} base concepts from taxonomy"
        )
        
        return base_concepts


__all__ = ['ExtensionInheritanceTracer']