# File: engines/fact_authority/process/statement_reconciler.py
# Path: engines/fact_authority/process/statement_reconciler.py

"""
Statement Reconciler
====================

Reconciles mapper outputs against taxonomy authority.

CORE PRINCIPLE:
    TAXONOMY is the source of truth.
    Mappers are compared TO taxonomy, not to each other.

Decision Logic:
    1. Look up concept in taxonomy
    2. Get taxonomy's statement assignment
    3. Check if Map Pro placed it correctly
    4. Check if CCQ placed it correctly
    5. Generate validation result

Does NOT:
    - Load statements (statement_loader does that)
    - Parse taxonomy (taxonomy_reader does that)
    - Write output (output_writer does that)
"""

from typing import Dict, Any, List
from collections import defaultdict

from core.system_logger import get_logger
from core.data_paths import CCQPaths
from engines.fact_authority.process.concept_extractor import ConceptExtractor
from engines.fact_authority.process.role_classifier import RoleClassifier
from engines.fact_authority.process.concept_validator import ConceptValidator
from engines.fact_authority.process.concept_filter import ConceptFilter  # ← ADDED

logger = get_logger(__name__)


class StatementReconciler:
    """
    Reconciles mapper statements against taxonomy authority.
    
    Uses taxonomy_reader as the authoritative source for where
    concepts should be placed.
    """
    
    # Statement type mappings
    STATEMENT_TYPES = [
        'balance_sheet',
        'income_statement',
        'cash_flow',
        'other'
    ]
    
    def __init__(self, taxonomy_data: Dict[str, Any], ccq_paths: CCQPaths):
        """
        Initialize reconciler with taxonomy authority.
        
        Args:
            taxonomy_data: Taxonomy data (TaxonomyProfile object, dict, or enriched dict)
            ccq_paths: CCQPaths instance
        """
        self.logger = logger
        self.taxonomy_data = taxonomy_data
        self.ccq_paths = ccq_paths
        
        # Initialize helper components
        self.role_classifier = RoleClassifier()
        self.concept_extractor = ConceptExtractor(self.role_classifier)
        
        # Extract taxonomy concepts and their statement assignments
        self.taxonomy_concepts = self.concept_extractor.extract_taxonomy_concepts(
            taxonomy_data
        )
        
        # Extract extension mappings (if enriched taxonomy provided)
        # This will only exist if taxonomy was enriched with extensions
        if isinstance(taxonomy_data, dict):
            self.extension_mappings = taxonomy_data.get('extension_mappings', {})
        else:
            self.extension_mappings = {}
        
        # Initialize validator
        self.validator = ConceptValidator(
            self.taxonomy_concepts,
            self.extension_mappings,
            self.concept_extractor.normalize_concept
        )
        
        self.logger.info(
            f"StatementReconciler initialized with "
            f"{len(self.taxonomy_concepts)} taxonomy concepts, "
            f"{len(self.extension_mappings)} extension mappings"
        )
    
    def reconcile(
        self,
        map_pro_statements: Dict[str, Any],
        ccq_statements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Reconcile mapper statements against taxonomy.
        
        Args:
            map_pro_statements: Statements from Map Pro
            ccq_statements: Statements from CCQ
            
        Returns:
            {
                'statements': {
                    'balance_sheet': {
                        'validated_facts': [...],
                        'statistics': {...}
                    },
                    ... (for each statement type)
                },
                'overall_statistics': {...},
                'metadata': {...}
            }
        """
        self.logger.info("Starting reconciliation against taxonomy")
        
        reconciled_statements = {}
        overall_stats = self._initialize_statistics()
        
        # Reconcile each statement type
        for stmt_type in self.STATEMENT_TYPES:
            self.logger.info(f"Reconciling {stmt_type}")
            
            result = self._reconcile_statement(
                stmt_type,
                map_pro_statements.get(stmt_type, {}),
                ccq_statements.get(stmt_type, {})
            )
            
            reconciled_statements[stmt_type] = result
            
            # Aggregate statistics
            if 'statistics' in result:
                self._aggregate_statistics(overall_stats, result['statistics'])
        
        self.logger.info("Reconciliation completed")
        
        return {
            'statements': reconciled_statements,
            'overall_statistics': overall_stats,
            'metadata': {
                'reconciliation_method': 'taxonomy_authority',
                'taxonomy_concepts': len(self.taxonomy_concepts)
            }
        }
    
    def _reconcile_statement(
        self,
        statement_type: str,
        map_pro_statement: Dict[str, Any],
        ccq_statement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Reconcile one statement type against taxonomy.
        
        Args:
            statement_type: Statement type being reconciled
            map_pro_statement: Map Pro statement data
            ccq_statement: CCQ statement data
            
        Returns:
            {
                'validated_facts': [...],
                'statistics': {...},
                'discrepancies': [...]
            }
        """
        map_pro_facts = map_pro_statement.get('facts', [])
        ccq_facts = ccq_statement.get('facts', [])
        
        # Build concept indexes
        map_pro_concepts = self._build_concept_index(map_pro_facts)
        ccq_concepts = self._build_concept_index(ccq_facts)
        
        # Get all unique concepts
        all_concepts = set(map_pro_concepts.keys()) | set(ccq_concepts.keys())
        
        # ✅ FILTER OUT NON-FINANCIAL CONCEPTS (PHASE 1 FIX)
        all_concepts = ConceptFilter.filter_concepts(list(all_concepts))
        
        validated_facts = []
        discrepancies = []
        statistics = self._initialize_statistics()
        statistics['total_concepts'] = len(all_concepts)
        statistics['map_pro_facts'] = len(map_pro_facts)
        statistics['ccq_facts'] = len(ccq_facts)
        
        # Reconcile each concept
        for concept in sorted(all_concepts):
            normalized_concept = self.concept_extractor.normalize_concept(concept)
            
            # Check mapper placements
            in_map_pro = concept in map_pro_concepts
            in_ccq = concept in ccq_concepts
            
            # Validate concept placement
            validation = self.validator.validate_placement(
                concept,
                normalized_concept,
                statement_type,
                in_map_pro,
                in_ccq
            )
            
            # Determine category for statistics (using same logic as source_mapper)
            # This ensures reconciliation_report statistics match actual facts
            if validation['is_valid']:
                # Concept is correctly placed
                if in_map_pro and in_ccq:
                    category = 'taxonomy_correct_both'
                elif in_map_pro:
                    category = 'taxonomy_correct_map_pro_only'
                elif in_ccq:
                    category = 'taxonomy_correct_ccq_only'
                else:
                    # Taxonomy says concept should be here, but neither mapper has it
                    category = 'not_in_taxonomy'
            else:
                # Concept is incorrectly placed (or not in taxonomy)
                if 'not_in_taxonomy' in validation.get('reason', ''):
                    category = 'not_in_taxonomy'
                else:
                    category = 'taxonomy_correct_neither'
            
            # Update statistics with corrected category
            statistics[category] += 1
            
            # Add to validated facts if correct
            if validation['is_valid']:
                # Determine source mapper (same logic as category above)
                if in_map_pro and in_ccq:
                    source_mapper = 'both'
                elif in_map_pro:
                    source_mapper = 'map_pro'
                elif in_ccq:
                    source_mapper = 'ccq'
                else:
                    source_mapper = 'taxonomy'  # Shouldn't happen but safety
                
                # Use Map Pro fact if available (has more context)
                if in_map_pro:
                    facts_to_add = map_pro_concepts[concept]
                elif in_ccq:
                    facts_to_add = ccq_concepts[concept]
                else:
                    facts_to_add = []
                
                # Add source attribution to each fact
                for fact in facts_to_add:
                    fact_with_source = fact.copy()
                    fact_with_source['source_mapper'] = source_mapper
                    validated_facts.append(fact_with_source)
            
            # Record discrepancy if incorrect
            if not validation['is_valid']:
                taxonomy_statement = self.validator._resolve_taxonomy_statement(
                    concept, normalized_concept
                )
                discrepancies.append({
                    'concept': concept,
                    'expected_statement': taxonomy_statement,
                    'current_statement': statement_type,
                    'in_map_pro': in_map_pro,
                    'in_ccq': in_ccq,
                    'reason': validation['reason']
                })
        
        return {
            'validated_facts': validated_facts,
            'statistics': statistics,
            'discrepancies': discrepancies
        }
    
    def _build_concept_index(self, facts: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Build index of facts by concept.
        
        Handles different field names:
        - Map Pro uses 'concept'
        - CCQ uses 'qname'
        - Legacy/other formats may use 'concept_qname'
        
        Args:
            facts: List of fact dicts
            
        Returns:
            Dict mapping concept_qname to list of facts
        """
        index = defaultdict(list)
        
        for fact in facts:
            # Try different field names (market-agnostic approach)
            concept = (
                fact.get('concept_qname') or  # Legacy format
                fact.get('qname') or           # CCQ format
                fact.get('concept')            # Map Pro format
            )
            
            if concept:
                index[concept].append(fact)
        
        return dict(index)
    
    @staticmethod
    def _initialize_statistics() -> Dict[str, int]:
        """
        Initialize statistics dictionary.
        
        Returns:
            Dict with all statistic keys set to 0
        """
        return {
            'total_concepts': 0,
            'taxonomy_correct_both': 0,
            'taxonomy_correct_map_pro_only': 0,
            'taxonomy_correct_ccq_only': 0,
            'taxonomy_correct_neither': 0,
            'not_in_taxonomy': 0,
            'map_pro_facts': 0,
            'ccq_facts': 0
        }
    
    @staticmethod
    def _aggregate_statistics(overall: Dict[str, int], statement: Dict[str, int]) -> None:
        """
        Aggregate statement statistics into overall statistics.
        
        Args:
            overall: Overall statistics dict (modified in place)
            statement: Statement statistics dict
        """
        for key in overall.keys():
            if key in statement:
                overall[key] += statement[key]


__all__ = ['StatementReconciler']