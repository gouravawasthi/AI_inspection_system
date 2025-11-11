"""
Configuration Manager for AI Inspection System
Handles loading and managing all configuration settings from the configs folder
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigurationManager:
    """Centralized configuration management for the inspection system"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_dir: Path to configuration directory. If None, uses default location
        """
        if config_dir is None:
            # Auto-detect config directory - go up two levels from this file to reach project root, then into configs
            current_dir = Path(__file__).parent.parent.parent  # Go from src/config/ to project root
            self.config_dir = current_dir / "configs"
        else:
            self.config_dir = Path(config_dir)
            
        self._app_config = None
        self._inspection_workflows = None
        self._database_schema = None
        
        # Load configurations on initialization
        self._load_configurations()
    
    def _load_configurations(self):
        """Load all configuration files"""
        try:
            self._load_app_config()
            self._load_inspection_workflows()
            self._load_database_schema()
            print(f"✅ Configuration loaded from: {self.config_dir}")
        except Exception as e:
            print(f"❌ Configuration loading error: {e}")
            raise
    
    def _load_app_config(self):
        """Load main application configuration"""
        config_file = self.config_dir / "app_config.json"
        if not config_file.exists():
            raise FileNotFoundError(f"App config file not found: {config_file}")
            
        with open(config_file, 'r') as f:
            self._app_config = json.load(f)
    
    def _load_inspection_workflows(self):
        """Load inspection workflow configuration"""
        workflow_file = self.config_dir / "inspection_workflows.json"
        if not workflow_file.exists():
            raise FileNotFoundError(f"Workflow config file not found: {workflow_file}")
            
        with open(workflow_file, 'r') as f:
            self._inspection_workflows = json.load(f)
    
    def _load_database_schema(self):
        """Load database schema configuration"""
        schema_file = self.config_dir / "database_schema.json"
        if schema_file.exists():
            with open(schema_file, 'r') as f:
                self._database_schema = json.load(f)
    
    # API Configuration Methods
    def get_api_base_url(self) -> str:
        """Get the base API URL"""
        return self._app_config["api"]["base_url"]
    
    def get_api_endpoint_url(self, endpoint: str) -> str:
        """
        Get full URL for a specific API endpoint
        
        Args:
            endpoint: Endpoint name (e.g., 'CHIPINSPECTION', 'INLINEINSPECTIONBOTTOM')
            
        Returns:
            Full URL for the endpoint
        """
        base_url = self.get_api_base_url()
        
        # Check if endpoints section exists in config
        if "endpoints" in self._app_config.get("api", {}):
            endpoint_path = self._app_config["api"]["endpoints"].get(endpoint, f"/{endpoint}")
        else:
            # Fallback: construct endpoint path directly
            endpoint_path = f"/{endpoint}"
            
        return f"{base_url}{endpoint_path}"
    
    def get_api_timeout(self) -> int:
        """Get API timeout in seconds"""
        return self._app_config["api"]["timeout"]
    
    def get_api_retry_config(self) -> Dict[str, int]:
        """Get API retry configuration"""
        return {
            "attempts": self._app_config["api"]["retry_attempts"],
            "delay": self._app_config["api"]["retry_delay"]
        }
    
    def get_api_headers(self) -> Dict[str, str]:
        """Get default API headers"""
        api_config = self._app_config.get("api", {})
        if "headers" in api_config:
            return api_config["headers"].copy()
        else:
            # Return default headers if not configured
            return {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
    
    # Server Configuration Methods
    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration"""
        return self._app_config["server"].copy()
    
    def get_server_host(self) -> str:
        """Get server host"""
        return self._app_config["server"]["host"]
    
    def get_server_port(self) -> int:
        """Get server port"""
        return self._app_config["server"]["port"]
    
    # Database Configuration Methods
    def get_database_path(self) -> str:
        """Get database file path"""
        return self._app_config["database"]["path"]
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self._app_config["database"].copy()
    
    # Inspection Configuration Methods
    def get_process_id(self, inspection_type: str) -> str:
        """
        Get process ID for inspection type
        
        Args:
            inspection_type: Type of inspection (INLINE_BOTTOM, INLINE_TOP, EOLT, CHIP)
            
        Returns:
            Process ID string
        """
        inspection_config = self._app_config.get("inspection", {})
        process_ids = inspection_config.get("process_ids", {})
        
        return process_ids.get(
            inspection_type.upper(), 
            f"{inspection_type.upper()}_PROC_001"
        )
    
    def get_station_id(self, inspection_type: str) -> str:
        """
        Get station ID for inspection type
        
        Args:
            inspection_type: Type of inspection (INLINE_BOTTOM, INLINE_TOP, EOLT, CHIP)
            
        Returns:
            Station ID string
        """
        inspection_config = self._app_config.get("inspection", {})
        station_ids = inspection_config.get("station_ids", {})
        
        return station_ids.get(
            inspection_type.upper(),
            f"{inspection_type.upper()}_STATION_01"
        )
    
    def get_component_pass_rate(self, component: str) -> float:
        """
        Get default pass rate for a component
        
        Args:
            component: Component name (ANTENNA, CAPACITOR, etc.)
            
        Returns:
            Pass rate as decimal (0.0-1.0)
        """
        inspection_config = self._app_config.get("inspection", {})
        pass_rates = inspection_config.get("default_pass_rates", {})
        
        return pass_rates.get(
            component.upper(), 
            0.90  # Default 90% pass rate
        )
    
    # Workflow Configuration Methods
    def get_workflow_by_name(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """
        Get workflow configuration by name
        
        Args:
            workflow_name: Name of the workflow (e.g., 'CHIP_TO_INLINE_BOTTOM')
            
        Returns:
            Workflow configuration dict or None if not found
        """
        for workflow in self._inspection_workflows:
            if workflow.get("name") == workflow_name:
                return workflow
        return None
    
    def get_all_workflows(self) -> list:
        """Get all workflow configurations"""
        return self._inspection_workflows.copy()
    
    def get_enabled_workflows(self) -> list:
        """Get only enabled workflow configurations"""
        return [wf for wf in self._inspection_workflows if wf.get("enabled", True)]
    
    # UI Configuration Methods
    def get_ui_colors(self) -> Dict[str, str]:
        """Get UI color configuration"""
        ui_config = self._app_config.get("ui", {})
        component_display = ui_config.get("component_display", {})
        
        if "result_colors" in component_display:
            return component_display["result_colors"].copy()
        else:
            # Return default colors if not configured
            return {
                "pass": "#27ae60",
                "fail": "#e74c3c"
            }
    
    def should_show_individual_results(self) -> bool:
        """Check if individual component results should be shown"""
        ui_config = self._app_config.get("ui", {})
        component_display = ui_config.get("component_display", {})
        return component_display.get("show_individual_results", True)  # Default True
    
    def get_ui_update_interval(self) -> int:
        """Get UI update interval in milliseconds"""
        ui_config = self._app_config.get("ui", {})
        component_display = ui_config.get("component_display", {})
        return component_display.get("update_interval", 100)  # Default 100ms
    
    # Utility Methods
    def reload_config(self):
        """Reload all configuration files"""
        self._load_configurations()
    
    def get_config_version(self) -> str:
        """Get configuration version"""
        return self._app_config["config_version"]
    
    def get_app_version(self) -> str:
        """Get application version"""
        return self._app_config["app_version"]
    
    def validate_config(self) -> Dict[str, bool]:
        """
        Validate configuration files
        
        Returns:
            Dictionary with validation results for each config file
        """
        results = {}
        
        try:
            # Check app config
            required_sections = ["database", "server", "api", "inspection"]
            results["app_config"] = all(
                section in self._app_config for section in required_sections
            )
            
            # Check workflows
            results["workflows"] = isinstance(self._inspection_workflows, list) and len(self._inspection_workflows) > 0
            
            # Check if critical files exist
            results["config_files_exist"] = all([
                (self.config_dir / "app_config.json").exists(),
                (self.config_dir / "inspection_workflows.json").exists()
            ])
            
        except Exception as e:
            print(f"❌ Configuration validation error: {e}")
            results["validation_error"] = str(e)
        
        return results


# Global configuration manager instance
config_manager = None

def get_config_manager(config_dir: Optional[str] = None) -> ConfigurationManager:
    """
    Get or create the global configuration manager instance
    
    Args:
        config_dir: Configuration directory path (only used on first call)
        
    Returns:
        ConfigurationManager instance
    """
    global config_manager
    if config_manager is None:
        config_manager = ConfigurationManager(config_dir)
    return config_manager

def reload_configuration():
    """Reload the global configuration"""
    global config_manager
    if config_manager:
        config_manager.reload_config()
    else:
        config_manager = ConfigurationManager()