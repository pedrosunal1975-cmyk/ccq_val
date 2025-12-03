# File: engines/fact_authority/process/__init__.py

"""
Fact Authority Processing Components
=====================================

Components for reconciliation and analysis against taxonomy authority.

Components:
    - phase_manager: Coordinates the 3 validation phases
    - statement_reconciler: Reconciles statements against taxonomy
    - statement_classifier: Classifies facts by statement type (taxonomy-driven)
    - concept_filter: Filters non-financial concepts from validation  # ← ADD THIS
    - null_quality_handler: Analyzes null quality patterns
    - extension_inheritance_tracer: Traces extension concept inheritance
    - xbrl_filings: Consolidates XBRL extensions with taxonomy
    - taxonomy_enricher: Enriches taxonomy with extension concepts
    - taxonomy_detector: Detects taxonomies from concept namespaces
    - concept_extractor: Extracts concepts from taxonomy sources
    - role_classifier: Classifies role URIs to statement types
    - concept_validator: Validates concept placements
"""

# Existing imports
from engines.fact_authority.process.statement_reconciler import StatementReconciler
from engines.fact_authority.process.statement_classifier import StatementClassifier
from engines.fact_authority.process.concept_filter import ConceptFilter  # ← ADD THIS
from engines.fact_authority.process.null_quality_handler import NullQualityHandler
from engines.fact_authority.process.extension_inheritance_tracer import ExtensionInheritanceTracer
from engines.fact_authority.process.xbrl_filings import XBRLFilingsConsolidator
from engines.fact_authority.process.phase_manager import PhaseManager
from engines.fact_authority.process.taxonomy_enricher import TaxonomyEnricher
from engines.fact_authority.process.taxonomy_detector import TaxonomyDetector
from engines.fact_authority.process.concept_extractor import ConceptExtractor
from engines.fact_authority.process.role_classifier import RoleClassifier
from engines.fact_authority.process.concept_validator import ConceptValidator

__all__ = [
    'StatementReconciler',
    'StatementClassifier',
    'ConceptFilter',  # ← ADD THIS
    'NullQualityHandler',
    'ExtensionInheritanceTracer',
    'XBRLFilingsConsolidator',
    'PhaseManager',
    'TaxonomyEnricher',
    'TaxonomyDetector',
    'ConceptExtractor',
    'RoleClassifier',
    'ConceptValidator',
]