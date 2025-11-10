# AI Inspection System - Deployment Guide

## Overview

This guide explains how to package the AI Inspection System into a standalone executable with flexible configuration management for different deployment environments.

## Architecture for Deployment

### 1. Configuration Management

The system uses a multi-tier configuration approach:

```
user_configs/           # User-specific configs (highest priority)
├── app_config.json     # Server, database, API settings
├── database_schema.json # Table schemas and structures  
└── inspection_workflows.json # Custom workflows

configs_template/       # Default templates (fallback)
├── app_config.json
├── database_schema.json
└── inspection_workflows.json
```

### 2. Flexible Schema Management

**Adding New Tables:**
```json
// In database_schema.json
{
  "name": "NEW_INSPECTION_TABLE",
  "columns": ["Barcode", "DT", "CustomField1", "CustomField2", "ManualResult"],
  "primary_key": "Barcode", 
  "timestamp_column": "DT"
}
```

**Custom Workflows:**
```json
// In inspection_workflows.json
{
  "name": "CUSTOM_WORKFLOW",
  "api1_table": "TABLE1",
  "api2_table": "TABLE2",
  "description": "Custom inspection process",
  "enabled": true
}
```

### 3. Runtime Configuration Updates

The system supports runtime configuration changes:

```python
# Update server port
config_manager.update_config({"server.port": 8080})

# Update database path
config_manager.update_config({"database.path": "custom/path/db.sqlite"})

# Add new workflow
new_workflow = {
  "name": "NEW_WORKFLOW",
  "api1_table": "SOURCE_TABLE", 
  "api2_table": "TARGET_TABLE",
  "enabled": True
}
config.workflows.append(InspectionWorkflow(**new_workflow))
```

## Building Executable

### Prerequisites

```bash
pip install PyInstaller>=5.0.0
pip install -r requirements_minimal.txt
```

### Build Process

1. **Standard Build:**
```bash
python build.py
```

2. **Custom Build Options:**
```bash
# Build without database files
python build.py --no-data

# Build with specific icon
python build.py --icon=app_icon.ico

# Debug build with console
python build.py --debug
```

### Build Configuration

Edit `build.py` to customize:

```python
BUILD_CONFIG = {
    "onefile": True,           # Single .exe file
    "console": True,           # Show console window
    "icon": "app_icon.ico",   # Application icon
    "datas": [                # Files to include
        ("configs", "configs"),
        ("data", "data"),
    ],
    "hiddenimports": [        # Modules to force include
        "sqlite3", "flask", "requests"
    ],
    "excludes": [             # Modules to exclude
        "tkinter", "matplotlib"
    ]
}
```

## Deployment Package Structure

```
deployment_package/
├── AI_Inspection_System.exe    # Main executable
├── user_configs/               # User configuration directory
│   ├── app_config.json        # Customize for environment
│   ├── database_schema.json   # Add/modify tables
│   └── inspection_workflows.json # Custom workflows
├── configs_template/           # Default templates
├── data/
│   └── db/
│       └── sample_inspection_data.db
├── logs/                       # Application logs
└── README.txt                  # Setup instructions
```

## Configuration Examples

### 1. Production Server Setup

```json
// user_configs/app_config.json
{
  "server": {
    "host": "0.0.0.0",         // Accept external connections
    "port": 8080,              // Production port
    "debug": false,            // Disable debug mode
    "threaded": true,
    "max_connections": 200
  },
  "database": {
    "path": "D:/InspectionData/production.db",
    "backup_enabled": true,
    "backup_interval": 1800    // 30 minutes
  },
  "api": {
    "base_url": "http://production-server:8080/api",
    "timeout": 60,             // Longer timeout for production
    "retry_attempts": 5
  }
}
```

### 2. Custom Table Schema

```json
// user_configs/database_schema.json
[
  {
    "name": "PCB_INSPECTION",
    "columns": [
      "Barcode", "DT", "Process_id", "Station_ID",
      "SolderQuality", "ComponentAlignment", "TraceIntegrity",
      "ManualSolder", "ManualAlignment", "ManualTrace", "ManualResult"
    ],
    "primary_key": "Barcode",
    "timestamp_column": "DT"
  },
  {
    "name": "OPTICAL_INSPECTION", 
    "columns": [
      "Barcode", "DT", "Process_id", "Station_ID",
      "ScratchCount", "DustParticles", "ColorDeviation",
      "ManualScratch", "ManualDust", "ManualColor", "ManualResult"
    ],
    "primary_key": "Barcode",
    "timestamp_column": "DT"
  }
]
```

### 3. Multi-Stage Workflows

```json
// user_configs/inspection_workflows.json
[
  {
    "name": "PCB_TO_OPTICAL",
    "api1_table": "PCB_INSPECTION",
    "api2_table": "OPTICAL_INSPECTION",
    "description": "PCB inspection to optical verification",
    "enabled": true
  },
  {
    "name": "OPTICAL_TO_FINAL",
    "api1_table": "OPTICAL_INSPECTION", 
    "api2_table": "FINAL_QC",
    "description": "Optical to final quality control",
    "enabled": true
  }
]
```

## API Endpoint Management

The system automatically generates endpoints based on schema:

```
GET  /api/PCB_INSPECTION?barcode=XYZ123
POST /api/PCB_INSPECTION
PUT  /api/PCB_INSPECTION
DELETE /api/PCB_INSPECTION

GET  /api/OPTICAL_INSPECTION?barcode=XYZ123
POST /api/OPTICAL_INSPECTION
PUT  /api/OPTICAL_INSPECTION  
DELETE /api/OPTICAL_INSPECTION
```

## Database Schema Changes

### Adding New Columns

1. Update `database_schema.json`:
```json
{
  "name": "EXISTING_TABLE",
  "columns": ["Barcode", "DT", "ExistingField", "NewField1", "NewField2"],
  // ... rest of config
}
```

2. The system handles schema evolution automatically

### Migration Support

For major schema changes, create migration scripts:

```python
# migrations/add_new_columns.py
def migrate_schema(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("ALTER TABLE EXISTING_TABLE ADD COLUMN NewField1 TEXT")
    cursor.execute("ALTER TABLE EXISTING_TABLE ADD COLUMN NewField2 INTEGER")
    db_connection.commit()
```

## Best Practices

### 1. Configuration Management
- Keep user configs separate from templates
- Version your configuration files
- Validate configs before deployment
- Use environment-specific config files

### 2. Database Management
- Regular backups (automated via config)
- Schema versioning
- Migration planning for major changes
- Performance monitoring

### 3. Deployment
- Test in staging environment first
- Document configuration changes
- Monitor logs after deployment
- Have rollback plan ready

### 4. Security
- Don't include sensitive data in executables
- Use secure database paths
- Limit network access as needed
- Regular security updates

## Troubleshooting

### Common Issues

1. **Port conflicts:**
   - Change port in `user_configs/app_config.json`
   - Check firewall settings

2. **Database access:**
   - Verify database path in config
   - Check file permissions
   - Ensure directory exists

3. **Configuration not loading:**
   - Check JSON syntax
   - Verify file paths
   - Check logs for errors

### Logging

Application logs are in `logs/ai_inspection_system.log`:

```
2025-11-07 10:30:15,123 - Main - INFO - Configuration loaded successfully
2025-11-07 10:30:15,124 - Main - INFO - Database configured: /path/to/db
2025-11-07 10:30:15,125 - Server - INFO - Server starting on 127.0.0.1:5001
```

## Support

For deployment issues:
1. Check application logs
2. Verify configuration files
3. Test database connectivity
4. Review system requirements