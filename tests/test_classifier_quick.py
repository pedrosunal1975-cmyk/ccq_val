# File: tests/test_classifier_quick.py
# Test: Quick StatementClassifier test
# Run from project root: python tests/test_classifier_quick.py

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engines.fact_authority.process import StatementClassifier

def main():
    print("Testing StatementClassifier...")
    classifier = StatementClassifier({'concepts': {}})
    
    # Should handle unknown concepts gracefully
    result = classifier.classify_concept('us-gaap:Assets')
    print(f"  Classification result: {result} (expected None with empty taxonomy)")
    
    # Should validate placement
    validation = classifier.validate_placement('us-gaap:Assets', 'balance_sheet')
    print(f"  Validation: {validation['is_valid']} - {validation['reason']}")
    
    print("✓ StatementClassifier structure OK")
    print("⚠ Needs taxonomy integration for full function")
    return 0

if __name__ == '__main__':
    sys.exit(main())