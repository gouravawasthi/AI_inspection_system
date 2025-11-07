# Server package - Flask REST API for inspection database
"""
Server package for providing REST API access to inspection database.

This package provides:
- Flask application with dynamic CRUD endpoints
- Database configuration and connection management  
- Table validation and query execution
- Server startup and management functions
"""

from .server import (
    # Main functions
    configure_database,
    start_server,
    get_db_connection,
    execute_db_command,
    
    # Route handlers
    dynamic_get,
    dynamic_post, 
    dynamic_put,
    dynamic_delete,
    dynamic_handler,
    
    # Constants and configuration
    VALID_TABLES,
    app,
    DB_FILE,
    DATA_DIR,
)

__all__ = [
    'configure_database',
    'start_server', 
    'get_db_connection',
    'execute_db_command',
    'dynamic_get',
    'dynamic_post',
    'dynamic_put', 
    'dynamic_delete',
    'dynamic_handler',
    'VALID_TABLES',
    'app',
    'DB_FILE',
    'DATA_DIR',
]