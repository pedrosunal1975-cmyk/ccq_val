# File: filing_validator.py
# Location: engines/fact_authority/filings_reader/filing_validator.py

"""
Filing Validator
================

Validates completeness and accessibility of company XBRL filings.

Checks:
- All discovered files are accessible
- Required files are present (extension schema, linkbases)
- File integrity (readable, valid size)
- Completeness based on hints

Provides validation status for FilingProfile.

Classes:
    FilingValidator: Validates filing completeness and accessibility
"""

from pathlib import Path
from typing import Dict, List, Optional
import logging


logger = logging.getLogger(__name__)


class FilingValidator:
    """
    Validates company XBRL filing completeness and accessibility.
    
    Performs validation checks:
    - File accessibility (can read files)
    - Required files present (extension schema)
    - Linkbase completeness
    - File integrity
    
    Returns validation results for FilingProfile.
    """
    
    # Required file types for complete filing
    REQUIRED_TYPES = {
        'extension_schema',
    }
    
    # Recommended file types (not required, but expected)
    RECOMMENDED_TYPES = {
        'presentation',
        'calculation',
        'definition',
        'label',
    }
    
    def __init__(self):
        """Initialize filing validator."""
        pass
    
    def validate(
        self,
        discovered_files: Dict[str, List[Path]],
        hints: Optional[Dict[str, any]] = None
    ) -> Dict[str, any]:
        """
        Validate discovered filing files.
        
        Args:
            discovered_files: Dictionary from FilingDiscoverer.discover()
            hints: Optional hints for validation
            
        Returns:
            Validation results:
            {
                'all_files_accessible': True/False,
                'schema_valid': True/False,
                'linkbases_complete': True/False,
                'required_files_present': True/False,
                'errors': [list of error messages],
                'warnings': [list of warning messages],
                'summary': 'Complete', 'Incomplete', or 'Invalid'
            }
        """
        results = {
            'all_files_accessible': True,
            'schema_valid': False,
            'linkbases_complete': False,
            'required_files_present': False,
            'errors': [],
            'warnings': [],
            'summary': 'Unknown'
        }
        
        # Check if any files were discovered
        total_files = sum(len(files) for key, files in discovered_files.items() 
                         if key != 'useless')
        
        if total_files == 0:
            results['errors'].append("No XBRL files discovered")
            results['summary'] = 'Invalid'
            results['all_files_accessible'] = False
            return results
        
        # Validate required files
        required_check = self._check_required_files(discovered_files)
        results['required_files_present'] = required_check['passed']
        results['errors'].extend(required_check['errors'])
        results['warnings'].extend(required_check['warnings'])
        
        # Validate extension schema
        schema_check = self._check_extension_schema(discovered_files)
        results['schema_valid'] = schema_check['passed']
        results['errors'].extend(schema_check['errors'])
        results['warnings'].extend(schema_check['warnings'])
        
        # Validate linkbases
        linkbase_check = self._check_linkbases(discovered_files)
        results['linkbases_complete'] = linkbase_check['passed']
        results['warnings'].extend(linkbase_check['warnings'])
        
        # Check file accessibility
        accessibility_check = self._check_accessibility(discovered_files)
        results['all_files_accessible'] = accessibility_check['passed']
        results['errors'].extend(accessibility_check['errors'])
        
        # Determine summary
        if results['errors']:
            results['summary'] = 'Invalid'
        elif not results['required_files_present']:
            results['summary'] = 'Incomplete'
        elif results['warnings']:
            results['summary'] = 'Complete (with warnings)'
        else:
            results['summary'] = 'Complete'
        
        logger.info(f"Validation summary: {results['summary']}")
        
        return results
    
    def _check_required_files(
        self,
        discovered_files: Dict[str, List[Path]]
    ) -> Dict[str, any]:
        """
        Check if required files are present.
        
        Args:
            discovered_files: Discovered files dictionary
            
        Returns:
            Check results with errors/warnings
        """
        results = {
            'passed': True,
            'errors': [],
            'warnings': []
        }
        
        # Check extension schema
        if not discovered_files.get('extension_schema'):
            results['errors'].append("Extension schema not found")
            results['passed'] = False
        
        return results
    
    def _check_extension_schema(
        self,
        discovered_files: Dict[str, List[Path]]
    ) -> Dict[str, any]:
        """
        Validate extension schema file.
        
        Args:
            discovered_files: Discovered files dictionary
            
        Returns:
            Check results
        """
        results = {
            'passed': False,
            'errors': [],
            'warnings': []
        }
        
        schemas = discovered_files.get('extension_schema', [])
        
        if not schemas:
            results['errors'].append("No extension schema found")
            return results
        
        if len(schemas) > 1:
            results['warnings'].append(
                f"Multiple extension schemas found: {len(schemas)}"
            )
        
        # Validate first schema
        schema = schemas[0]
        
        if not schema.exists():
            results['errors'].append(f"Extension schema not accessible: {schema}")
            return results
        
        if not schema.is_file():
            results['errors'].append(f"Extension schema is not a file: {schema}")
            return results
        
        # Check if file is readable
        try:
            with open(schema, 'r', encoding='utf-8') as f:
                f.read(100)  # Read first 100 bytes
            results['passed'] = True
        except Exception as e:
            results['errors'].append(f"Cannot read extension schema: {e}")
        
        return results
    
    def _check_linkbases(
        self,
        discovered_files: Dict[str, List[Path]]
    ) -> Dict[str, any]:
        """
        Check linkbase completeness.
        
        Args:
            discovered_files: Discovered files dictionary
            
        Returns:
            Check results
        """
        results = {
            'passed': False,
            'warnings': []
        }
        
        # Check for recommended linkbases
        has_presentation = bool(discovered_files.get('presentation'))
        has_calculation = bool(discovered_files.get('calculation'))
        has_definition = bool(discovered_files.get('definition'))
        has_label = bool(discovered_files.get('label'))
        
        missing = []
        if not has_presentation:
            missing.append('presentation')
        if not has_calculation:
            missing.append('calculation')
        if not has_definition:
            missing.append('definition')
        if not has_label:
            missing.append('label')
        
        if missing:
            results['warnings'].append(
                f"Missing recommended linkbases: {', '.join(missing)}"
            )
        else:
            results['passed'] = True
        
        return results
    
    def _check_accessibility(
        self,
        discovered_files: Dict[str, List[Path]]
    ) -> Dict[str, any]:
        """
        Check if all files are accessible.
        
        Args:
            discovered_files: Discovered files dictionary
            
        Returns:
            Check results
        """
        results = {
            'passed': True,
            'errors': []
        }
        
        # Check each file type
        for file_type, files in discovered_files.items():
            if file_type == 'useless':
                continue
            
            for file_path in files:
                if not file_path.exists():
                    results['errors'].append(
                        f"{file_type}: File not found: {file_path}"
                    )
                    results['passed'] = False
                
                elif not file_path.is_file():
                    results['errors'].append(
                        f"{file_type}: Not a file: {file_path}"
                    )
                    results['passed'] = False
        
        return results
    
    def validate_single_file(self, file_path: Path) -> bool:
        """
        Quick validation of a single file.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file is valid and accessible
        """
        if not file_path.exists():
            return False
        
        if not file_path.is_file():
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(100)
            return True
        except Exception:
            return False