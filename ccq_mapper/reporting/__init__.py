"""
CCQ Mapper Reporting Package
=============================

Location: ccq_val/engines/ccq_mapper/reporting/__init__.py

Comprehensive reporting and logging for CCQ mapper operations.

Modules:
- constants: Reporting constants and formatting templates
- mapper_logger: Main orchestrator for structured logging (orchestrator)
- classification_reporter: Classification metrics reporting
- summary_generator: Executive summary generation

Logger Components (refactored):
- logger_base: Core logger setup and configuration
- phase_logger: Phase tracking and timing
- classification_logger: Classification metrics logging
- duplicate_logger: Duplicate detection logging
- quality_logger: Data quality assessment logging
- success_logger: Overall success metrics logging
- general_logger: General purpose logging functions

Usage:
    # Standard usage (unchanged)
    from engines.ccq_mapper.reporting import get_mapper_logger
    
    logger = get_mapper_logger(filing_id="AAPL_10K_20231231")
    logger.log_phase_start("classify")
    logger.log_classification_summary(100, 95, 95.0)
    
    # Using specialized components (new)
    from engines.ccq_mapper.reporting import PhaseLogger
    from engines.ccq_mapper.reporting.logger_base import MapperLoggerBase
    
    base = MapperLoggerBase(filing_id="AAPL_10K_20231231")
    phase_logger = PhaseLogger(base)
    phase_logger.log_phase_start("classify")
"""

# Core constants and templates
from .constants import *

# Main logger (orchestrator - backward compatible)
from .mapper_logger import MapperLogger, get_mapper_logger

# Specialized logger components (new)
from .logger_base import MapperLoggerBase
from .phase_logger import PhaseLogger
from .classification_logger import ClassificationLogger
from .duplicate_logger import DuplicateLogger
from .quality_logger import QualityLogger
from .success_logger import SuccessLogger
from .general_logger import GeneralLogger

# Reporting components
from .classification_reporter import ClassificationReporter
from .summary_generator import SummaryGenerator

__all__ = [
    # Constants (from constants.py)
    'SECTION_SEPARATOR',
    'SUBSECTION_SEPARATOR',
    'MAX_DISPLAY_ITEMS',
    'MAX_DISPLAY_DETAILS',
    'MAX_DISPLAY_PATTERNS',
    'MAX_DISPLAY_GAPS',
    'MAX_DISPLAY_DUPLICATES',
    'LOG_LEVEL_MAPPING',
    'REPORT_SECTIONS',
    'SUCCESS_LEVEL_SYMBOLS',
    'CLASSIFICATION_DIMENSIONS',
    'CONFIDENCE_LEVELS',
    'DUPLICATE_SEVERITY_LABELS',
    'GAP_TYPE_LABELS',
    'DISPLAY_PRECISION',
    
    # Main logger (orchestrator)
    'MapperLogger',
    'get_mapper_logger',
    
    # Logger components (new exports)
    'MapperLoggerBase',
    'PhaseLogger',
    'ClassificationLogger',
    'DuplicateLogger',
    'QualityLogger',
    'SuccessLogger',
    'GeneralLogger',
    
    # Reporting components
    'ClassificationReporter',
    'SummaryGenerator',
]

__version__ = '2.0.0'