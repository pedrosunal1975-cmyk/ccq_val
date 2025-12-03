"""
Statement Constructor
=====================

Constructs financial statements from clustered facts.

CRITICAL: Builds from CLUSTERS, not concept hierarchies.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone

from core.system_logger import get_logger

logger = get_logger(__name__)


class StatementConstructor:
    """
    Construct financial statements from fact clusters.
    
    Builds:
    - Statement metadata
    - Hierarchical line item structure
    - Relationships between line items
    - Summary metrics
    
    Does NOT use taxonomy presentation hierarchies.
    """
    
    STATEMENT_TYPE_NAMES = {
        'balance_sheet': 'Balance Sheet',
        'income_statement': 'Income Statement',
        'cash_flow': 'Statement of Cash Flows',
        'other': 'Other Financial Data'
    }
    
    def construct_statements(
        self,
        clusters: Dict[str, List[Dict[str, Any]]],
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Construct statements from clustered facts.
        
        Args:
            clusters: Dictionary of fact clusters
            metadata: Filing metadata
            
        Returns:
            List of constructed statement dictionaries
        """
        logger.info(f"Constructing statements from {len(clusters)} clusters")
        
        # Group clusters by statement type
        statements_by_type = self._group_by_statement_type(clusters)
        
        # Build each statement
        constructed_statements = []
        
        for stmt_type, type_clusters in statements_by_type.items():
            logger.info(f"Building {stmt_type} from {len(type_clusters)} clusters")
            
            # Merge related clusters for same statement
            merged_facts = self._merge_statement_clusters(type_clusters)
            
            if not merged_facts:
                continue
            
            # Build statement structure
            statement = self._build_statement(stmt_type, merged_facts, metadata)
            constructed_statements.append(statement)
        
        logger.info(f"Constructed {len(constructed_statements)} statements")
        
        return constructed_statements
    
    def _group_by_statement_type(
        self,
        clusters: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """Group clusters by statement type."""
        from collections import defaultdict
        
        grouped = defaultdict(dict)
        
        for cluster_id, facts in clusters.items():
            if not facts:
                continue
            
            # Determine statement type from majority
            stmt_votes = defaultdict(int)
            for fact in facts:
                classification = fact.get('classification', {})
                stmt_type = classification.get('predicted_statement', 'other')
                stmt_votes[stmt_type] += 1
            
            stmt_type = max(stmt_votes, key=stmt_votes.get) if stmt_votes else 'other'
            grouped[stmt_type][cluster_id] = facts
        
        return dict(grouped)
    
    def _merge_statement_clusters(
        self,
        type_clusters: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Merge multiple clusters for the same statement.
        
        Removes duplicates and orders facts logically.
        """
        all_facts = []
        seen_qnames = set()
        
        for cluster_id, facts in type_clusters.items():
            for fact in facts:
                # Use qname + context as unique key
                props = fact.get('extracted_properties', {})
                qname = props.get('qname', '')
                context_ref = props.get('context_ref', '')
                unique_key = f"{qname}_{context_ref}"
                
                if unique_key not in seen_qnames:
                    all_facts.append(fact)
                    seen_qnames.add(unique_key)
        
        # Sort facts by aggregation level and label
        all_facts.sort(key=self._fact_sort_key)
        
        return all_facts
    
    def _fact_sort_key(self, fact: Dict[str, Any]) -> tuple:
        """Generate sort key for fact ordering."""
        classification = fact.get('classification', {})
        props = fact.get('extracted_properties', {})
        
        # Aggregation level (totals last)
        agg_level = classification.get('aggregation_level', 'line_item')
        agg_order = {
            'abstract': 0,
            'total': 3,
            'subtotal': 2,
            'line_item': 1
        }.get(agg_level, 1)
        
        # Label for secondary sort
        label = (props.get('label') or '').lower()
        
        return (agg_order, label)
    
    def _build_statement(
        self,
        stmt_type: str,
        facts: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build a single statement structure.
        """
        # Extract period information
        period_info = self._extract_period_info(facts)
        
        # Build line items with hierarchy
        line_items = self._build_line_items(facts)
        
        # Calculate totals
        totals = self._calculate_totals(line_items)
        
        return {
            'statement_type': stmt_type,
            'statement_name': self.STATEMENT_TYPE_NAMES.get(stmt_type, stmt_type),
            'company': {
                'name': metadata.get('company_name'),
                'cik': metadata.get('cik')
            },
            'period': period_info,
            'line_items': line_items,
            'totals': totals,
            'metadata': {
                'filing_id': metadata.get('filing_id'),
                'filing_date': metadata.get('filing_date'),
                'form_type': metadata.get('form_type'),
                'fact_count': len(facts),
                'constructed_at': datetime.now(timezone.utc).isoformat()
            },
            'construction_method': 'ccq_property_based'
        }
    
    def _extract_period_info(self, facts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract period information from facts."""
        if not facts:
            return {}
        
        # Get period from first fact
        props = facts[0].get('extracted_properties', {})
        context_info = props.get('context_info', {})
        period = context_info.get('period', {})
        
        return {
            'type': period.get('type'),
            'instant': str(period.get('instant')) if period.get('instant') else None,
            'start': str(period.get('start')) if period.get('start') else None,
            'end': str(period.get('end')) if period.get('end') else None,
            'duration_days': period.get('duration_days')
        }
    
    def _build_line_items(
        self,
        facts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Build hierarchical line items from facts.
        """
        line_items = []
        
        for fact in facts:
            line_item = self._fact_to_line_item(fact)
            line_items.append(line_item)
        
        return line_items
    
    def _fact_to_line_item(self, fact: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a fact to a line item structure."""
        props = fact.get('extracted_properties', {})
        classification = fact.get('classification', {})
        
        return {
            'qname': props.get('qname'),
            'label': props.get('label'),
            'value': props.get('value'),
            'unit': props.get('unit'),
            'decimals': props.get('decimals'),
            'context_ref': props.get('context_ref'),
            'properties': {
                'balance_type': props.get('balance_type'),
                'period_type': props.get('period_type'),
                'is_abstract': props.get('is_abstract', False),
                'is_nil': props.get('is_nil', False)
            },
            'classification': {
                'statement': classification.get('predicted_statement'),
                'monetary_type': classification.get('monetary_type'),
                'temporal_type': classification.get('temporal_type'),
                'accounting_type': classification.get('accounting_type'),
                'aggregation_level': classification.get('aggregation_level')
            }
        }
    
    def _calculate_totals(self, line_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary totals from line items."""
        totals = {
            'total_line_items': len(line_items),
            'monetary_items': 0,
            'abstract_items': 0,
            'total_items': 0,
            'subtotal_items': 0,
            'line_item_count': 0
        }
        
        for item in line_items:
            classification = item.get('classification', {})
            
            if classification.get('monetary_type') in ['currency', 'shares']:
                totals['monetary_items'] += 1
            
            if item.get('properties', {}).get('is_abstract'):
                totals['abstract_items'] += 1
            
            agg_level = classification.get('aggregation_level')
            if agg_level == 'total':
                totals['total_items'] += 1
            elif agg_level == 'subtotal':
                totals['subtotal_items'] += 1
            elif agg_level == 'line_item':
                totals['line_item_count'] += 1
        
        return totals
    
    def build_hierarchy(
        self,
        line_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build parent-child hierarchy from flat line items.
        
        Uses aggregation levels to determine relationships.
        """
        hierarchy = {
            'root': [],
            'relationships': []
        }
        
        current_parent = None
        current_children = []
        
        for item in line_items:
            classification = item.get('classification', {})
            agg_level = classification.get('aggregation_level')
            
            if agg_level == 'total':
                # Total becomes parent
                if current_parent and current_children:
                    hierarchy['relationships'].append({
                        'parent': current_parent,
                        'children': current_children
                    })
                current_parent = item
                current_children = []
            elif agg_level in ['line_item', 'subtotal']:
                # Add to current parent's children
                if current_parent:
                    current_children.append(item)
                else:
                    hierarchy['root'].append(item)
            else:
                # Abstract or unknown - add to root
                hierarchy['root'].append(item)
        
        # Add final relationship
        if current_parent and current_children:
            hierarchy['relationships'].append({
                'parent': current_parent,
                'children': current_children
            })
        
        return hierarchy


__all__ = ['StatementConstructor']