# API package - Main interface for inspection workflow management
"""
API Manager package for handling inspection workflows and database interactions.

This package provides:
- APIManager class for managing inspection workflows
- API endpoint constants and configurations
- Workflow patterns for different inspection types
"""

from .api_manager import (
    # Main class
    APIManager,
    
    # Constants
    API_BASE_URL,
    API_ENDPOINTS,
    INSPECTION_WORKFLOWS,
)

__all__ = [
    'APIManager',
    'API_BASE_URL', 
    'API_ENDPOINTS',
    'INSPECTION_WORKFLOWS',
]