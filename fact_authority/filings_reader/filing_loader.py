"""
Filing Loader for XBRL Filing Reader.

Coordinates complete filing loading by orchestrating Phase 1 (discovery)
and Phase 2 (parsing) components.

Market-agnostic: Works with SEC, FCA, ESMA filings.
"""

from pathlib import Path
from typing import Dict, Optional
import logging

from engines.fact_authority.filings_reader.filing_discoverer import FilingDiscoverer
from engines.fact_authority.filings_reader.filing_validator import FilingValidator
from engines.fact_authority.filings_reader.extension_schema_parser import ExtensionSchemaParser
from engines.fact_authority.filings_reader.linkbase_reader import LinkbaseReader
from engines.fact_authority.filings_reader.instance_parser import InstanceParser
from engines.fact_authority.filings_reader.concept_resolver import ConceptResolver


logger = logging.getLogger(__name__)


class FilingLoader:
    """
    Load and parse complete XBRL filing.
    
    Orchestrates:
    1. Phase 1 - File discovery and validation
    2. Phase 2 - Parsing (schema, linkbases, instances)
    3. Concept resolution
    
    Key features:
    - Complete filing loading in one call
    - Validates completeness before parsing
    - Provides structured, parsed data
    - Market-agnostic loading logic
    
    Used by FilingReader to load filings for fact_authority engine.
    """
    
    def __init__(self):
        """Initialize filing loader with all required components."""
        # Phase 1 components
        self.discoverer = FilingDiscoverer()
        self.validator = FilingValidator()
        
        # Phase 2 components
        self.schema_parser = ExtensionSchemaParser()
        self.linkbase_reader = LinkbaseReader()
        self.instance_parser = InstanceParser()
        self.concept_resolver = ConceptResolver()
    
    def load(self, filing_path: Path) -> Dict:
        """
        Load complete XBRL filing.
        
        Args:
            filing_path: Path to filing directory
            
        Returns:
            Dict with complete parsed filing data:
            {
                'filing_path': Path,
                'market': str,
                'discovered_files': Dict,
                'validation': {
                    'all_files_accessible': bool,
                    'schema_valid': bool,
                    'linkbases_complete': bool,
                    'required_files_present': bool,
                    'errors': List[str],
                    'warnings': List[str]
                },
                'extension_schema': Dict (if found),
                'linkbases': Dict,
                'instance': Dict (if found),
                'concept_resolver': ConceptResolver,
                'statistics': Dict
            }
            
        Raises:
            ValueError: If filing path invalid or required files missing
        """
        logger.info(f"Loading filing from: {filing_path}")
        
        if not filing_path or not filing_path.exists():
            raise ValueError(f"Invalid filing path: {filing_path}")
        
        # Phase 1: Discover files
        discovered = self.discoverer.discover(filing_path)
        market = discovered.get('market', 'UNKNOWN')
        
        logger.debug(f"Discovered {discovered.get('total_files', 0)} files, market: {market}")
        
        # Phase 1: Validate completeness
        validation = self.validator.validate(discovered)
        
        # Check validation results (FilingValidator returns multiple status keys)
        is_valid = validation.get('all_files_accessible', True) and \
                   validation.get('required_files_present', True)
        
        if not is_valid:
            logger.warning(f"Filing validation warnings: {validation.get('warnings', [])}")
            # Continue anyway - some filings may be incomplete but still usable
        
        # Phase 2: Parse discovered files
        result = {
            'filing_path': filing_path,
            'market': market,
            'discovered_files': discovered,
            'validation': validation
        }
        
        # Parse extension schema (if found)
        if discovered['extension_schema']:
            schema_path = discovered['extension_schema'][0]
            logger.debug(f"Parsing extension schema: {schema_path.name}")
            try:
                result['extension_schema'] = self.schema_parser.parse(schema_path)
                
                # Load into concept resolver
                self.concept_resolver.load_extension_schema(result['extension_schema'])
                
            except Exception as e:
                logger.error(f"Failed to parse extension schema: {e}")
                result['extension_schema'] = None
        else:
            logger.warning("No extension schema found")
            result['extension_schema'] = None
        
        # Parse linkbases
        result['linkbases'] = self._parse_linkbases(discovered)
        
        # Parse instance document (if found)
        if discovered['instance']:
            instance_path = discovered['instance'][0]
            logger.debug(f"Parsing instance: {instance_path.name}")
            try:
                result['instance'] = self.instance_parser.parse(instance_path)
            except Exception as e:
                logger.error(f"Failed to parse instance: {e}")
                result['instance'] = None
        else:
            logger.warning("No instance document found")
            result['instance'] = None
        
        # Add concept resolver
        result['concept_resolver'] = self.concept_resolver
        
        # Generate statistics
        result['statistics'] = self._generate_statistics(result)
        
        logger.info(f"Loaded filing: {result['statistics']['summary']}")
        
        return result
    
    def _parse_linkbases(self, discovered: Dict) -> Dict:
        """
        Parse all discovered linkbases.
        
        Args:
            discovered: Discovered files from FilingDiscoverer
            
        Returns:
            Dict with parsed linkbase data
        """
        linkbases = {
            'presentation': None,
            'calculation': None,
            'definition': None,
            'label': None
        }
        
        # Parse presentation
        if discovered['presentation']:
            try:
                linkbases['presentation'] = self.linkbase_reader.parse_presentation(
                    discovered['presentation'][0]
                )
            except Exception as e:
                logger.error(f"Failed to parse presentation linkbase: {e}")
        
        # Parse calculation
        if discovered['calculation']:
            try:
                linkbases['calculation'] = self.linkbase_reader.parse_calculation(
                    discovered['calculation'][0]
                )
            except Exception as e:
                logger.error(f"Failed to parse calculation linkbase: {e}")
        
        # Parse definition
        if discovered['definition']:
            try:
                linkbases['definition'] = self.linkbase_reader.parse_definition(
                    discovered['definition'][0]
                )
            except Exception as e:
                logger.error(f"Failed to parse definition linkbase: {e}")
        
        # Parse label
        if discovered['label']:
            try:
                linkbases['label'] = self.linkbase_reader.parse_label(
                    discovered['label'][0]
                )
            except Exception as e:
                logger.error(f"Failed to parse label linkbase: {e}")
        
        return linkbases
    
    def _generate_statistics(self, result: Dict) -> Dict:
        """
        Generate loading statistics.
        
        Args:
            result: Complete loading result
            
        Returns:
            Dict with statistics
        """
        stats = {
            'market': result['market'],
            'filing_path': str(result['filing_path']),
            'validation_passed': result['validation'].get('all_files_accessible', True) and 
                                result['validation'].get('required_files_present', True),
            'files_discovered': result['discovered_files'].get('total_files', 0),
            'has_extension_schema': result['extension_schema'] is not None,
            'has_instance': result['instance'] is not None,
            'linkbases_parsed': sum(1 for v in result['linkbases'].values() if v is not None)
        }
        
        # Extension schema stats
        if result['extension_schema']:
            stats['extension_elements'] = result['extension_schema'].get('element_count', 0)
            stats['extension_namespace'] = result['extension_schema'].get('namespace')
        else:
            stats['extension_elements'] = 0
            stats['extension_namespace'] = None
        
        # Instance stats
        if result['instance']:
            stats['fact_count'] = result['instance'].get('fact_count', 0)
            stats['context_count'] = result['instance'].get('context_count', 0)
            stats['instance_format'] = result['instance'].get('format')
        else:
            stats['fact_count'] = 0
            stats['context_count'] = 0
            stats['instance_format'] = None
        
        # Linkbase stats
        if result['linkbases']['presentation']:
            stats['presentation_roles'] = len(result['linkbases']['presentation'].get('roles', {}))
        else:
            stats['presentation_roles'] = 0
        
        # Summary message
        summary_parts = []
        if stats['has_extension_schema']:
            summary_parts.append(f"{stats['extension_elements']} elements")
        if stats['has_instance']:
            summary_parts.append(f"{stats['fact_count']} facts")
        summary_parts.append(f"{stats['linkbases_parsed']} linkbases")
        
        stats['summary'] = ', '.join(summary_parts)
        
        return stats
    
    def get_concept_resolver(self) -> ConceptResolver:
        """
        Get the concept resolver instance.
        
        Returns:
            ConceptResolver instance
        """
        return self.concept_resolver