#!/usr/bin/env python3
"""
Build script for AI Inspection System
Creates executable using PyInstaller with proper configuration management
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Build configuration
APP_NAME = "AI_Inspection_System"
MAIN_SCRIPT = "main.py"

def build_executable():
    """Build the application into executable"""
    
    print(f"Building {APP_NAME}...")
    
    # Clean previous builds
    for dir_name in ["build", "dist", "__pycache__"]:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"Cleaned {dir_name}/")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--name", APP_NAME,
        "--onefile",                    # Single executable
        "--console",                    # Keep console window
        "--clean",                      # Clean cache
        "--noconfirm",                  # Overwrite without confirmation
        
        # Include data files
        "--add-data", f"configs{os.pathsep}configs",
        "--add-data", f"data{os.pathsep}data", 
        "--add-data", f"src{os.pathsep}src",
        
        # Hidden imports
        "--hidden-import", "sqlite3",
        "--hidden-import", "flask",
        "--hidden-import", "requests",
        "--hidden-import", "configparser",
        "--hidden-import", "json",
        "--hidden-import", "pathlib", 
        "--hidden-import", "logging",
        "--hidden-import", "threading",
        
        # Exclude unnecessary modules
        "--exclude-module", "tkinter",
        "--exclude-module", "matplotlib",
        "--exclude-module", "numpy.testing",
        
        # Main script
        MAIN_SCRIPT
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Build successful!")
        print(f"Executable created: dist/{APP_NAME}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def create_deployment_package():
    """Create deployment package with configs"""
    
    if not Path("dist").exists():
        print("No dist directory found. Run build first.")
        return False
    
    package_dir = Path("deployment_package")
    
    # Clean and create package directory
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()
    
    # Copy executable
    executable_name = f"{APP_NAME}.exe" if sys.platform == "win32" else APP_NAME
    shutil.copy2(f"dist/{executable_name}", package_dir / executable_name)
    
    # Copy configuration templates
    config_template_dir = package_dir / "configs_template"
    shutil.copytree("configs", config_template_dir)
    
    # Create user directories
    (package_dir / "user_configs").mkdir()
    (package_dir / "logs").mkdir() 
    (package_dir / "data" / "db").mkdir(parents=True)
    
    # Copy sample database if exists
    if Path("data/db/inspection_data.db").exists():
        shutil.copy2("data/db/inspection_data.db", package_dir / "data" / "db" / "sample_inspection_data.db")
    
    # Create README for deployment
    readme_content = f"""# {APP_NAME} Deployment Package

## Setup Instructions:

1. Copy configuration templates:
   - Copy `configs_template/*` to `user_configs/`
   - Modify `user_configs/app_config.json` for your environment
   - Update `user_configs/database_schema.json` if needed
   - Customize `user_configs/inspection_workflows.json` for your workflows

2. Database Setup:
   - Place your database in `data/db/inspection_data.db`
   - Or use the sample database provided

3. Run the application:
   - Execute `./{executable_name}`
   - The application will look for configs in `user_configs/` first, then `configs_template/`

## Configuration:

### Server Configuration (app_config.json):
```json
{{
  "server": {{
    "host": "127.0.0.1",
    "port": 5001
  }},
  "database": {{
    "path": "data/db/inspection_data.db"
  }}
}}
```

### Adding New Tables (database_schema.json):
```json
[
  {{
    "name": "NEW_TABLE",
    "columns": ["Barcode", "DT", "Field1", "Field2"],
    "primary_key": "Barcode",
    "timestamp_column": "DT"
  }}
]
```

### Custom Workflows (inspection_workflows.json):
```json
[
  {{
    "name": "CUSTOM_WORKFLOW",
    "api1_table": "TABLE1",
    "api2_table": "TABLE2", 
    "description": "Custom inspection workflow",
    "enabled": true
  }}
]
```

## Logs:
- Application logs: `logs/ai_inspection_system.log`
- Server access logs: Console output

## Support:
Contact: {os.environ.get('SUPPORT_EMAIL', 'support@example.com')}
Version: 1.0.0
"""
    
    with open(package_dir / "README.txt", "w") as f:
        f.write(readme_content)
    
    print(f"Deployment package created: {package_dir}")
    return True

if __name__ == "__main__":
    print("AI Inspection System Build Script")
    print("=" * 40)
    
    if "--package-only" in sys.argv:
        create_deployment_package()
    else:
        if build_executable():
            create_deployment_package()
        else:
            sys.exit(1)