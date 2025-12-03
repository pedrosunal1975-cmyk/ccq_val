# File: engines/ccq_mapper/orchestration/classification_processor.py

"""
Classification Processor
=========================

Handles fact classification using multiple classifiers.

Responsibility:
- Run all classifiers on facts
- Track classification metrics
- Generate classification reports
"""

from typing import Tuple, List, Dict, Any

from core.system_logger import get_logger
from ..classifiers.monetary_classifier import MonetaryClassifier
from ..classifiers.temporal_classifier import TemporalClassifier
from ..classifiers.accounting_classifier import AccountingClassifier
from ..classifiers.aggregation_classifier import AggregationClassifier
from ..classifiers.statement_classifier import StatementClassifier
from ..analysis.classification_metrics import ClassificationMetrics

logger = get_logger(__name__)


class ClassificationProcessor:
    """Processes fact classification with metrics tracking."""
    
    def __init__(self):
        """Initialize classification processor."""
        self.monetary_classifier = MonetaryClassifier()
        self.temporal_classifier = TemporalClassifier()
        self.accounting_classifier = AccountingClassifier()
        self.aggregation_classifier = AggregationClassifier()
        self.statement_classifier = StatementClassifier()
        self.classification_metrics = ClassificationMetrics()
        self.logger = logger
    
    def classify_facts(
        self,
        enriched_facts: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Classify facts by their intrinsic properties.
        
        NO CONCEPT MATCHING - pure property-based classification.
        
        Args:
            enriched_facts: Facts with extracted properties
            
        Returns:
            (classified_facts, metrics_report) tuple
        """
        self.logger.info("Classifying facts by properties...")
        
        classified_facts = []
        
        for fact in enriched_facts:
            props = fact['extracted_properties']
            
            # Run independent classifiers (no concept matching)
            classification = {
                'monetary_type': self.monetary_classifier.classify(props),
                'temporal_type': self.temporal_classifier.classify(props),
                'accounting_type': self.accounting_classifier.classify(props),
                'aggregation_level': self.aggregation_classifier.classify(props),
                'predicted_statement': self.statement_classifier.classify(props)
            }
            
            classified_fact = {
                **fact,
                'classification': classification
            }
            
            classified_facts.append(classified_fact)
        
        # Track classification metrics
        self.classification_metrics.track_classified_facts(classified_facts)
        metrics_report = self.classification_metrics.generate_metrics_report()
        
        return classified_facts, metrics_report
    
    def get_statement_classifier(self) -> StatementClassifier:
        """Get statement classifier for external use."""
        return self.statement_classifier
    
    def get_monetary_classifier(self) -> MonetaryClassifier:
        """Get monetary classifier for external use."""
        return self.monetary_classifier
    
    def get_temporal_classifier(self) -> TemporalClassifier:
        """Get temporal classifier for external use."""
        return self.temporal_classifier


__all__ = ['ClassificationProcessor']