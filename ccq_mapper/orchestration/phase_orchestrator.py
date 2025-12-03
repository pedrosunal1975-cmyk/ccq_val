# File: engines/ccq_mapper/orchestration/phase_orchestrator.py

"""
Phase Orchestrator
==================

Orchestrates the execution of all mapping phases with proper timing,
logging, and error handling.

Responsibility:
- Coordinate phase execution
- Track phase timing
- Handle phase-level errors
- Delegate to specialized processors
"""

from typing import Dict, Any, List, Tuple
from pathlib import Path
import time

from core.system_logger import get_logger
from ..reporting.mapper_logger import get_mapper_logger

logger = get_logger(__name__)


class PhaseOrchestrator:
    """Orchestrates mapping phases with timing and logging."""
    
    def __init__(self, filing_id: str):
        """
        Initialize phase orchestrator.
        
        Args:
            filing_id: Filing identifier for logging
        """
        self.filing_id = filing_id
        self.mapper_logger = get_mapper_logger(filing_id=filing_id)
        self.phase_timings = {}
    
    def execute_phase(
        self,
        phase_name: str,
        phase_callable: callable,
        **kwargs
    ) -> Any:
        """
        Execute a single phase with timing and logging.
        
        Args:
            phase_name: Name of the phase
            phase_callable: Function to execute
            **kwargs: Additional logging metrics
            
        Returns:
            Result from phase execution
        """
        self.mapper_logger.log_phase_start(phase_name, filing_id=self.filing_id)
        phase_start = time.time()
        
        try:
            result = phase_callable()
            phase_duration = time.time() - phase_start
            self.phase_timings[phase_name] = phase_duration
            
            # Filter out non-serializable objects (functions, callables, etc.)
            safe_kwargs = {
                k: v for k, v in kwargs.items() 
                if not callable(v) and not hasattr(v, '__call__')
            }
            
            self.mapper_logger.log_phase_complete(
                phase_name,
                phase_duration,
                **safe_kwargs
            )
            
            return result
            
        except Exception as e:
            phase_duration = time.time() - phase_start
            self.phase_timings[phase_name] = phase_duration
            self.mapper_logger.log_error(e, phase=phase_name)
            raise
    
    def get_total_duration(self) -> float:
        """Get total duration across all phases."""
        return sum(self.phase_timings.values())
    
    def get_phase_timings(self) -> Dict[str, float]:
        """Get all phase timings."""
        return self.phase_timings.copy()


__all__ = ['PhaseOrchestrator']