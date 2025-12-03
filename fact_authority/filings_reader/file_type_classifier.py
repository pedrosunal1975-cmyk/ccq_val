# File: file_type_classifier.py
# Location: engines/fact_authority/filings_reader/file_type_classifier.py

"""
File Type Classifier
====================

Intelligently classifies files in company XBRL filings.

Distinguishes between:
- Extension schema files (company-YYYY.xsd)
- Linkbase files (_pre.xml, _cal.xml, _def.xml, _lab.xml)
- Instance documents (.xml, .xhtml for iXBRL)
- Standard taxonomy files (us-gaap, ifrs, etc.)
- Useless files (images, PDFs, etc.)

Uses hints from parsed_facts.json to improve accuracy.

Classes:
    FileTypeClassifier: Classifies filing files by type and purpose
"""

from pathlib import Path
from typing import Optional, Dict, Set
import re
import logging


logger = logging.getLogger(__name__)


class FileTypeClassifier:
    """
    Classifies files in company XBRL filings by type and purpose.
    
    Uses intelligent pattern matching with hints from parsed_facts.json
    to accurately identify extension schemas, linkbases, instance documents,
    and useless files.
    
    Key features:
    - Pattern-based classification
    - Namespace-aware (uses hints)
    - Distinguishes extensions from standard taxonomies
    - Filters useless files
    """
    
    # Standard taxonomy namespaces (NOT extensions)
    STANDARD_TAXONOMIES = {
        'us-gaap', 'ifrs', 'ifrs-full', 'dei', 'country',
        'currency', 'exch', 'naics', 'sic', 'stpr', 'invest'
    }
    
    # XBRL file patterns
    EXTENSION_SCHEMA_PATTERN = r'^([a-z]{2,10})-(\d{4})\.xsd$'
    PRESENTATION_PATTERN = r'_pre\.xml$'
    CALCULATION_PATTERN = r'_cal\.xml$'
    DEFINITION_PATTERN = r'_def\.xml$'
    LABEL_PATTERN = r'_lab\.xml$'
    INSTANCE_XML_PATTERN = r'-(\d{8})\.xml$'
    INSTANCE_IXBRL_PATTERN = r'\.xhtml$'
    
    # Useless file extensions
    USELESS_EXTENSIONS = {
        # Images
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico',
        # Documents
        '.pdf', '.txt', '.doc', '.docx',
        # Web support files (NOT .htm/.html which can be iXBRL)
        '.css', '.js',
        # Archives
        '.zip', '.gz', '.tar', '.rar',
        # Excel/Spreadsheets
        '.xls', '.xlsx', '.xlsm', '.csv',
        # Other
        '.json', '.log', '.md', '.readme'
    }
    
    def __init__(self):
        """Initialize file type classifier."""
        self.hints = {}
    
    def set_hints(self, hints: Dict[str, any]):
        """
        Set classification hints from parsed_facts.json.
        
        Args:
            hints: Dictionary with:
                - company_namespace: Company extension namespace
                - year: Taxonomy year
                - expected_files: List of expected filenames
        """
        self.hints = hints
    
    def classify(self, file_path: Path) -> str:
        """
        Classify a file by type.
        
        Args:
            file_path: Path to file
            
        Returns:
            Classification: 'extension_schema', 'presentation', 'calculation',
            'definition', 'label', 'instance_xml', 'instance_ixbrl',
            'standard_taxonomy', 'useless', or 'unknown'
        """
        filename = file_path.name.lower()
        
        # Check if useless first (quick filter)
        if self._is_useless(file_path):
            return 'useless'
        
        # Check XBRL file types
        if filename.endswith('.xsd'):
            return self._classify_schema(file_path)
        
        elif filename.endswith('.xml'):
            return self._classify_xml(file_path)
        
        elif filename.endswith('.xhtml'):
            return 'instance_ixbrl'
        
        # Check if .htm/.html contains iXBRL content (market-agnostic)
        elif filename.endswith(('.htm', '.html')):
            return self._classify_html(file_path)
        
        return 'unknown'
    
    def _classify_html(self, file_path: Path) -> str:
        """
        Classify .htm/.html file by checking content for iXBRL markers.
        
        Market-agnostic approach: checks file content rather than filename patterns.
        
        Args:
            file_path: Path to .htm/.html file
            
        Returns:
            'instance_ixbrl' if contains XBRL content, 'useless' otherwise
        """
        try:
            # Read first 5000 bytes to check for XBRL/iXBRL markers
            with open(file_path, 'rb') as f:
                header = f.read(5000).decode('utf-8', errors='ignore').lower()
            
            # Check for iXBRL namespace (definitive marker)
            if 'http://www.xbrl.org/2013/inlinexbrl' in header:
                return 'instance_ixbrl'
            
            # Check for XBRL instance namespace
            if 'http://www.xbrl.org/2003/instance' in header:
                return 'instance_ixbrl'
            
            # Check for ix: prefix usage (inline XBRL elements)
            if 'xmlns:ix=' in header or '<ix:' in header:
                return 'instance_ixbrl'
            
            # Not XBRL content
            return 'useless'
            
        except Exception:
            # If we can't read the file, treat as useless
            return 'useless'
    
    def _is_useless(self, file_path: Path) -> bool:
        """
        Check if file is useless (not XBRL-related).
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file should be ignored
        """
        suffix = file_path.suffix.lower()
        return suffix in self.USELESS_EXTENSIONS
    
    def _classify_schema(self, file_path: Path) -> str:
        """
        Classify .xsd schema file.
        
        UNIVERSAL LOGIC (NO PATTERNS):
        - If filename contains standard taxonomy name → standard_taxonomy
        - Otherwise → extension_schema
        
        Works for ANY naming convention: company-YYYY.xsd, company-YYYYMMDD.xsd,
        company_schema.xsd, CompanyExtension.xsd, ANYTHING.
        
        Args:
            file_path: Path to .xsd file
            
        Returns:
            'extension_schema' or 'standard_taxonomy'
        """
        filename = file_path.name.lower()
        
        # Check if it's a standard taxonomy
        for standard in self.STANDARD_TAXONOMIES:
            if standard in filename:
                return 'standard_taxonomy'
        
        # If it's NOT a standard taxonomy, it MUST be an extension
        return 'extension_schema'
    
    def _classify_xml(self, file_path: Path) -> str:
        """
        Classify .xml file.
        
        Args:
            file_path: Path to .xml file
            
        Returns:
            Classification type
        """
        filename = file_path.name
        
        # Check linkbase patterns
        if re.search(self.PRESENTATION_PATTERN, filename):
            return 'presentation'
        
        if re.search(self.CALCULATION_PATTERN, filename):
            return 'calculation'
        
        if re.search(self.DEFINITION_PATTERN, filename):
            return 'definition'
        
        if re.search(self.LABEL_PATTERN, filename):
            return 'label'
        
        # Check if instance document (has date in filename)
        if re.search(self.INSTANCE_XML_PATTERN, filename):
            return 'instance_xml'
        
        return 'unknown'
    
    def is_extension_file(self, file_path: Path) -> bool:
        """
        Check if file is part of company extension taxonomy.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file is extension-related
        """
        classification = self.classify(file_path)
        
        # Extension files include schema and all linkbases
        extension_types = {
            'extension_schema',
            'presentation',
            'calculation',
            'definition',
            'label'
        }
        
        if classification in extension_types:
            # Further check: filename should contain company namespace
            if self.hints:
                company_ns = self.hints.get('company_namespace', '')
                if company_ns and company_ns in file_path.name.lower():
                    return True
            
            # If no hints, classify based on pattern
            return classification == 'extension_schema'
        
        return False
    
    def is_xbrl_file(self, file_path: Path) -> bool:
        """
        Check if file is XBRL-related (not useless).
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file is XBRL-related
        """
        classification = self.classify(file_path)
        return classification not in ['useless', 'unknown']
    
    def get_statistics(self, file_paths: list) -> Dict[str, int]:
        """
        Get classification statistics for a list of files.
        
        Args:
            file_paths: List of file paths
            
        Returns:
            Dictionary with counts by type
        """
        stats = {
            'extension_schema': 0,
            'presentation': 0,
            'calculation': 0,
            'definition': 0,
            'label': 0,
            'instance_xml': 0,
            'instance_ixbrl': 0,
            'standard_taxonomy': 0,
            'useless': 0,
            'unknown': 0
        }
        
        for file_path in file_paths:
            classification = self.classify(file_path)
            if classification in stats:
                stats[classification] += 1
        
        return stats