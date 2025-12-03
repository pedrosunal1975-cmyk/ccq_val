# File: engines/ccq_mapper/orchestration/property_processor.py

"""
Property Processor
==================

Handles property extraction and fact enrichment.

Responsibility:
- Extract XBRL properties from facts
- Analyze context information
- Enrich facts with extracted data
"""

from typing import Dict, Any, List

from core.system_logger import get_logger
from ..extractors.property_extractor import PropertyExtractor
from ..extractors.context_analyzer import ContextAnalyzer

logger = get_logger(__name__)


class PropertyProcessor:
    """Processes fact properties and enrichment."""
    
    def __init__(self):
        """Initialize property processor."""
        self.property_extractor = PropertyExtractor()
        self.context_analyzer = ContextAnalyzer()
        self.logger = logger
    
    def extract_properties(
        self,
        facts: List[Dict[str, Any]],
        contexts: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract XBRL properties from each fact.
        
        NO CONCEPT MATCHING - just property extraction.
        
        Args:
            facts: List of facts to process
            contexts: Context information
            
        Returns:
            List of enriched facts with extracted properties
        """
        self.logger.info("Extracting properties from facts...")
        
        enriched_facts = []
        
        for fact in facts:
            # Extract base properties
            properties = self.property_extractor.extract_properties(fact)
            
            # Analyze context structure
            context_info = self.context_analyzer.analyze_context(
                fact.get('contextRef') or fact.get('context_ref'), contexts
            )
            
            # Combine
            enriched_fact = {
                **fact,
                'extracted_properties': properties,
                'context_info': context_info
            }
            
            enriched_facts.append(enriched_fact)
        
        return enriched_facts


__all__ = ['PropertyProcessor']