"""
CCQ Validation Tests
====================

Test suite for validating mapper consistency and coverage.
"""

import sys
from pathlib import Path

# Add parent directory to Python path so we can import core modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))