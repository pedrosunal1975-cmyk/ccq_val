"""
Parsed Facts Loader for Fact Authority Engine.

UNIVERSAL LOADER - Works across ALL markets (SEC, FCA, ESMA) and supports
multiple field name conventions through intelligent fallback patterns.

Loads facts.json files from Map Pro using existing CCQPaths infrastructure.
Based on the proven parsed_facts_loader.py implementation.

FIELD NAME SUPPORT (Fallback Pattern):
- Concept: 'concept_qname' OR 'qname' OR 'concept' OR 'concept_local_name'
- Value: 'fact_value' OR 'value'
- Context: 'context_ref' OR 'contextRef' OR 'context'
- Unit: 'unit_ref' OR 'unit'

This makes the loader work with facts.json from ANY source:
- filings_reader output (uses concept_qname, fact_value, context_ref)
- Legacy formats (uses qname, value, contextRef)
- Database exports (uses concept, value, context)

Actual Map Pro facts.json structure (from filings_reader output):
{
    'facts': [...],
    'contexts': [...],
    'units': [...],
    'metadata': {
        'filing_id': ...,
        'company': ...,
        'cik': ...,
        'filing_type': ...,
        'filing_date': ...,
        'market': 'sec'|'fca'|'esma',  # MARKET-AGNOSTIC
        'ticker': ...
    },
    'statistics': {...}  # optional
}

Fact structure (filings_reader format):
{
    'concept_qname': 'us-gaap:Assets',  # Concept qualified name
    'fact_value': '1000000',
    'context_ref': 'ctx_...',            # Reference to context
    'unit_ref': 'USD',
    'decimals': '-3',
    'concept_label': 'Assets'
}
"""

from pathlib import Path
from typing import Dict, List, Optional
import json
import logging

from core.data_paths import CCQPaths


logger = logging.getLogger(__name__)


