# File: tests/test_extension_tracer_quick.py
# Test: Quick ExtensionInheritanceTracer test
# Run from project root: python tests/test_extension_tracer_quick.py

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
from dotenv import load_dotenv
load_dotenv()

from core.config_loader import ConfigLoader
from core.data_paths import CCQPaths
from engines.fact_authority.process import ExtensionInheritanceTracer

def main():
    print("Testing ExtensionInheritanceTracer...")
    config = ConfigLoader()
    ccq_paths = CCQPaths(
        data_root=config.get('data_root'),
        input_path=config.get('input_path'),
        output_path=config.get('output_path'),
        taxonomy_path=config.get('taxonomy_path'),
        parsed_facts_path=config.get('parsed_facts_path'),
        mapper_xbrl_path=config.get('mapper_xbrl_path'),
        mapper_output_path=config.get('mapper_output_path'),
        unified_output_path=config.get('unified_output_path')
    )
    tracer = ExtensionInheritanceTracer(ccq_paths)
    
    # Mock filing with extension
    mock_filing = {
        'extension_schema': {
            'concepts': {
                'aci:CustomRevenue': {
                    'type': 'monetary',
                    'substitutionGroup': 'us-gaap:Revenue'
                }
            }
        }
    }
    
    mock_taxonomy = {'concepts': {}}
    
    result = tracer.trace_extensions(mock_filing, mock_taxonomy)
    print(f"  Extensions found: {result['statistics']['total_extensions']}")
    print(f"  Mapped to base: {result['statistics']['mapped_to_base']}")
    print("✓ ExtensionInheritanceTracer structure OK")
    print("⚠ Needs taxonomy integration for validation")
    return 0

if __name__ == '__main__':
    sys.exit(main())