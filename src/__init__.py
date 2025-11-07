# Main source package - Core AI inspection system components
"""
Main source package containing all core components of the AI inspection system.

Sub-packages:
- api: Workflow management and API interaction
- server: Flask REST API server for database operations
- data: Data management and database utilities
- camera: Camera interface and image capture
- image_processing: Image analysis and processing algorithms
- ml: Machine learning models and inference
- ui: User interface components
"""

from . import api
from . import server
from . import data

__all__ = [
    'api',
    'server', 
    'data',
]

# Import main classes for convenience
from .api import APIManager, API_ENDPOINTS, INSPECTION_WORKFLOWS
from .server import configure_database, start_server, VALID_TABLES

# Make commonly used items available at package level
__all__.extend([
    'APIManager',
    'API_ENDPOINTS',
    'INSPECTION_WORKFLOWS', 
    'configure_database',
    'start_server',
    'VALID_TABLES',
])