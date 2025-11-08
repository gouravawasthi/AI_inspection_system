#!/usr/bin/env python3
"""
AI VDI System - Main Entry Point
Visual Defect Inspection System using AI/ML for automated quality control

Enhanced with flexible configuration management for production deployment
"""

import sys
import os
import logging
from pathlib import Path

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Import configuration manager first
from config import config_manager, AppConfig

# Import other modules  
from server.server import start_server, configure_database
from api.api_manager import APIManager


def setup_logging(config: AppConfig):
    """Setup logging configuration based on config"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    log_level = getattr(config, 'log_level', 'INFO').upper()
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'ai_inspection_system.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def initialize_application():
    """Initialize application with configuration management"""
    
    # Load configuration
    config = config_manager.load_config()
    
    # Setup logging
    logger = setup_logging(config)
    
    logger.info("=" * 60)
    logger.info("AI INSPECTION SYSTEM STARTING")
    logger.info(f"Version: {config.app_version}")
    logger.info(f"Config Version: {config.config_version}")
    logger.info("=" * 60)
    
    # Validate configuration
    if not config_manager.validate_config(config):
        logger.error("Configuration validation failed")
        return None, None
    
    logger.info("Configuration loaded and validated successfully")
    
    # Configure database
    db_path = os.path.join(current_dir, config.database.path)
    logger.info(f"Configuring database at: {db_path}")
    configure_database(db_path)
    
    return config, logger


def create_api_manager(config: AppConfig, logger: logging.Logger):
    """Create API manager based on configuration"""
    
    try:
        # Find enabled workflow
        enabled_workflows = [wf for wf in config.workflows if wf.enabled]
        
        if not enabled_workflows:
            logger.warning("No enabled workflows found, using default")
            api_manager = APIManager.create_workflow('CHIP_TO_EOLT')
        else:
            # Use first enabled workflow
            workflow = enabled_workflows[0]
            logger.info(f"Using workflow: {workflow.name}")
            
            # Create API manager from workflow config
            api1_url = f"{config.api.base_url}/{workflow.api1_table}"
            api2_url = f"{config.api.base_url}/{workflow.api2_table}"
            
            api_manager = APIManager(
                api1_url=api1_url,
                api2_url=api2_url, 
                placeholders=(workflow.api1_table.lower(), workflow.api2_table.lower())
            )
            
        logger.info("✅ API Manager configured successfully")
        return api_manager
        
    except Exception as e:
        logger.error(f"Failed to create API Manager: {e}")
        return None


def start_application_server(config: AppConfig, logger: logging.Logger):
    """Start the Flask application server"""
    
    logger.info("🚀 Starting Flask server")
    logger.info(f"   Server: http://{config.server.host}:{config.server.port}")
    logger.info(f"   Database: {config.database.path}")
    logger.info(f"   Debug mode: {config.server.debug}")
    
    try:
        start_server(
            host=config.server.host,
            port=config.server.port,
            debug=config.server.debug,
            threaded=config.server.threaded
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        return False
    
    return True


def main():
    """Main application entry point"""
    
    try:
        # Initialize application
        config, logger = initialize_application()
        if not config or not logger:
            print("Failed to initialize application")
            sys.exit(1)
        
        # Create API manager
        api_manager = create_api_manager(config, logger)
        if not api_manager:
            logger.error("Failed to create API manager")
            sys.exit(1)
        
        # Start server
        logger.info("Starting API server (GUI disabled for executable)")
        if not start_application_server(config, logger):
            logger.error("Failed to start server")
            sys.exit(1)
            
    except KeyboardInterrupt:
        if 'logger' in locals():
            logger.info("Application interrupted by user")
        else:
            print("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        if 'logger' in locals():
            logger.error(f"Unexpected error: {e}")
        else:
            print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()