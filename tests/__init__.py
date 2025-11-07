# Tests package - Test scripts and utilities
"""
Tests package containing all test scripts for the AI inspection system.

This package provides:
- API testing scripts
- Database operation tests
- Workflow validation tests
- Debug and troubleshooting utilities
"""

# Test modules are meant to be run directly, not imported
# But we can make them discoverable for test runners

__all__ = [
    # Test scripts - run directly, not imported
    'test_api',
    'test_latest_records', 
    'test_manual_result',
    'debug_api',
    'debug_manual_result',
    'quick_test',
]