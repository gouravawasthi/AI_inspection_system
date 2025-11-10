"""
Configuration Management System for AI Inspection Application
Handles dynamic configuration loading, validation, and schema management
"""

import os
import json
import configparser
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration"""
    path: str = "data/db/inspection_data.db"
    backup_enabled: bool = True
    backup_interval: int = 3600  # seconds
    schema_version: str = "1.0"
    
@dataclass 
class ServerConfig:
    """Server configuration"""
    host: str = "127.0.0.1"
    port: int = 5001
    debug: bool = False
    threaded: bool = True
    max_connections: int = 100

@dataclass
class APIConfig:
    """API configuration"""
    base_url: str = "http://127.0.0.1:5001/api"
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 1

@dataclass
class TableSchema:
    """Database table schema definition"""
    name: str
    columns: List[str]
    primary_key: str = "Barcode"
    timestamp_column: str = "DT"

@dataclass
class InspectionWorkflow:
    """Inspection workflow definition"""
    name: str
    api1_table: str
    api2_table: str
    description: str
    enabled: bool = True

@dataclass
class CameraConfig:
    """Camera configuration"""
    device_id: int = 0
    resolution_width: int = 1920
    resolution_height: int = 1080
    fps: int = 30
    auto_focus: bool = True
    exposure: str = "auto"
    capture_format: str = "jpg"

@dataclass
class ImageProcessingConfig:
    """Image processing configuration"""
    preprocessing: dict
    detection: dict

@dataclass
class MLConfig:
    """Machine learning configuration"""
    model_path: str = "ml/models/defect_detection.onnx"
    device: str = "cpu"
    confidence_threshold: float = 0.7
    batch_size: int = 1
    input_size: list = None

@dataclass
class BrandingConfig:
    """GUI branding configuration"""
    logo_directory: str = "brand_images"
    taisys_logo: str = "Taisys.jpeg"
    avenya_logo: str = "Avenya.jpg"
    logo_width: int = 300
    logo_height: int = 200
    show_logos: bool = True
    background_color: str = "#ffffff"

@dataclass
class GUIConfig:
    """GUI configuration"""
    theme: str = "modern"
    window_width: int = 1200
    window_height: int = 800
    fullscreen_mode: bool = True
    raspberry_pi_optimized: bool = True
    auto_start_camera: bool = True
    show_debug_info: bool = False
    branding: BrandingConfig = None
    
    def __post_init__(self):
        if self.branding is None:
            self.branding = BrandingConfig()

@dataclass
class InspectionConfig:
    """Inspection workflow configuration"""
    auto_proceed_on_pass: bool = True
    save_inspection_images: bool = True
    image_save_path: str = "data/inspection_images"
    quality_threshold: float = 0.8

@dataclass
class AppConfig:
    """Main application configuration"""
    database: DatabaseConfig
    server: ServerConfig  
    api: APIConfig
    camera: CameraConfig
    image_processing: ImageProcessingConfig
    ml: MLConfig
    gui: GUIConfig
    inspection: InspectionConfig
    table_schemas: List[TableSchema]
    workflows: List[InspectionWorkflow]
    app_version: str = "1.0.0"
    config_version: str = "1.0"
    log_level: str = "INFO"

class ConfigManager:
    """
    Configuration Manager for handling different config formats and runtime updates
    """
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.config_file_paths = {
            'main': self.config_dir / "app_config.json",
            'schema': self.config_dir / "database_schema.json", 
            'workflows': self.config_dir / "inspection_workflows.json",
            'ini': self.config_dir / "config.ini"
        }
        self._config: Optional[AppConfig] = None
        
    def load_config(self) -> AppConfig:
        """Load configuration from files, creating defaults if needed"""
        
        # Try loading from JSON first (preferred for complex configs)
        if self.config_file_paths['main'].exists():
            try:
                return self._load_from_json()
            except Exception as e:
                logger.warning(f"Failed to load JSON config: {e}")
        
        # Fallback to INI file
        if self.config_file_paths['ini'].exists():
            try:
                return self._load_from_ini()
            except Exception as e:
                logger.warning(f"Failed to load INI config: {e}")
                
        # Create default configuration
        logger.info("Creating default configuration")
        return self._create_default_config()
    
    def save_config(self, config: AppConfig, format: str = "json"):
        """Save configuration to file"""
        if format.lower() == "json":
            self._save_to_json(config)
        elif format.lower() == "ini":
            self._save_to_ini(config)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _load_from_json(self) -> AppConfig:
        """Load from JSON files"""
        with open(self.config_file_paths['main'], 'r') as f:
            data = json.load(f)
        
        # Load schemas if separate file exists
        schema_data = []
        if self.config_file_paths['schema'].exists():
            with open(self.config_file_paths['schema'], 'r') as f:
                schema_data = json.load(f)
        
        # Load workflows if separate file exists  
        workflow_data = []
        if self.config_file_paths['workflows'].exists():
            with open(self.config_file_paths['workflows'], 'r') as f:
                workflow_data = json.load(f)
        
        # Reconstruct config object
        config = AppConfig(
            database=DatabaseConfig(**data['database']),
            server=ServerConfig(**data['server']),
            api=APIConfig(**data['api']),
            table_schemas=[TableSchema(**schema) for schema in (schema_data or data.get('table_schemas', []))],
            workflows=[InspectionWorkflow(**wf) for wf in (workflow_data or data.get('workflows', []))],
            app_version=data.get('app_version', '1.0.0'),
            config_version=data.get('config_version', '1.0')
        )
        
        return config
    
    def _save_to_json(self, config: AppConfig):
        """Save to JSON files"""
        # Main config
        main_data = {
            'database': asdict(config.database),
            'server': asdict(config.server),
            'api': asdict(config.api),
            'app_version': config.app_version,
            'config_version': config.config_version
        }
        
        with open(self.config_file_paths['main'], 'w') as f:
            json.dump(main_data, f, indent=2)
        
        # Schemas
        schema_data = [asdict(schema) for schema in config.table_schemas]
        with open(self.config_file_paths['schema'], 'w') as f:
            json.dump(schema_data, f, indent=2)
            
        # Workflows
        workflow_data = [asdict(wf) for wf in config.workflows]
        with open(self.config_file_paths['workflows'], 'w') as f:
            json.dump(workflow_data, f, indent=2)
    
    def _load_from_ini(self) -> AppConfig:
        """Load from INI file (legacy support)"""
        parser = configparser.ConfigParser()
        parser.read(self.config_file_paths['ini'])
        
        # Create config from INI
        database = DatabaseConfig(
            path=parser.get('database', 'path', fallback='data/db/inspection_data.db')
        )
        
        server = ServerConfig(
            host=parser.get('server', 'host', fallback='127.0.0.1'),
            port=parser.getint('server', 'port', fallback=5001),
            debug=parser.getboolean('server', 'debug', fallback=False)
        )
        
        api = APIConfig(
            base_url=parser.get('api', 'base_url', fallback=f"http://{server.host}:{server.port}/api"),
            timeout=parser.getint('api', 'timeout', fallback=30)
        )
        
        # Default schemas and workflows
        table_schemas = self._get_default_schemas()
        workflows = self._get_default_workflows()
        
        return AppConfig(
            database=database,
            server=server,
            api=api,
            table_schemas=table_schemas,
            workflows=workflows
        )
    
    def _create_default_config(self) -> AppConfig:
        """Create default configuration"""
        config = AppConfig(
            database=DatabaseConfig(),
            server=ServerConfig(),
            api=APIConfig(),
            camera=CameraConfig(),
            image_processing=ImageProcessingConfig(
                preprocessing={
                    "resize_width": 224,
                    "resize_height": 224,
                    "normalize": True,
                    "denoise": True
                },
                detection={
                    "scratch_threshold": 0.3,
                    "dust_threshold": 0.2,
                    "color_threshold": 0.1,
                    "edge_detection": True
                }
            ),
            ml=MLConfig(
                input_size=[224, 224, 3]
            ),
            gui=GUIConfig(
                branding=BrandingConfig()
            ),
            inspection=InspectionConfig(),
            table_schemas=self._get_default_schemas(),
            workflows=self._get_default_workflows()
        )
        
        # Save default config
        self.save_config(config, "json")
        return config
    
    def _get_default_schemas(self) -> List[TableSchema]:
        """Get default table schemas"""
        return [
            TableSchema(
                name="CHIPINSPECTION",
                columns=['Barcode', 'DT', 'Process_id', 'Station_ID', 'PASS_FAIL']
            ),
            TableSchema(
                name="INLINEINSPECTIONTOP", 
                columns=['Barcode', 'DT', 'Process_id', 'Station_ID', 'Screw', 'Plate', 'Result', 'ManualScrew', 'ManualPlate', 'ManualResult']
            ),
            TableSchema(
                name="INLINEINSPECTIONBOTTOM",
                columns=['Barcode', 'DT', 'Process_id', 'Station_ID', 'Antenna', 'Capacitor', 'Speaker', 'Result', 'ManualAntenna', 'ManualCapacitor', 'ManualSpeaker', 'ManualResult']
            ),
            TableSchema(
                name="EOLTINSPECTION",
                columns=['Barcode', 'DT', 'Process_id', 'Station_ID', 'Upper', 'Lower', 'Left', 'Right', 'Result', 'Printtext', 'Barcodetext', 'ManualUpper', 'ManualLower', 'ManualLeft', 'ManualRight', 'ManualResult']
            )
        ]
    
    def _get_default_workflows(self) -> List[InspectionWorkflow]:
        """Get default inspection workflows"""
        return [
            InspectionWorkflow(
                name="CHIP_TO_EOLT",
                api1_table="CHIPINSPECTION", 
                api2_table="EOLTINSPECTION",
                description="Chip inspection to EOLT testing workflow"
            ),
            InspectionWorkflow(
                name="INLINE_TOP_TO_EOLT",
                api1_table="INLINEINSPECTIONTOP",
                api2_table="EOLTINSPECTION", 
                description="Inline top inspection to EOLT testing workflow"
            ),
            InspectionWorkflow(
                name="INLINE_BOTTOM_TO_EOLT",
                api1_table="INLINEINSPECTIONBOTTOM",
                api2_table="EOLTINSPECTION",
                description="Inline bottom inspection to EOLT testing workflow"  
            )
        ]
    
    def update_config(self, updates: Dict[str, Any]) -> AppConfig:
        """Update configuration at runtime"""
        if not self._config:
            self._config = self.load_config()
            
        # Apply updates using dot notation
        for key, value in updates.items():
            self._set_nested_value(self._config, key, value)
        
        return self._config
    
    def _set_nested_value(self, obj: Any, key: str, value: Any):
        """Set nested value using dot notation (e.g., 'server.port')"""
        keys = key.split('.')
        current = obj
        
        for k in keys[:-1]:
            current = getattr(current, k)
        
        setattr(current, keys[-1], value)
    
    def validate_config(self, config: AppConfig) -> bool:
        """Validate configuration"""
        try:
            # Check database path
            db_path = Path(config.database.path)
            if not db_path.parent.exists():
                db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check port availability
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                result = s.connect_ex((config.server.host, config.server.port))
                if result == 0:
                    logger.warning(f"Port {config.server.port} is already in use")
            
            return True
        except Exception as e:
            logger.error(f"Config validation failed: {e}")
            return False

# Global config manager instance
config_manager = ConfigManager()