class ParsedFactsLoader:
    """
    Load and validate Map Pro facts.json files.
    
    Integrates with existing CCQPaths infrastructure for file discovery.
    Uses the ACTUAL facts.json structure from filings_reader output.
    
    Key features:
    - Uses CCQPaths for file discovery
    - Loads facts with structure: {qname, value, contextRef, ...}
    - Provides accessor methods for facts, contexts, metadata
    - No caching (JSON is ready to load)
    - No filtering (that's for ccq_mapper, not fact_authority)
    
    Usage:
        loader = ParsedFactsLoader(ccq_paths)
        facts_data = loader.load_by_filing_info(market, entity, filing_type, date)
        
        facts = loader.get_facts(facts_data)
        contexts = loader.get_contexts(facts_data)
        metadata = loader.get_metadata(facts_data)
    """
    
    def __init__(self, ccq_paths: CCQPaths):
        """
        Initialize parsed facts loader.
        
        Args:
            ccq_paths: CCQPaths instance for file discovery
        """
        self.paths = ccq_paths
        self.last_loaded_path = None
        self.last_loaded_data = None
    
    def load_by_filing_info(
        self,
        market: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Dict:
        """
        Load parsed facts using filing information.
        
        Uses CCQPaths.find_parsed_facts_filing() to locate the file.
        
        Args:
            market: Market type (e.g., 'sec', 'fca', 'esma')
            entity_name: Entity name
            filing_type: Filing type (e.g., '10-K', '10-Q')
            filing_date: Filing date (YYYYMMDD format)
            
        Returns:
            Dict with parsed facts data
            
        Raises:
            FileNotFoundError: If parsed facts file not found
            ValueError: If JSON is malformed or invalid structure
        """
        logger.info(f"Loading parsed facts: {market}/{entity_name}/{filing_type}/{filing_date}")
        
        # Use existing CCQPaths method to find file
        facts_path = self.paths.find_parsed_facts_filing(
            market=market,
            entity_name=entity_name,
            filing_type=filing_type,
            filing_date=filing_date
        )
        
        if not facts_path:
            raise FileNotFoundError(
                f"Parsed facts not found for: {market}/{entity_name}/{filing_type}/{filing_date}"
            )
        
        logger.debug(f"Found parsed facts at: {facts_path}")
        
        return self.load_from_path(facts_path)
    
    def load_from_path(self, facts_path: Path) -> Dict:
        """
        Load parsed facts from specific file path.
        
        Args:
            facts_path: Path to facts.json file
            
        Returns:
            Dict with parsed facts data (as-is from JSON):
            {
                'facts': List[Dict],
                'contexts': List[Dict],
                'units': List[Dict],
                'metadata': Dict,
                'statistics': Dict (optional)
            }
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON is malformed or invalid structure
        """
        logger.info(f"Loading parsed facts from: {facts_path}")
        
        if not facts_path or not facts_path.exists():
            raise FileNotFoundError(f"Parsed facts file not found: {facts_path}")
        
        # Load JSON
        try:
            with open(facts_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {facts_path}: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load {facts_path}: {e}")
        
        # Validate structure
        self._validate_structure(data, facts_path)
        
        # Store for reference
        self.last_loaded_path = facts_path
        self.last_loaded_data = data
        
        facts_count = len(data.get('facts', []))
        logger.info(f"Loaded {facts_count} facts from {facts_path.name}")
        
        return data
    
    def _validate_structure(self, data: Dict, facts_path: Path) -> None:
        """
        Validate parsed facts structure.
        
        Args:
            data: Parsed facts data
            facts_path: Path to file (for error messages)
            
        Raises:
            ValueError: If structure is invalid
        """
        if not isinstance(data, dict):
            raise ValueError(f"Parsed facts must be a dict, got {type(data)}")
        
        # Check for required 'facts' key
        if 'facts' not in data:
            raise ValueError(f"'facts' key missing in {facts_path.name}")
        
        if not isinstance(data['facts'], list):
            raise ValueError(
                f"'facts' must be a list, got {type(data['facts'])} in {facts_path.name}"
            )
        
        # Warn if contexts missing (not fatal, some files may not have them)
        if 'contexts' not in data:
            logger.warning(f"'contexts' key missing in {facts_path.name}")
        
        # Warn if metadata missing (not fatal)
        if 'metadata' not in data:
            logger.warning(f"'metadata' key missing in {facts_path.name}")
        
        logger.debug(f"Validated structure: {len(data['facts'])} facts")
    
    def get_facts(self, facts_data: Dict) -> List[Dict]:
        """
        Extract facts list from parsed facts data.
        
        Args:
            facts_data: Parsed facts data from load_*() method
            
        Returns:
            List of fact dicts with structure:
            {
                'qname': 'us-gaap:Assets',  # Concept qualified name
                'value': '1000000',
                'contextRef': 'ctx_...',
                'unit': 'USD',
                'decimals': '-3',
                'label': 'Assets'
            }
        """
        return facts_data.get('facts', [])
    
    def get_contexts(self, facts_data: Dict) -> List[Dict]:
        """
        Extract contexts list from parsed facts data.
        
        Args:
            facts_data: Parsed facts data from load_*() method
            
        Returns:
            List of context dicts
        """
        return facts_data.get('contexts', [])
    
    def get_metadata(self, facts_data: Dict) -> Dict:
        """
        Extract metadata from parsed facts data.
        
        Args:
            facts_data: Parsed facts data from load_*() method
            
        Returns:
            Metadata dict with keys like:
            {
                'filing_id': ...,
                'company': ...,
                'cik': ...,
                'filing_type': ...,
                'filing_date': ...,
                'market': ...,
                'ticker': ...
            }
        """
        return facts_data.get('metadata', {})
    
    def get_units(self, facts_data: Dict) -> List[Dict]:
        """
        Extract units list from parsed facts data.
        
        Args:
            facts_data: Parsed facts data from load_*() method
            
        Returns:
            List of unit dicts (empty if not present)
        """
        return facts_data.get('units', [])
    
    def get_statistics(self, facts_data: Dict) -> Dict:
        """
        Get statistics about loaded facts.
        
        Args:
            facts_data: Parsed facts data from load_*() method
            
        Returns:
            Dict with statistics
        """
        facts = self.get_facts(facts_data)
        contexts = self.get_contexts(facts_data)
        metadata = self.get_metadata(facts_data)
        units = self.get_units(facts_data)
        
        return {
            'total_facts': len(facts),
            'total_contexts': len(contexts),
            'total_units': len(units),
            'has_metadata': bool(metadata),
            'has_contexts': 'contexts' in facts_data,
            'has_units': 'units' in facts_data,
            'has_statistics': 'statistics' in facts_data,
            'market': metadata.get('market', 'unknown'),
            'company': metadata.get('company', 'unknown'),
            'filing_type': metadata.get('filing_type', 'unknown')
        }
    
    def filter_facts_by_concept(
        self,
        facts_data: Dict,
        concept_qname: str
    ) -> List[Dict]:
        """
        Filter facts by concept qname.
        
        Supports multiple field name variations:
        - concept_qname
        - qname
        - concept
        
        Args:
            facts_data: Parsed facts data
            concept_qname: Concept qname to filter by (e.g., 'us-gaap:Assets')
            
        Returns:
            List of matching facts
        """
        facts = self.get_facts(facts_data)
        matching = []
        for fact in facts:
            concept = (
                fact.get('concept_qname') or
                fact.get('qname') or
                fact.get('concept')
            )
            if concept == concept_qname:
                matching.append(fact)
        return matching
    
    def filter_facts_by_context(
        self,
        facts_data: Dict,
        context_ref: str
    ) -> List[Dict]:
        """
        Filter facts by context reference.
        
        Supports multiple field name variations:
        - context_ref
        - contextRef
        - context
        
        Args:
            facts_data: Parsed facts data
            context_ref: Context reference to filter by
            
        Returns:
            List of matching facts
        """
        facts = self.get_facts(facts_data)
        matching = []
        for fact in facts:
            context = (
                fact.get('context_ref') or
                fact.get('contextRef') or
                fact.get('context')
            )
            if context == context_ref:
                matching.append(fact)
        return matching
    
    def get_concepts(self, facts_data: Dict) -> List[str]:
        """
        Get list of unique concept qnames in facts.
        
        Supports multiple field name variations:
        - concept_qname
        - qname
        - concept
        
        Args:
            facts_data: Parsed facts data
            
        Returns:
            List of unique concept qnames
        """
        facts = self.get_facts(facts_data)
        concepts = set()
        for fact in facts:
            concept = (
                fact.get('concept_qname') or
                fact.get('qname') or
                fact.get('concept')
            )
            if concept:
                concepts.add(concept)
        return sorted(list(concepts))
    
    def get_last_loaded_path(self) -> Optional[Path]:
        """
        Get path to last loaded file.
        
        Returns:
            Path to last loaded facts.json, or None
        """
        return self.last_loaded_path