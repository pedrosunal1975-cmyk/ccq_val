"""
CCQ Mapper Logger
=================

Specialized logger for CCQ Mapper with mapper-specific context.

Extends the system logger with mapper-specific features:
- Mapper phase tracking (extraction, classification, clustering, etc.)
- Property classification logging
- Comparison result logging
- Disagreement tracking
"""

import logging
from typing import Any, Dict, Optional
from pathlib import Path

from core.system_logger import get_logger as get_system_logger, SystemLogger


class MapperLogger:
    """
    Specialized logger for CCQ Mapper operations.
    
    Provides structured logging with mapper-specific context:
    - Filing identification
    - Processing phase
    - Classification statistics
    - Validation results
    """
    
    def __init__(self, filing_id: Optional[str] = None):
        """
        Initialize mapper logger.
        
        Args:
            filing_id: Optional filing ID for context
        """
        self.system_logger = SystemLogger()
        self.base_logger = get_system_logger('ccq_mapper')
        self.filing_id = filing_id
        
        # Initialize mapper-specific log file
        self._setup_mapper_log()
    
    def _setup_mapper_log(self):
        """Set up mapper-specific log file."""
        # Get log directory from config
        config = self.system_logger.config
        log_dir = config.get('log_dir')
        
        if log_dir:
            mapper_log_dir = log_dir / 'ccq_mapper'
            mapper_log_dir.mkdir(parents=True, exist_ok=True)
            
            # Create mapper-specific file handler
            from logging.handlers import RotatingFileHandler
            
            mapper_log_file = mapper_log_dir / 'mapper.log'
            file_handler = RotatingFileHandler(
                mapper_log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )
            
            # Use structured formatter if configured
            log_format = config.get('log_format', 'json')
            if log_format == 'json':
                from core.system_logger import StructuredFormatter
                file_handler.setFormatter(StructuredFormatter())
            else:
                file_handler.setFormatter(
                    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                )
            
            self.base_logger.addHandler(file_handler)
    
    def _add_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Add filing context to log entry."""
        full_context = {}
        if self.filing_id:
            full_context['filing_id'] = self.filing_id
        full_context.update(context)
        return full_context
    
    def log_phase_start(self, phase: str, **context: Any):
        """
        Log start of a mapping phase.
        
        Args:
            phase: Phase name (load, extract, classify, cluster, construct, validate)
            **context: Additional context
        """
        full_context = self._add_context({
            'phase': phase,
            'event': 'phase_start',
            **context
        })
        self.system_logger.log_with_context(
            self.base_logger,
            logging.INFO,
            f"Starting phase: {phase}",
            **full_context
        )
    
    def log_phase_complete(self, phase: str, duration: float, **context: Any):
        """
        Log completion of a mapping phase.
        
        Args:
            phase: Phase name
            duration: Phase duration in seconds
            **context: Additional context
        """
        full_context = self._add_context({
            'phase': phase,
            'event': 'phase_complete',
            'duration_seconds': duration,
            **context
        })
        self.system_logger.log_with_context(
            self.base_logger,
            logging.INFO,
            f"Completed phase: {phase} ({duration:.2f}s)",
            **full_context
        )
    
    def log_classification_stats(self, stats: Dict[str, Any]):
        """
        Log classification statistics.
        
        Args:
            stats: Classification statistics dictionary
        """
        full_context = self._add_context({
            'event': 'classification_stats',
            'stats': stats
        })
        self.system_logger.log_with_context(
            self.base_logger,
            logging.INFO,
            f"Classification complete: {stats.get('facts_classified', 0)} facts classified",
            **full_context
        )
    
    def log_clustering_results(self, cluster_count: int, facts_per_cluster: Dict[str, int]):
        """
        Log clustering results.
        
        Args:
            cluster_count: Number of clusters formed
            facts_per_cluster: Dictionary mapping cluster IDs to fact counts
        """
        full_context = self._add_context({
            'event': 'clustering_complete',
            'cluster_count': cluster_count,
            'facts_per_cluster': facts_per_cluster
        })
        self.system_logger.log_with_context(
            self.base_logger,
            logging.INFO,
            f"Clustering complete: {cluster_count} clusters formed",
            **full_context
        )
    
    def log_statement_construction(self, statement_type: str, line_item_count: int):
        """
        Log statement construction.
        
        Args:
            statement_type: Type of statement constructed
            line_item_count: Number of line items in statement
        """
        full_context = self._add_context({
            'event': 'statement_constructed',
            'statement_type': statement_type,
            'line_item_count': line_item_count
        })
        self.system_logger.log_with_context(
            self.base_logger,
            logging.INFO,
            f"Constructed {statement_type}: {line_item_count} line items",
            **full_context
        )
    
    def log_taxonomy_validation(self, validation_results: Dict[str, Any]):
        """
        Log taxonomy validation results.
        
        Args:
            validation_results: Validation results dictionary
        """
        pass_rate = validation_results.get('pass_rate', 0)
        full_context = self._add_context({
            'event': 'taxonomy_validation',
            'validation_results': validation_results
        })
        
        level = logging.INFO if pass_rate >= 90.0 else logging.WARNING
        
        self.system_logger.log_with_context(
            self.base_logger,
            level,
            f"Taxonomy validation complete: {pass_rate:.1f}% pass rate",
            **full_context
        )
    
    def log_map_pro_comparison(self, comparison_results: Dict[str, Any]):
        """
        Log Map Pro comparison results.
        
        Args:
            comparison_results: Comparison results dictionary
        """
        agreement_rate = comparison_results.get('agreement_rate', 0)
        overall_agreement = comparison_results.get('overall_agreement', False)
        
        full_context = self._add_context({
            'event': 'map_pro_comparison',
            'comparison_results': comparison_results
        })
        
        level = logging.INFO if overall_agreement else logging.WARNING
        
        self.system_logger.log_with_context(
            self.base_logger,
            level,
            f"Map Pro comparison: {agreement_rate:.1f}% agreement",
            **full_context
        )
    
    def log_disagreement(
        self,
        concept_name: str,
        ccq_value: Any,
        map_pro_value: Any,
        reason: str
    ):
        """
        Log a specific disagreement with Map Pro.
        
        Args:
            concept_name: Concept that disagrees
            ccq_value: CCQ's value/classification
            map_pro_value: Map Pro's value/classification
            reason: Reason for disagreement
        """
        full_context = self._add_context({
            'event': 'disagreement',
            'concept_name': concept_name,
            'ccq_value': ccq_value,
            'map_pro_value': map_pro_value,
            'reason': reason
        })
        
        self.system_logger.log_with_context(
            self.base_logger,
            logging.WARNING,
            f"Disagreement on {concept_name}: {reason}",
            **full_context
        )
    
    def log_property_extraction(self, fact_count: int, properties_extracted: int):
        """
        Log property extraction results.
        
        Args:
            fact_count: Number of facts processed
            properties_extracted: Number of properties extracted per fact
        """
        full_context = self._add_context({
            'event': 'property_extraction',
            'fact_count': fact_count,
            'properties_extracted': properties_extracted
        })
        
        self.system_logger.log_with_context(
            self.base_logger,
            logging.INFO,
            f"Extracted properties from {fact_count} facts",
            **full_context
        )
    
    def log_error(self, error: Exception, phase: Optional[str] = None, **context: Any):
        """
        Log an error during mapping.
        
        Args:
            error: Exception that occurred
            phase: Phase where error occurred (optional)
            **context: Additional context
        """
        full_context = self._add_context({
            'event': 'error',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'phase': phase,
            **context
        })
        
        self.system_logger.log_with_context(
            self.base_logger,
            logging.ERROR,
            f"Error in {phase or 'mapping'}: {str(error)}",
            **full_context
        )
        
        # Also log traceback
        self.base_logger.exception("Full traceback:")
    
    def log_warning(self, message: str, **context: Any):
        """
        Log a warning.
        
        Args:
            message: Warning message
            **context: Additional context
        """
        full_context = self._add_context({
            'event': 'warning',
            **context
        })
        
        self.system_logger.log_with_context(
            self.base_logger,
            logging.WARNING,
            message,
            **full_context
        )
    
    def log_info(self, message: str, **context: Any):
        """
        Log an info message.
        
        Args:
            message: Info message
            **context: Additional context
        """
        full_context = self._add_context({
            'event': 'info',
            **context
        })
        
        self.system_logger.log_with_context(
            self.base_logger,
            logging.INFO,
            message,
            **full_context
        )
    
    def log_debug(self, message: str, **context: Any):
        """
        Log a debug message.
        
        Args:
            message: Debug message
            **context: Additional context
        """
        full_context = self._add_context({
            'event': 'debug',
            **context
        })
        
        self.system_logger.log_with_context(
            self.base_logger,
            logging.DEBUG,
            message,
            **full_context
        )


def get_mapper_logger(filing_id: Optional[str] = None) -> MapperLogger:
    """
    Get mapper logger instance.
    
    Args:
        filing_id: Optional filing ID for context
        
    Returns:
        MapperLogger instance
    """
    return MapperLogger(filing_id=filing_id)


__all__ = ['MapperLogger', 'get_mapper_logger']