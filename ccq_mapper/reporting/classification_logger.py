"""
Classification Logger
=====================

Location: ccq_val/engines/ccq_mapper/reporting/classification_logger.py

Logging for classification operations and metrics.

Functions:
- log_classification_summary: Overall classification statistics
- log_classification_distribution: Classification by dimension
- log_confidence_metrics: Confidence score distribution
- log_clustering_summary: Clustering results

Features:
- Classification rate tracking
- Confidence level distribution
- Dimensional classification breakdown
"""

import logging
from typing import Any, Dict

from .constants import (
    SECTION_SEPARATOR,
    TEMPLATE_CLASSIFICATION_SUMMARY,
    TEMPLATE_CONFIDENCE_SUMMARY
)
from .logger_base import MapperLoggerBase


class ClassificationLogger:
    """Handles logging for classification operations."""
    
    def __init__(self, base_logger: MapperLoggerBase):
        """
        Initialize classification logger.
        
        Args:
            base_logger: MapperLoggerBase instance
        """
        self.base = base_logger
    
    def log_classification_summary(
        self,
        total_facts: int,
        classified_facts: int,
        classification_rate: float,
        **context: Any
    ):
        """
        Log classification summary statistics.
        
        Args:
            total_facts: Total number of facts
            classified_facts: Number of successfully classified facts
            classification_rate: Classification success rate (percentage)
            **context: Additional context
        """
        message = TEMPLATE_CLASSIFICATION_SUMMARY.format(
            classified=classified_facts,
            total=total_facts,
            rate=classification_rate
        )
        
        full_context = self.base._add_context({
            'event': 'classification_summary',
            'total_facts': total_facts,
            'classified_facts': classified_facts,
            'classification_rate': classification_rate,
            **context
        })
        
        self.base.system_logger.log_with_context(
            self.base.base_logger,
            logging.INFO,
            message,
            **full_context
        )
    
    def log_classification_distribution(
        self,
        distribution: Dict[str, Dict[str, int]]
    ):
        """
        Log classification distribution across dimensions.
        
        Args:
            distribution: Classification distribution by dimension
                         e.g., {'accounting': {'debit': 10, 'credit': 15}}
        """
        self.base.base_logger.info(f"\n{SECTION_SEPARATOR}")
        self.base.base_logger.info("CLASSIFICATION DISTRIBUTION")
        self.base.base_logger.info(SECTION_SEPARATOR)
        
        for dimension, counts in distribution.items():
            self.base.base_logger.info(f"\n{dimension.upper()}:")
            for type_name, count in sorted(
                counts.items(),
                key=lambda x: x[1],
                reverse=True
            ):
                self.base.base_logger.info(f"  {type_name}: {count}")
        
        self.base.base_logger.info(f"\n{SECTION_SEPARATOR}\n")
    
    def log_confidence_metrics(
        self,
        avg_confidence: float,
        high_count: int,
        medium_count: int,
        low_count: int
    ):
        """
        Log confidence metrics.
        
        Args:
            avg_confidence: Average confidence score (0.0-1.0)
            high_count: Number of high-confidence classifications
            medium_count: Number of medium-confidence classifications
            low_count: Number of low-confidence classifications
        """
        message = TEMPLATE_CONFIDENCE_SUMMARY.format(
            avg=avg_confidence,
            high=high_count,
            medium=medium_count,
            low=low_count
        )
        
        full_context = self.base._add_context({
            'event': 'confidence_metrics',
            'average_confidence': avg_confidence,
            'high_confidence_count': high_count,
            'medium_confidence_count': medium_count,
            'low_confidence_count': low_count
        })
        
        # Use warning level if there are issues
        level = (
            logging.WARNING
            if low_count > 0 or avg_confidence < 0.7
            else logging.INFO
        )
        
        self.base.system_logger.log_with_context(
            self.base.base_logger,
            level,
            message,
            **full_context
        )
    
    def log_clustering_summary(
        self,
        cluster_count: int,
        clustered_facts: int,
        total_facts: int
    ):
        """
        Log clustering summary.
        
        Args:
            cluster_count: Number of clusters formed
            clustered_facts: Number of facts in clusters
            total_facts: Total number of facts
        """
        clustering_rate = (
            clustered_facts / total_facts * 100
            if total_facts > 0 else 0.0
        )
        
        message = (
            f"Clustering: {cluster_count} clusters, "
            f"{clustered_facts}/{total_facts} facts "
            f"({clustering_rate:.1f}%)"
        )
        
        full_context = self.base._add_context({
            'event': 'clustering_summary',
            'cluster_count': cluster_count,
            'clustered_facts': clustered_facts,
            'total_facts': total_facts,
            'clustering_rate': clustering_rate
        })
        
        self.base.system_logger.log_with_context(
            self.base.base_logger,
            logging.INFO,
            message,
            **full_context
        )