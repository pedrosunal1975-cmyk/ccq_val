# File: tests/test_null_quality_quick.py
# Test: Quick NullQualityHandler test
# Run from project root: python tests/test_null_quality_quick.py

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
from dotenv import load_dotenv
load_dotenv()

from core.config_loader import ConfigLoader
from core.data_paths import CCQPaths
from engines.fact_authority.process import NullQualityHandler

def main():
    print("Testing NullQualityHandler...")
    config = ConfigLoader()
    ccq_paths = CCQPaths.from_config(config)
    handler = NullQualityHandler(ccq_paths)
    
    # Mock data
    mock_mp = {'metadata': {'null_facts': [{'concept_qname': 'us-gaap:Test'}]}}
    mock_ccq = {'metadata': {'null_facts': [{'concept_qname': 'us-gaap:Test'}]}}
    
    result = handler.analyze_from_statements(mock_mp, mock_ccq)
    print(f"  Map Pro nulls: {result['map_pro_null_count']}")
    print(f"  CCQ nulls: {result['ccq_null_count']}")
    print(f"  Common: {len(result['common_null_concepts'])}")
    print("✓ NullQualityHandler OK")
    return 0

if __name__ == '__main__':
    sys.exit(main())