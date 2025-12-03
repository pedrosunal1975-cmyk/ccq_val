"""
CCQ Mapper - Property-Based Classification Mapper
=================================================

Alternative XBRL mapping engine that uses property-based classification
instead of concept-based matching. Designed to be structurally different
from Map Pro's search-based approach.

Architecture:
    - Bottom-up: Start with facts, not taxonomy
    - Property-driven: Classify by XBRL attributes
    - Cluster-based: Group similar facts naturally
    - Validate after: Compare to taxonomy post-construction

Key Difference from Map Pro:
    Map Pro: Taxonomy → Search Facts → Match
    CCQ: Facts → Extract Properties → Classify → Validate

Refactored Structure:
    - mapper_coordinator: Main entry point (backward compatible)
    - orchestration/: Phase coordination and specialized processors
    - loaders/: Data loading components
    - extractors/: Property and context extraction
    - classifiers/: Fact classification by properties
    - clustering/: Fact clustering and boundary detection
    - construction/: Statement construction
    - validation/: Validation and comparison
    - analysis/: Duplicate detection, gap analysis, success metrics
    - reporting/: Logging and report generation
"""

from .mapper_coordinator import CCQMapperCoordinator

__version__ = '0.2.0'
__all__ = ['CCQMapperCoordinator']