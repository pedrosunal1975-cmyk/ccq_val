"""
CCQ Exception Classes
=====================

Custom exception hierarchy for CCQ Validator.
All CCQ-specific exceptions inherit from CCQException.
"""


class CCQException(Exception):
    """Base exception for all CCQ errors."""
    pass


class CCQError(CCQException):
    """Generic CCQ error."""
    pass


class ConfigurationError(CCQException):
    """Configuration-related errors."""
    pass


class DatabaseError(CCQException):
    """Database operation errors."""
    pass


class NormalizationError(CCQException):
    """Errors during Phase 1 normalization."""
    pass


class ValidationError(CCQException):
    """Errors during Phase 2 validation."""
    pass


class ScoringError(CCQException):
    """Errors during Phase 3 scoring."""
    pass


class FileAccessError(CCQException):
    """File system access errors."""
    pass


class TaxonomyError(CCQException):
    """Taxonomy loading/access errors."""
    pass


class DataQualityError(CCQException):
    """Data quality issues detected."""
    pass

class DataAccessError(CCQException):
    """Data access errors (file system, database)."""
    pass


# Convenience exports for backwards compatibility
__all__ = [
    'CCQException',
    'CCQError',
    'ConfigurationError',
    'DatabaseError',
    'NormalizationError',
    'ValidationError',
    'ScoringError',
    'FileAccessError',
    'TaxonomyError',
    'DataQualityError',
]