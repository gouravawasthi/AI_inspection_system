# User Interface package - GUI components and interfaces
"""
User Interface package for the inspection system GUI.

This package provides:
- Main application interface
- Base inspection window class for inheritance
- EOLT inspection window for end-of-line testing
- INLINE inspection window for inline testing (TOP and BOTTOM)
- Configuration and settings panels
- Data visualization and reporting
"""

from .mainwindow import MainWindow
from .base_inspection_window import BaseInspectionWindow
from .eolt_inspection_window import EOLTInspectionWindow
from .inline_inspection_window import INLINEInspectionWindow

__all__ = [
    'MainWindow', 
    'BaseInspectionWindow',
    'EOLTInspectionWindow',
    'INLINEInspectionWindow'
]

# Placeholder for UI modules  
# from .main_window import *
# from .inspection_interface import *
# from .settings_panel import *

__all__ = [
    # Will be populated when UI modules are added
]