"""
Parsed Facts Loader
===================

Loads parsed facts from JSON files (Map Pro's parsed output).

CRITICAL: Loads facts WITHOUT building concept indexes.

Filtering Pipeline:
1. Load raw facts from JSON
2. Enrich with dimensional context flags
3. Filter out non-mappable concepts (metadata, DEI, etc.)
"""

from typing import Dict, Any, List, Tuple
from pathlib import Path
import json

from core.system_logger import get_logger

logger = get_logger(__name__)


class ParsedFactsLoader:
    """
    Load parsed facts from JSON files.
    
    These are facts that have been extracted from XBRL but NOT yet
    mapped to concepts. This is the raw input for CCQ mapper.
    
    Filtering Pipeline:
    1. Dimensional context filtering (primary vs dimensional)
    2. Concept namespace filtering (exclude dei, srt, country, etc.)
    3. Concept pattern filtering (exclude EntityCentralIndexKey, etc.)
    """
    
    def __init__(self, market: str = None):
        """
        Initialize loader with concept filter.
        
        Args:
            market: Optional market identifier (sec, fca, esma).
                   If None, will be extracted from metadata during loading.
        """
        self.default_market = market
        self.concept_filter = None  # Will be created when market is known
        
    def _ensure_concept_filter(self, market: str = None):
        """
        Ensure concept filter is initialized with correct market.
        
        Args:
            market: Market identifier from metadata
        """
        # Determine market to use
        filter_market = market or self.default_market or 'sec'
        
        # Create or recreate filter if market changed
        if self.concept_filter is None or getattr(self.concept_filter, 'market', None) != filter_market:
            try:
                from engines.ccq_mapper.filters.concept_filter import ConceptFilter
                self.concept_filter = ConceptFilter(market=filter_market)
                logger.info(f"Initialized ConceptFilter for market: {filter_market}")
            except ImportError:
                logger.warning("ConceptFilter not available - concept filtering disabled")
                self.concept_filter = None
    
    def load_parsed_facts(
        self,
        parsed_facts_path: Path
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Load parsed facts from JSON file.
        
        Args:
            parsed_facts_path: Path to parsed facts JSON
            
        Returns:
            Tuple of (facts_list, metadata_dict)
        """
        logger.info(f"Loading parsed facts from: {parsed_facts_path}")
        
        if not parsed_facts_path.exists():
            raise FileNotFoundError(f"Parsed facts file not found: {parsed_facts_path}")
        
        try:
            with open(parsed_facts_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract facts and metadata
            if isinstance(data, dict):
                facts = data.get('facts', [])
                contexts = data.get('contexts', [])
                
                # FIXED: Extract from nested 'metadata' key
                raw_metadata = data.get('metadata', {})
                
                # Extract market from metadata (defaults to 'sec')
                market = raw_metadata.get('market', 'sec')
                
                metadata = {
                    'filing_id': raw_metadata.get('filing_id'),
                    'company_name': raw_metadata.get('company'),  # Key is 'company' not 'company_name'
                    'cik': raw_metadata.get('cik'),
                    'form_type': raw_metadata.get('filing_type'),  # Key is 'filing_type' not 'form_type'
                    'filing_date': raw_metadata.get('filing_date'),
                    'market': market,
                    'ticker': raw_metadata.get('ticker'),
                    'source_file': str(parsed_facts_path)
                }
                
                # Initialize market-aware concept filter
                self._ensure_concept_filter(market)
                
                # CRITICAL FIX: Enrich facts with is_primary_context flag
                facts = self._enrich_with_context_flags(facts, contexts)
                
                # CRITICAL FIX 2: Filter out non-mappable concepts (now market-aware)
                facts = self._filter_non_mappable_concepts(facts)
                
            elif isinstance(data, list):
                # If data is just a list of facts
                facts = data
                metadata = {
                    'market': self.default_market or 'sec',
                    'source_file': str(parsed_facts_path)
                }
                
                # Initialize concept filter with default market
                self._ensure_concept_filter(metadata['market'])
            else:
                raise ValueError(f"Unexpected data format: {type(data)}")
            
            logger.info(f"Loaded {len(facts)} parsed facts")
            
            return facts, metadata
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load parsed facts: {e}")
            raise
    
    def load_multiple_filings(
        self,
        filing_paths: List[Path]
    ) -> Dict[str, Tuple[List[Dict[str, Any]], Dict[str, Any]]]:
        """
        Load parsed facts from multiple filings.
        
        Args:
            filing_paths: List of paths to parsed facts files
            
        Returns:
            Dictionary mapping filing_id to (facts, metadata)
        """
        logger.info(f"Loading {len(filing_paths)} filings")
        
        results = {}
        
        for path in filing_paths:
            try:
                facts, metadata = self.load_parsed_facts(path)
                filing_id = metadata.get('filing_id', path.stem)
                results[filing_id] = (facts, metadata)
            except Exception as e:
                logger.error(f"Failed to load {path}: {e}")
                continue
        
        logger.info(f"Successfully loaded {len(results)} filings")
        
        return results
    
    def validate_facts_structure(self, facts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate that facts have expected structure.
        
        Returns:
            Validation report
        """
        if not facts:
            return {
                'valid': False,
                'error': 'No facts found'
            }
        
        required_fields = ['value', 'contextRef']
        recommended_fields = ['label', 'qname', 'unit', 'decimals']
        
        issues = []
        
        for i, fact in enumerate(facts[:10]):  # Check first 10
            missing_required = [f for f in required_fields if f not in fact]
            if missing_required:
                issues.append(f"Fact {i}: Missing required fields {missing_required}")
        
        if issues:
            return {
                'valid': False,
                'issues': issues
            }
        
        return {
            'valid': True,
            'total_facts': len(facts),
            'sample_fact': facts[0] if facts else None
        }
    
    def _enrich_with_context_flags(
        self,
        facts: List[Dict[str, Any]],
        contexts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enrich facts with is_primary_context flag based on dimensional analysis.
        
        A primary context has NO dimensions (dimensions == {} or empty).
        A dimensional context has dimensions (product breakdowns, segments, etc.).
        
        Args:
            facts: List of fact dictionaries
            contexts: List of context dictionaries
            
        Returns:
            Facts enriched with is_primary_context flag
        """
        # Build context lookup by context_id
        context_lookup = {}
        for context in contexts:
            context_id = context.get('context_id')
            if context_id:
                context_lookup[context_id] = context
        
        logger.info(f"Built context lookup with {len(context_lookup)} contexts")
        
        # Enrich each fact
        primary_count = 0
        dimensional_count = 0
        
        for fact in facts:
            # Get context reference from fact
            context_ref = (
                fact.get('context_ref') or
                fact.get('contextRef') or
                fact.get('context')
            )
            
            if not context_ref:
                # No context ref - treat as primary by default
                fact['is_primary_context'] = True
                primary_count += 1
                continue
            
            # Look up context
            context = context_lookup.get(context_ref)
            
            if not context:
                # Context not found - treat as primary by default
                fact['is_primary_context'] = True
                primary_count += 1
                continue
            
            # Check dimensions
            dimensions = context.get('dimensions', {})
            
            # Primary context = NO dimensions (empty dict)
            # Dimensional context = HAS dimensions (non-empty dict)
            is_primary = len(dimensions) == 0
            
            fact['is_primary_context'] = is_primary
            
            if is_primary:
                primary_count += 1
            else:
                dimensional_count += 1
        
        logger.info(
            f"Enriched facts: {primary_count} primary context, "
            f"{dimensional_count} dimensional context"
        )
        
        return facts
    
    def _filter_non_mappable_concepts(
        self,
        facts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter out non-mappable concepts (metadata, DEI, etc.).
        
        Removes facts that belong to:
        - Non-mappable namespaces (dei, srt, country, currency, etc.)
        - Non-mappable patterns (EntityCentralIndexKey, DocumentType, etc.)
        - Extensible references (list/enumeration pointers)
        
        Args:
            facts: List of fact dictionaries
            
        Returns:
            Filtered list of mappable facts only
        """
        if not self.concept_filter:
            logger.warning("Concept filter not available - skipping concept filtering")
            return facts
        
        mappable_facts = []
        filtered_count = 0
        filter_reasons = {}
        
        for fact in facts:
            if self.concept_filter.is_mappable_fact(fact):
                mappable_facts.append(fact)
            else:
                filtered_count += 1
                # Track filter reasons for logging
                reason = self.concept_filter.get_filter_reason(fact)
                filter_reasons[reason] = filter_reasons.get(reason, 0) + 1
        
        # Log filtering results
        logger.info(
            f"Concept filtering: {len(mappable_facts)} mappable, "
            f"{filtered_count} filtered"
        )
        
        if filter_reasons:
            logger.debug("Filter reasons:")
            for reason, count in sorted(filter_reasons.items(), key=lambda x: -x[1]):
                logger.debug(f"  {reason}: {count} facts")
        
        return mappable_facts


__all__ = ['ParsedFactsLoader']