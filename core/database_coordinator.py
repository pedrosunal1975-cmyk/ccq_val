"""
Database Coordinator

Manages database connections and provides transactional operations.
Implements connection pooling and automatic retry logic.
"""

from typing import Optional, Any
from contextlib import contextmanager
import logging

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import Pool

from .config_loader import ConfigLoader
from .system_logger import SystemLogger
from shared.exceptions import DatabaseError


class DatabaseCoordinator:
    """
    Centralized database connection manager.
    
    Provides connection pooling, session management, and transactional
    operations with automatic cleanup and error handling.
    """
    
    _instance: Optional['DatabaseCoordinator'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'DatabaseCoordinator':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize database coordinator. Only runs once due to singleton pattern."""
        if DatabaseCoordinator._initialized:
            return
        
        self.config = ConfigLoader()
        self.logger = SystemLogger().get_logger(__name__)
        
        self._engine = None
        self._session_factory = None
        
        self._initialize_engine()
        DatabaseCoordinator._initialized = True
    
    def _initialize_engine(self) -> None:
        """
        Initialize SQLAlchemy engine with connection pooling.
        
        CRITICAL: This is CCQ's OWN database, not Map Pro's.
        CCQ never reads actual financial data from databases.
        
        Raises:
            DatabaseError: If engine initialization fails
        """
        try:
            # CCQ's own database for validation results
            db_url = self.config.get('db_url')
            pool_size = self.config.get('db_pool_size', 3)
            max_overflow = self.config.get('db_max_overflow', 7)
            pool_timeout = self.config.get('db_pool_timeout', 30)
            pool_recycle = self.config.get('db_pool_recycle', 300)
            pool_pre_ping = self.config.get('db_pool_pre_ping', True)
            
            self._engine = create_engine(
                db_url,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=pool_timeout,
                pool_recycle=pool_recycle,
                pool_pre_ping=pool_pre_ping,
                echo=self.config.get('debug', False),
            )
            
            # Register connection pool listeners for monitoring
            event.listen(Pool, 'connect', self._on_connect)
            event.listen(Pool, 'checkout', self._on_checkout)
            
            # Create session factory
            self._session_factory = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False,
            )
            
            self.logger.info("CCQ database engine initialized successfully (own database)")
            
        except Exception as e:
            error_msg = f"Failed to initialize database engine: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e
    
    def _on_connect(self, dbapi_conn: Any, connection_record: Any) -> None:
        """
        Called when a new database connection is created.
        
        Args:
            dbapi_conn: Raw database connection
            connection_record: SQLAlchemy connection record
        """
        self.logger.debug("New database connection established")
    
    def _on_checkout(self, dbapi_conn: Any, connection_record: Any, connection_proxy: Any) -> None:
        """
        Called when a connection is retrieved from the pool.
        
        Args:
            dbapi_conn: Raw database connection
            connection_record: SQLAlchemy connection record
            connection_proxy: Connection proxy object
        """
        self.logger.debug("Connection checked out from pool")
    
    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions.
        
        Provides automatic session lifecycle management with
        commit on success and rollback on error.
        
        Yields:
            SQLAlchemy Session object
            
        Example:
            with db_coordinator.get_session() as session:
                result = session.query(Model).first()
        """
        if not self._session_factory:
            raise DatabaseError("Database not initialized")
        
        session = self._session_factory()
        
        try:
            yield session
            session.commit()
            self.logger.debug("Database session committed successfully")
        except Exception as e:
            session.rollback()
            self.logger.error(f"Database session rolled back due to error: {str(e)}")
            raise DatabaseError(f"Database operation failed: {str(e)}") from e
        finally:
            session.close()
            self.logger.debug("Database session closed")
    
    def execute_query(self, query: str, params: Optional[dict] = None) -> Any:
        """
        Execute raw SQL query with parameters.
        
        Args:
            query: SQL query string
            params: Query parameters dictionary
            
        Returns:
            Query result
            
        Raises:
            DatabaseError: If query execution fails
        """
        with self.get_session() as session:
            try:
                result = session.execute(text(query), params or {})
                return result
            except Exception as e:
                raise DatabaseError(f"Query execution failed: {str(e)}") from e
    
    def test_connection(self) -> bool:
        """
        Test database connectivity.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            self.logger.info("Database connection test successful")
            return True
        except Exception as e:
            self.logger.error(f"Database connection test failed: {str(e)}")
            return False
    
    def close(self) -> None:
        """
        Close database engine and dispose of connection pool.
        
        Should be called during application shutdown.
        """
        if self._engine:
            self._engine.dispose()
            self.logger.info("Database connections closed")