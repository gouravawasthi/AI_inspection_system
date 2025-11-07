"""
AI VDI System - Main Entry Point
Visual Defect Inspection System using AI/ML for automated quality control
"""

import sys
import os
import configparser
import logging
from pathlib import Path

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)
# Import the server module directly
from server.server import start_server, configure_database
from api.api_manager import APIManager


def setup_logging(log_level: str = 'INFO'):
    """
    Setup logging configuration for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Create logs directory if it doesn't exist
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'ai_inspection_system.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def load_config(config_path: str = 'config.ini') -> dict:
    """
    Load configuration from INI file
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    config = configparser.ConfigParser()
    
    # Set default configuration
    default_config = {
        'database': {
            'db_path': 'data/db',
            'db_name': 'inspection_data.db',
            'db_full_path': 'data/db/inspection_data.db',
            'table_names': ['CHIPINSPECTION', 'INLINEINSPECTIONBOTTOM', 'INLINEINSPECTIONTOP', 'EOLTINSPECTION']
        },
        'camera': {
            'camera_id': '1',
            'resolution_width': '1920',
            'resolution_height': '1080',
            'fps': '30'
        },
        'ml': {
            'model_path': 'ml/models/defect_model.pth',
            'model_type': 'cnn',
            'device': 'cpu',
            'threshold': '0.5',
            'target_size_width': '224',
            'target_size_height': '224'
        },
        'barcode': {
            'enabled': 'true',
            'scan_timeout': '5.0',
            'supported_formats': 'CODE128,QR'
        },
        'api_manager': {
            'server_host': '127.0.0.1',
            'server_port': '5000',
            'workflow': 'CHIP_TO_EOLT',
            'api1_endpoint': 'CHIP_INSPECTION',
            'api2_endpoint': 'EOLT_INSPECTION',
            'api1_description': 'chip inspection',
            'api2_description': 'EOLT testing',
            'timeout': '5',
            'auto_retry': 'true',
            'retry_count': '3'
        },
        'system': {
            'log_level': 'INFO',
            'auto_start': 'false',
            'save_inspection_images': 'true',
            'inspection_log_path': 'data/inspection_logs'
        },
        'api' = {
            'visual_api1': 'http://localhost:5001/visual/check_previous',
            'visual_api2': 'http://localhost:5002/visual/check_duplicate',
            'electrical_api1': 'http://localhost:5001/electrical/check_previous',
            'electrical_api2': 'http://localhost:5002/electrical/check_duplicate'
}
    }
    
    # Load default configuration
    config.read_dict(default_config)
    
    # Try to load from file
    if os.path.exists(config_path):
        try:
            config.read(config_path)
            print(f"Configuration loaded from {config_path}")
        except Exception as e:
            print(f"Error loading config file: {e}")
            print("Using default configuration")
    else:
        print(f"Config file {config_path} not found. Using default configuration")
    
    # Convert to nested dictionary
    config_dict = {}
    for section_name in config.sections():
        section = config[section_name]
        config_dict[section_name] = {}
        
        for key, value in section.items():
            # Try to convert to appropriate types
            if value.lower() in ('true', 'false'):
                config_dict[section_name][key] = value.lower() == 'true'
            elif value.replace('.', '').replace('-', '').isdigit():
                # Check if it's a simple number, not an IP address or complex string
                dot_count = value.count('.')
                if dot_count == 0:
                    # Integer
                    config_dict[section_name][key] = int(value)
                elif dot_count == 1 and not any(char.isalpha() for char in value):
                    # Simple float  
                    config_dict[section_name][key] = float(value)
                else:
                    # Multiple dots (likely IP) or contains letters - keep as string
                    config_dict[section_name][key] = value
            else:
                config_dict[section_name][key] = value
    
    return config_dict


def create_directory_structure():
    """Create necessary directories if they don't exist"""
    directories = [
        'data/raw',
        'data/processed', 
        'data/inspection_logs',
        'data/api_logs',
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def create_api_manager(config: dict) -> APIManager:
    """
    Create and configure APIManager from configuration settings
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured APIManager instance
    """
    api_config = config.get('api_manager', {})
    
    # Method 1: Use predefined workflow if specified
    workflow = api_config.get('workflow')
    if workflow and workflow != 'custom':
        try:
            api_manager = APIManager.create_workflow(workflow)
            print(f"✅ Created API Manager using workflow: {workflow}")
            return api_manager
        except ValueError as e:
            print(f"⚠️  Workflow creation failed: {e}")
            print("   Falling back to endpoint configuration...")
    
    # Method 2: Use endpoint configuration
    api1_endpoint = api_config.get('api1_endpoint', 'CHIP_INSPECTION')
    api2_endpoint = api_config.get('api2_endpoint', 'EOLT_INSPECTION')
    api1_desc = api_config.get('api1_description', 'previous inspection')
    api2_desc = api_config.get('api2_description', 'current inspection')
    
    try:
        api_manager = APIManager.create_from_config(
            api1_endpoint=api1_endpoint,
            api2_endpoint=api2_endpoint,
            placeholders=(api1_desc, api2_desc)
        )
        print(f"✅ Created API Manager: {api1_endpoint} -> {api2_endpoint}")
        return api_manager
    except ValueError as e:
        print(f"❌ API Manager creation failed: {e}")
        raise


def main():
    """Main function to start only the API server (GUI disabled for now)"""
    try:
        # Create necessary directories
        create_directory_structure()

        # Load configuration
        config = load_config()

        # Setup logging
        log_level = config.get('system', {}).get('log_level', 'INFO')
        setup_logging(log_level)

        logger = logging.getLogger('Main')
        logger.info("Starting API server only (GUI disabled)")

        # Configure database path from config
        db_full_path = config.get('database', {}).get('db_full_path', 'data/db/inspection_data.db')
        # Make sure path is absolute
        if not os.path.isabs(db_full_path):
            db_full_path = os.path.join(current_dir, db_full_path)
        
        logger.info(f"Configuring database at: {db_full_path}")
        configure_database(db_full_path)

        # Create and configure API Manager
        try:
            api_manager = create_api_manager(config)
            logger.info("API Manager configured successfully")
            
            # Store API manager instance globally for use by other modules
            # (You can also inject it into other components as needed)
            globals()['api_manager'] = api_manager
            
        except Exception as e:
            logger.error(f"Failed to configure API Manager: {e}")
            logger.warning("Continuing without API Manager...")

        # Start Flask server (blocking)
        start_server()

    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        logging.exception("Fatal error occurred")
        sys.exit(1)


if __name__ == "__main__":
    main()
