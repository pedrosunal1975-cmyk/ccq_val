"""
Configuration Loader

Centralized configuration management for the CCQ Validator.
Loads and validates environment variables with type safety and defaults.
"""

import os
from typing import Any, Optional
from pathlib import Path
from dotenv import load_dotenv


class ConfigLoader:
    """
    Thread-safe singleton configuration loader.
    
    Loads configuration from environment variables with validation,
    type conversion, and sensible defaults. All configuration access
    should go through this class to ensure consistency.
    """
    
    _instance: Optional['ConfigLoader'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'ConfigLoader':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize configuration loader. Only runs once due to singleton pattern."""
        if ConfigLoader._initialized:
            return
            
        # Load .env file if it exists
        env_path = Path('.env')
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, interpolate=True)
        
        self._config = self._load_configuration()
        ConfigLoader._initialized = True
    
    def _load_configuration(self) -> dict[str, Any]:
        """
        Load and validate all configuration from environment.
        
        Returns:
            Dictionary of validated configuration values
            
        Raises:
            ValueError: If required configuration is missing or invalid
        """
        config = {
            # Environment
            'environment': self._get_env('CCQ_ENVIRONMENT', 'development'),
            'debug': self._get_bool('CCQ_DEBUG', False),
            'log_level': self._get_env('CCQ_LOG_LEVEL', 'INFO'),
            
            # Map Pro Root Paths (for fallback filesystem searches)
            'map_pro_data_root': self._get_path('MAP_PRO_DATA_ROOT', required=False),
            'map_pro_program_root': self._get_path('MAP_PRO_PROGRAM_ROOT', required=False),
            
            # Data Paths - Critical for integration
            'data_root': self._get_path('CCQ_DATA_ROOT', required=True),
            'program_root': self._get_path('CCQ_PROGRAM_ROOT', required=True),
            'input_path': self._get_path('CCQ_INPUT_PATH', required=True),
            'output_path': self._get_path('CCQ_OUTPUT_PATH', required=True),
            'taxonomy_path': self._get_path('CCQ_TAXONOMY_PATH', required=True),
            'parsed_facts_path': self._get_path('CCQ_PARSED_FACTS_PATH', required=True),
            
            # CCQ Mapper Paths (optional)
            'mapper_xbrl_path': self._get_path('CCQ_MAPPER_XBRL_PATH', required=False),
            'mapper_output_path': self._get_path('CCQ_MAPPER_OUTPUT_PATH', required=False),
            
            # Unified Mapper Path (fact_authority engine)
            'unified_output_path': self._get_path('CCQ_UNIFIED_OUTPUT_PATH', required=False),
            
            # Log Paths (optional)
            'ccq_logs_path': self._get_path('CCQ_LOG_DIR', required=False),
            'mapper_logs_path': self._get_path('CCQ_MAPPER_LOG_DIR', required=False),
            
            # Map Pro Physical Data Locations (for fallback searches when DB fails)
            'map_pro_entities_path': self._get_path('MAP_PRO_ENTITIES_PATH', required=False),
            'map_pro_parsed_path': self._get_path('MAP_PRO_PARSED_PATH', required=False),
            'map_pro_library_path': self._get_path('MAP_PRO_LIBRARY_PATH', required=False),
            'map_pro_mapped_path': self._get_path('MAP_PRO_MAPPED_PATH', required=False),
            
            # Database - CCQ's own database
            'db_url': self._get_env('CCQ_DB_URL', required=True),
            
            # Map Pro databases - ALL 4 DATABASES for metadata access (file paths, job info)
            'map_pro_core_db_url': self._get_env('CCQ_MAP_PRO_CORE_DB_URL', required=False),
            'map_pro_parsed_db_url': self._get_env('CCQ_MAP_PRO_PARSED_DB_URL', required=False),
            'map_pro_library_db_url': self._get_env('CCQ_MAP_PRO_LIBRARY_DB_URL', required=False),
            'map_pro_mapped_db_url': self._get_env('CCQ_MAP_PRO_MAPPED_DB_URL', required=False),
            'enable_map_pro_db_access': self._get_bool('CCQ_ENABLE_MAP_PRO_DB_ACCESS', True),
            
            # Database Pool
            'db_pool_size': self._get_int('CCQ_DB_POOL_SIZE', 3),
            'db_max_overflow': self._get_int('CCQ_DB_MAX_OVERFLOW', 7),
            'db_pool_timeout': self._get_int('CCQ_DB_POOL_TIMEOUT', 30),
            'db_pool_recycle': self._get_int('CCQ_DB_POOL_RECYCLE', 300),
            'db_pool_pre_ping': self._get_bool('CCQ_DB_POOL_PRE_PING', True),
            
            # Connection Pool Management
            'connection_idle_timeout': self._get_int('CCQ_CONNECTION_IDLE_TIMEOUT', 5),
            'connection_cleanup_enabled': self._get_bool('CCQ_CONNECTION_CLEANUP_ENABLED', True),
            'connection_warning_threshold': self._get_int('CCQ_CONNECTION_WARNING_THRESHOLD', 80),
            
            # Validation Thresholds
            'accounting_equation_tolerance': self._get_float('CCQ_ACCOUNTING_EQUATION_TOLERANCE', 0.00001),
            'cash_reconciliation_tolerance': self._get_float('CCQ_CASH_RECONCILIATION_TOLERANCE', 0.001),
            'subtotal_absolute_tolerance': self._get_float('CCQ_SUBTOTAL_ABSOLUTE_TOLERANCE', 1000.0),
            'retained_earnings_tolerance': self._get_float('CCQ_RETAINED_EARNINGS_TOLERANCE', 0.01),
            'yoy_outlier_threshold': self._get_float('CCQ_YOY_OUTLIER_THRESHOLD', 5.0),
            'extreme_value_multiplier': self._get_float('CCQ_EXTREME_VALUE_MULTIPLIER', 10.0),
            'negative_revenue_tolerance': self._get_float('CCQ_NEGATIVE_REVENUE_TOLERANCE', 0.0),
            
            # Quality Scoring
            'min_confidence_score': self._get_float('CCQ_MIN_CONFIDENCE_SCORE', 70.0),
            'critical_check_weight': self._get_float('CCQ_CRITICAL_CHECK_WEIGHT', 0.50),
            'mandatory_check_weight': self._get_float('CCQ_MANDATORY_CHECK_WEIGHT', 0.30),
            'qualitative_check_weight': self._get_float('CCQ_QUALITATIVE_CHECK_WEIGHT', 0.20),
            
            # Market Configuration
            'default_market': self._get_env('CCQ_DEFAULT_MARKET', 'sec'),
            'enable_market_auto_detection': self._get_bool('CCQ_ENABLE_MARKET_AUTO_DETECTION', True),
            'enable_sec_validation': self._get_bool('CCQ_ENABLE_SEC_VALIDATION', True),
            'enable_fca_validation': self._get_bool('CCQ_ENABLE_FCA_VALIDATION', True),
            'enable_esma_validation': self._get_bool('CCQ_ENABLE_ESMA_VALIDATION', True),
            
            # Normalization Options
            'preserve_original_values': self._get_bool('CCQ_PRESERVE_ORIGINAL_VALUES', True),
            'add_classification_metadata': self._get_bool('CCQ_ADD_CLASSIFICATION_METADATA', True),
            'flag_corrections': self._get_bool('CCQ_FLAG_CORRECTIONS', True),
            'standardize_to_base_units': self._get_bool('CCQ_STANDARDIZE_TO_BASE_UNITS', True),
            'enforce_sign_convention': self._get_bool('CCQ_ENFORCE_SIGN_CONVENTION', True),
            'sign_convention_source': self._get_env('CCQ_SIGN_CONVENTION_SOURCE', 'taxonomy'),
            
            # Processing
            'max_concurrent_validations': self._get_int('CCQ_MAX_CONCURRENT_VALIDATIONS', 5),
            'validation_timeout_seconds': self._get_int('CCQ_VALIDATION_TIMEOUT_SECONDS', 30),
            'job_retry_attempts': self._get_int('CCQ_JOB_RETRY_ATTEMPTS', 3),
            'job_queue_check_interval': self._get_int('CCQ_JOB_QUEUE_CHECK_interval', 5),
            'max_processing_time_seconds': self._get_int('CCQ_MAX_PROCESSING_TIME_SECONDS', 30),
            
            # Taxonomy
            'enable_taxonomy_caching': self._get_bool('CCQ_ENABLE_TAXONOMY_CACHING', True),
            'taxonomy_cache_size_mb': self._get_int('CCQ_TAXONOMY_CACHE_SIZE_MB', 100),
            'taxonomy_cache_ttl_hours': self._get_int('CCQ_TAXONOMY_CACHE_TTL_HOURS', 24),
            'taxonomy_cache_path': self._get_path('CCQ_TAXONOMY_CACHE_PATH', required=False),
            'filings_cache_path': self._get_path('CCQ_FILINGS_CACHE_PATH', required=False),
            
            # Logging
            'log_dir': self._get_path('CCQ_LOG_DIR', required=False),
            'log_format': self._get_env('CCQ_LOG_FORMAT', 'json'),
            'log_rotation': self._get_env('CCQ_LOG_ROTATION', 'daily'),
            'log_retention_days': self._get_int('CCQ_LOG_RETENTION_DAYS', 30),
            'log_max_size_mb': self._get_int('CCQ_LOG_MAX_SIZE_MB', 10),
            'log_backup_count': self._get_int('CCQ_LOG_BACKUP_COUNT', 5),
            
            # Feature Flags
            'enable_vertical_checks': self._get_bool('CCQ_ENABLE_VERTICAL_CHECKS', True),
            'enable_horizontal_checks': self._get_bool('CCQ_ENABLE_HORIZONTAL_CHECKS', True),
            'enable_anomaly_detection': self._get_bool('CCQ_ENABLE_ANOMALY_DETECTION', True),
            'enable_qualitative_checks': self._get_bool('CCQ_ENABLE_QUALITATIVE_CHECKS', True),
            
            # Integration
            'enable_map_pro_integration': self._get_bool('CCQ_ENABLE_MAP_PRO_INTEGRATION', True),
            'map_pro_job_type': self._get_env('CCQ_MAP_PRO_JOB_TYPE', 'validate_statements'),
        }
        
        return config
    
    def _get_env(self, key: str, default: Optional[str] = None, required: bool = False) -> str:
        """
        Get string environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            required: If True, raises ValueError when missing
            
        Returns:
            Environment variable value or default
            
        Raises:
            ValueError: If required and not found
        """
        value = os.getenv(key)
        
        if value is None:
            if required:
                raise ValueError(f"Required environment variable '{key}' is not set")
            return default
        
        return value.strip()
    
    def _get_bool(self, key: str, default: bool) -> bool:
        """
        Get boolean environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            
        Returns:
            Boolean value
        """
        value = os.getenv(key)
        
        if value is None:
            return default
        
        value_lower = value.strip().lower()
        return value_lower in ('true', '1', 'yes', 'on')
    
    def _get_int(self, key: str, default: int) -> int:
        """
        Get integer environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            
        Returns:
            Integer value
            
        Raises:
            ValueError: If value cannot be converted to int
        """
        value = os.getenv(key)
        
        if value is None:
            return default
        
        try:
            return int(value.strip())
        except ValueError as e:
            raise ValueError(f"Environment variable '{key}' must be an integer, got '{value}'") from e
    
    def _get_float(self, key: str, default: float) -> float:
        """
        Get float environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            
        Returns:
            Float value
            
        Raises:
            ValueError: If value cannot be converted to float
        """
        value = os.getenv(key)
        
        if value is None:
            return default
        
        try:
            return float(value.strip())
        except ValueError as e:
            raise ValueError(f"Environment variable '{key}' must be a number, got '{value}'") from e
    
    def _get_path(self, key: str, default: Optional[str] = None, required: bool = False) -> Path:
        """
        Get path environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            required: If True, raises ValueError when missing
            
        Returns:
            Path object
            
        Raises:
            ValueError: If required and not found
        """
        value = self._get_env(key, default, required)
        return Path(value) if value else Path(default)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)
    
    def get_all(self) -> dict[str, Any]:
        """
        Get all configuration as dictionary.
        
        Returns:
            Complete configuration dictionary
        """
        return self._config.copy()
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self._config['environment'] == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self._config['environment'] == 'development'