# File: engines/fact_authority/input/__init__.py
# Path: engines/fact_authority/input/__init__.py

"""
Fact Authority Input Components
================================

Components for loading data and accepting user input.

Components:
    - run_authority: Interactive CLI for filing selection
    - statement_loader: Loads mapped statements from both mappers
"""

from engines.fact_authority.input.statement_loader import StatementLoader

__all__ = [
    'StatementLoader',
]