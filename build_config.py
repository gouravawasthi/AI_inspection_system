# Build specification for PyInstaller
# This file configures how to package the application into an executable

"""
PyInstaller Build Configuration
"""

import os
import sys
from pathlib import Path

# Application metadata
APP_NAME = "AI_Inspection_System"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Taisys"
APP_DESCRIPTION = "AI-powered Visual Defect Inspection System"

# Build configuration
BUILD_CONFIG = {
    # Main script
    "entry_point": "main.py",
    
    # Build options
    "onefile": True,  # Create single executable
    "console": True,  # Show console window
    "icon": None,     # Path to icon file
    
    # Data files to include
    "datas": [
        ("configs", "configs"),           # Configuration files
        ("data", "data"),                 # Database and data files  
        ("brand_images", "brand_images"), # Brand assets
        ("src", "src"),                   # Source code (if needed)
    ],
    
    # Hidden imports (modules not detected automatically)
    "hiddenimports": [
        "sqlite3",
        "flask",
        "requests", 
        "configparser",
        "json",
        "pathlib",
        "logging",
    ],
    
    # Exclude unnecessary modules
    "excludes": [
        "tkinter",
        "matplotlib",
        "numpy.testing",
        "pandas.tests",
    ],
    
    # Runtime hooks
    "runtime_hooks": [],
    
    # Additional options
    "noarchive": False,
    "optimize": 2,
    "strip": False,
    "upx": False,  # UPX compression
    "clean": True,
}

# Build script template
BUILD_SCRIPT = f"""
# PyInstaller build script for {APP_NAME}
# Run: python build.py

import PyInstaller.__main__
import shutil
import os
from pathlib import Path

def build_app():
    args = [
        '--name={APP_NAME}',
        '--onefile' if {BUILD_CONFIG['onefile']} else '--onedir',
        {'--console' if BUILD_CONFIG['console'] else '--windowed'},
        '--clean',
        '--noconfirm',
    ]
    
    # Add data files
    for src, dst in {BUILD_CONFIG['datas']}:
        args.append(f'--add-data={{src}}{{os.pathsep}}{{dst}}')
    
    # Add hidden imports
    for module in {BUILD_CONFIG['hiddenimports']}:
        args.append(f'--hidden-import={{module}}')
    
    # Add excludes
    for module in {BUILD_CONFIG['excludes']}:
        args.append(f'--exclude-module={{module}}')
    
    # Entry point
    args.append('{BUILD_CONFIG['entry_point']}')
    
    print(f"Building {{APP_NAME}} v{APP_VERSION}")
    print(f"PyInstaller args: {{' '.join(args)}}")
    
    # Run PyInstaller
    PyInstaller.__main__.run(args)
    
    print(f"Build complete! Executable: dist/{APP_NAME}")

if __name__ == "__main__":
    build_app()
"""

# Deployment configuration
DEPLOYMENT_CONFIG = {
    "target_platforms": ["windows", "linux", "macos"],
    "python_version": "3.9+",
    "dependencies_file": "requirements.txt",
    "config_template_dir": "configs_template",
    "user_data_dir": "user_data",
    "logs_dir": "logs",
}

# External configuration paths (relative to executable)
RUNTIME_PATHS = {
    "config_dir": "./configs",
    "user_config": "./user_configs", 
    "database_dir": "./data/db",
    "logs_dir": "./logs",
    "temp_dir": "./temp",
}