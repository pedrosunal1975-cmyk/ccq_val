# File: engines/ccq_mapper/orchestration/__init__.py

"""
Orchestration Module
====================

Contains orchestrators and processors for coordinating mapper operations.

Components:
- PhaseOrchestrator: Coordinates phase execution with timing
- DataLoader: Handles all data loading operations
- PropertyProcessor: Extracts and processes fact properties
- ClassificationProcessor: Runs fact classification
- ClusteringProcessor: Handles fact clustering
- AnalysisOrchestrator: Coordinates analysis operations
- OutputWriter: Writes all outputs to filesystem
"""

from .phase_orchestrator import PhaseOrchestrator
from .data_loader import DataLoader
from .property_processor import PropertyProcessor
from .classification_processor import ClassificationProcessor
from .clustering_processor import ClusteringProcessor
from .analysis_orchestrator import AnalysisOrchestrator
from .output_writer import OutputWriter

__all__ = [
    'PhaseOrchestrator',
    'DataLoader',
    'PropertyProcessor',
    'ClassificationProcessor',
    'ClusteringProcessor',
    'AnalysisOrchestrator',
    'OutputWriter'
]