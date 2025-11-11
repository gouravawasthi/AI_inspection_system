#!/usr/bin/env python3
"""
AI Visual Defect Inspection System - Main Entry Point

System Flow:
1. Configuration & Logging Setup
2. Server Initialization  
3. GUI Application Launch
4. Camera & Image Processing Integration
5. API Communication & Results Management

Author: Nexvion AI Team
Version: 1.0.0
"""

import sys
import os
import logging
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Import configuration system
from config import config_manager, AppConfig

# Import system components
from server.server import start_server, configure_database
from api.api_manager import APIManager

# Import ML and Camera components
from ml.algorithm_engine import AlgorithmEngine
from camera.camera_integrator import CameraIntegrator

# TODO: Import when implemented
# from image_processing.processor import ImageProcessor

# GUI imports (conditional to handle missing PyQt5)
try:
    import sys
    import os
    # Ensure the correct path for UI imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ui_path = os.path.join(current_dir, 'src', 'ui')
    if ui_path not in sys.path:
        sys.path.insert(0, ui_path)
    
    from mainwindow import MainWindow
    PYQT5_AVAILABLE = True
    print("✅ PyQt5 and GUI components available")
except ImportError as e:
    PYQT5_AVAILABLE = False
    MainWindow = None
    print(f"⚠️  GUI not available: {e}")

class AIInspectionSystem:
    """
    Main application class that orchestrates all system components
    """
    
    def __init__(self):
        self.config: Optional[AppConfig] = None
        self.logger: Optional[logging.Logger] = None
        self.server_thread: Optional[threading.Thread] = None
        self.gui_app = None
        self.main_window = None
        self.api_manager: Optional[APIManager] = None
        
        # System components - Camera and AI
        self.camera_integrator: Optional[CameraIntegrator] = None
        self.algorithm_engine: Optional[AlgorithmEngine] = None
        self.image_processor = None
        self.main_window = None
        
        # System state
        self.server_running = False
        self.camera_active = False
        self.system_ready = False

    def initialize_system(self) -> bool:
        """
        Phase 1: Initialize configuration and logging
        """
        print("🔧 Initializing AI Inspection System...")
        
        try:
            # Load configuration
            self.config = config_manager.load_config()
            print(f"✅ Configuration loaded (Version: {self.config.config_version})")
            
            # Setup logging
            self._setup_logging()
            self.logger.info("="*60)
            self.logger.info("AI VISUAL DEFECT INSPECTION SYSTEM")
            self.logger.info(f"Application Version: {self.config.app_version}")
            self.logger.info(f"Config Version: {self.config.config_version}")
            self.logger.info("="*60)
            
            # Validate configuration
            if not config_manager.validate_config(self.config):
                self.logger.error("❌ Configuration validation failed")
                return False
                
            self.logger.info("✅ System configuration validated")
            return True
            
        except Exception as e:
            print(f"❌ System initialization failed: {e}")
            if self.logger:
                self.logger.error(f"System initialization failed: {e}")
            return False

    def start_server_component(self) -> bool:
        """
        Phase 2: Start the API server in background
        """
        try:
            self.logger.info("🚀 Starting API server component...")
            
            # Configure database
            db_path = os.path.join(current_dir, self.config.database.path)
            self.logger.info(f"Database: {db_path}")
            configure_database(db_path)
            
            # Create API manager
            self.api_manager = self._create_api_manager()
            if not self.api_manager:
                return False
            
            # Start server in background thread
            self.server_thread = threading.Thread(
                target=self._run_server,
                daemon=True,
                name="APIServer"
            )
            self.server_thread.start()
            
            # Wait for server to start
            self._wait_for_server_startup()
            
            if self.server_running:
                self.logger.info("✅ API server started successfully")
                return True
            else:
                self.logger.error("❌ Failed to start API server")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Server startup failed: {e}")
            return False

    def initialize_camera_system(self) -> bool:
        """
        Phase 3: Initialize camera and algorithm engine
        """
        try:
            self.logger.info("📷 Initializing camera and algorithm system...")
            
            # Initialize algorithm engine first
            config_dir = os.path.join(current_dir, 'configs')
            algo_config_path = os.path.join(config_dir, 'algo.json')
            
            if not os.path.exists(algo_config_path):
                self.logger.error(f"Algorithm config not found: {algo_config_path}")
                return False
            
            self.algorithm_engine = AlgorithmEngine(algo_config_path, debug=True)
            self.logger.info("✅ Algorithm engine initialized")
            
            # Load reference images and masks
            load_results = self.algorithm_engine.load_all_defaults()
            loaded_count = sum(1 for success in load_results.values() if success)
            total_count = len(load_results)
            
            self.logger.info(f"📸 References/Masks loaded: {loaded_count}/{total_count}")
            
            if loaded_count == 0:
                self.logger.warning("⚠️ No reference images loaded - inspection may not work correctly")
            
            # Initialize camera integrator with algorithm engine
            camera_config_path = os.path.join(config_dir, 'camera_config.json')
            self.camera_integrator = CameraIntegrator(camera_config_path, algo_config_path)
            
            # Verify camera integration
            if hasattr(self.camera_integrator, 'camera') and hasattr(self.camera_integrator, 'algorithm_engine'):
                self.logger.info("✅ Camera integrator initialized with algorithm engine")
                self.camera_active = True
                
                # Test camera readiness
                if self.camera_integrator.camera._capture is not None:
                    self.logger.info("� Camera device detected and ready")
                else:
                    self.logger.info("📹 Camera in simulation mode (no device detected)")
                
                return True
            else:
                self.logger.error("❌ Camera integrator missing required components")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Camera system initialization failed: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def launch_gui_application(self) -> bool:
        """
        Phase 4: Launch the GUI application
        """
        try:
            self.logger.info("🖥️  Launching GUI application...")
            
            if not PYQT5_AVAILABLE:
                self.logger.warning("⚠️  PyQt5 not available - running in console mode")
                self.system_ready = True
                return True
            
            # Import PyQt5 here to avoid startup issues if not available
            from PyQt5.QtWidgets import QApplication
            
            # Create QApplication
            self.gui_app = QApplication(sys.argv)
            self.gui_app.setApplicationName("AI Inspection System")
            
            # Create main window with camera integrator
            self.main_window = MainWindow()
            
            # Connect camera integrator to main window if available
            if hasattr(self.main_window, 'set_camera_integrator') and self.camera_integrator:
                self.main_window.set_camera_integrator(self.camera_integrator)
                self.logger.info("🔗 Camera integrator connected to main window")
            
            # Connect signals for inspection requests
            self.main_window.eolt_inspection_requested.connect(lambda: self._handle_inspection_request("EOLT"))
            self.main_window.inline_inspection_requested.connect(lambda: self._handle_inspection_request("INLINE"))
            self.main_window.quit_requested.connect(self._handle_quit_request)
            
            # Show main window
            self.main_window.show()
            
            self.logger.info("✅ GUI application ready")
            self.system_ready = True
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ GUI initialization failed: {e}")
            return False

    def _handle_inspection_request(self, inspection_type: str):
        """Handle inspection request from GUI"""
        try:
            self.logger.info(f"🔍 {inspection_type} inspection requested from GUI")
            
            # TODO: Implement specific inspection logic
            # For now, just show status
            test_barcode = f"TEST_{inspection_type}_123"
            result = self.run_inspection_workflow(test_barcode)
            
            self.logger.info(f"Inspection result: {result}")
            
            if self.main_window:
                self.main_window.show_inspection_status(f"{inspection_type} inspection completed")
                
        except Exception as e:
            self.logger.error(f"Error handling {inspection_type} inspection: {e}")
    
    def _handle_quit_request(self):
        """Handle quit request from GUI"""
        self.logger.info("🚪 Quit requested from GUI")
        self.shutdown()

    def run_inspection_workflow(self, barcode: str) -> Dict[str, Any]:
        """
        Main inspection workflow with real camera capture and algorithm analysis
        """
        try:
            self.logger.info(f"🔍 Starting inspection for barcode: {barcode}")
            
            # Step 1: API Manager checks previous inspection results
            api_result = self.api_manager.process_barcode(barcode)
            self.logger.info(f"API Check: {api_result['status']} - {api_result['message']}")
            
            if api_result['action_required']:
                self.logger.info("⚠️  User action required for duplicate handling")
                return api_result
            
            if api_result['status'] != 'success':
                self.logger.warning(f"Cannot proceed with inspection: {api_result['message']}")
                return api_result
            
            # Step 2: Verify camera and algorithm engine are ready
            if not self.camera_integrator or not self.algorithm_engine:
                self.logger.error("Camera or algorithm engine not initialized")
                return {
                    'status': 'error',
                    'message': 'Camera or algorithm engine not ready',
                    'data': None,
                    'action_required': False
                }
            
            # Step 3: Camera captures frames, averages them, and runs algorithm
            # This is now handled automatically by the camera integrator
            # The capture process includes:
            # - Stop live streaming and freeze last frame
            # - Capture multiple frames based on config
            # - Average the frames to reduce noise
            # - Pass averaged frame to algorithm engine
            # - Return results with original and processed images
            
            self.logger.info("📸 Starting frame capture and averaging process...")
            
            # The actual capture is triggered by the inspection window's capture button
            # This workflow method focuses on the high-level orchestration
            
            # For now, return a placeholder result that indicates the capture is ready
            # The real results will be handled by the inspection window when capture completes
            
            inspection_result = {
                'barcode': barcode,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'capture_ready',
                'message': 'Ready for capture - click capture button to proceed',
                'camera_state': str(self.camera_integrator.get_camera_state()),
                'algorithm_ready': True,
                'references_loaded': len(self.algorithm_engine.references),
                'masks_loaded': len(self.algorithm_engine.masks)
            }
            
            self.logger.info(f"✅ Inspection workflow ready - Camera state: {inspection_result['camera_state']}")
            self.logger.info(f"📚 References: {inspection_result['references_loaded']}, Masks: {inspection_result['masks_loaded']}")
            
            return {
                'status': 'ready',
                'message': 'System ready for inspection - use capture button to start',
                'data': inspection_result,
                'action_required': False
            }
            
        except Exception as e:
            self.logger.error(f"❌ Inspection workflow failed: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'status': 'error',
                'message': f"Inspection failed: {str(e)}",
                'data': None,
                'action_required': False
            }

    def run_main_loop(self):
        """
        Phase 5: Run main application loop
        """
        try:
            self.logger.info("🚀 Starting main application loop...")
            
            if PYQT5_AVAILABLE and self.gui_app:
                # GUI mode - run Qt event loop
                self.logger.info("📱 Running in GUI mode")
                print("\n" + "="*60)
                print("🎯 AI INSPECTION SYSTEM READY (GUI Mode)")
                print("="*60)
                print(f"📊 Server: http://{self.config.server.host}:{self.config.server.port}")
                print(f"💾 Database: {self.config.database.path}")
                print(f"🔄 Active Workflows: {len(self.config.workflows)}")
                print(f"📷 Camera: {'Active' if self.camera_active else 'Inactive'}")
                print("🖥️  GUI: MainWindow Active")
                print("="*60)
                
                self.gui_app.exec_()
            else:
                # Console mode - simple loop
                self.logger.info("💻 Running in console mode")
                self._console_mode_loop()
                
        except Exception as e:
            self.logger.error(f"❌ Main loop error: {e}")
        finally:
            self.shutdown()
    
    def _console_mode_loop(self):
        """Run console mode loop when GUI is not available"""
        print("\n" + "="*60)
        print("🎯 AI INSPECTION SYSTEM READY (Console Mode)")
        print("="*60)
        print(f"📊 Server: http://{self.config.server.host}:{self.config.server.port}")
        print(f"💾 Database: {self.config.database.path}")
        print(f"🔄 Active Workflows: {len(self.config.workflows)}")
        print(f"📷 Camera: {'Active' if self.camera_active else 'Inactive'}")
        print("💻 Console commands: eolt, inline, test <barcode>, quit")
        print("="*60)
        
        while self.system_ready:
            try:
                user_input = input("\n> ").strip().lower()
                
                if user_input == "quit":
                    break
                elif user_input == "eolt":
                    self._handle_inspection_request("EOLT")
                elif user_input == "inline":
                    self._handle_inspection_request("INLINE")
                elif user_input.startswith("test "):
                    barcode = user_input.replace("test ", "").strip()
                    if barcode:
                        result = self.run_inspection_workflow(barcode)
                        print(f"Result: {result}")
                else:
                    print("Commands: eolt, inline, test <barcode>, quit")
                    
            except KeyboardInterrupt:
                break
            except EOFError:
                break

    def shutdown(self):
        """
        Graceful system shutdown
        """
        try:
            self.logger.info("🛑 Shutting down AI Inspection System...")
            
            # Close GUI application
            if PYQT5_AVAILABLE and self.gui_app and self.main_window:
                self.main_window.close()
                self.gui_app.quit()
                self.logger.info("�️  GUI application closed")
            
            # TODO: Cleanup components
            if self.camera_active and self.camera_integrator:
                self.camera_integrator.stop_inspection()
                self.logger.info("📷 Camera system stopped")
            
            # Cleanup algorithm engine
            if self.algorithm_engine:
                self.algorithm_engine = None
                self.logger.info("🧠 Algorithm engine cleaned up")
            
            # Mark system as not ready
            self.system_ready = False
            
            self.logger.info("✅ System shutdown completed")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during shutdown: {e}")
            print(f"Error during shutdown: {e}")

    # Private helper methods
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # Get log level from config or default to INFO
        log_level = getattr(self.config, 'log_level', 'INFO').upper()
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'ai_inspection_system.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        
    def _create_api_manager(self) -> Optional[APIManager]:
        """Create and configure API manager"""
        try:
            # Find enabled workflow
            enabled_workflows = [wf for wf in self.config.workflows if wf.enabled]
            
            if not enabled_workflows:
                self.logger.warning("No enabled workflows found, using default")
                return APIManager.create_workflow('CHIP_TO_EOLT')
            
            # Use first enabled workflow
            workflow = enabled_workflows[0]
            self.logger.info(f"Using workflow: {workflow.name} - {workflow.description}")
            
            # Create API manager
            api1_url = f"{self.config.api.base_url}/{workflow.api1_table}"
            api2_url = f"{self.config.api.base_url}/{workflow.api2_table}"
            
            return APIManager(
                api1_url=api1_url,
                api2_url=api2_url,
                placeholders=(workflow.api1_table.lower(), workflow.api2_table.lower())
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create API Manager: {e}")
            return None
    
    def _run_server(self):
        """Run Flask server in background thread"""
        try:
            self.logger.info("🔧 Starting Flask server in background thread...")
            start_server()
        except Exception as e:
            self.logger.error(f"❌ Server thread error: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def is_server_running(self) -> bool:
        """Check if server is currently running and responsive"""
        try:
            import requests
            url = f"http://{self.config.server.host}:{self.config.server.port}/api/CHIPINSPECTION"
            response = requests.get(url, timeout=2)
            return response.status_code in (200, 404)
        except:
            return False
    
    def _wait_for_server_startup(self, timeout: int = 15):
        """Wait for server to start up"""
        import requests
        
        url = f"http://{self.config.server.host}:{self.config.server.port}/api/CHIPINSPECTION"
        self.logger.info(f"⏳ Waiting for server startup at {url}")
        
        for i in range(timeout):
            try:
                response = requests.get(url, timeout=2)
                if response.status_code in (200, 404):  # 404 is OK (no data)
                    self.server_running = True
                    self.logger.info(f"✅ Server responded successfully (status: {response.status_code})")
                    time.sleep(1)  # Give server extra moment to fully initialize
                    return
            except requests.exceptions.RequestException as e:
                if i == 0:
                    self.logger.info(f"🔄 Server starting... (attempt {i+1}/{timeout})")
            except:
                pass
            time.sleep(1)
        
        self.logger.error(f"❌ Server failed to start within {timeout} seconds")
        self.server_running = False


def main():
    """
    Main entry point with proper error handling
    """
    system = None
    
    try:
        # Create system instance
        system = AIInspectionSystem()
        
        # Phase 1: Initialize configuration and logging
        if not system.initialize_system():
            print("❌ System initialization failed")
            return 1
            
        # Phase 2: Start API server
        if not system.start_server_component():
            print("❌ Server startup failed")
            return 1
            
        # Phase 3: Initialize camera and image processing
        if not system.initialize_camera_system():
            print("❌ Camera system initialization failed")
            return 1
            
        # Phase 4: Launch GUI application
        if not system.launch_gui_application():
            print("❌ GUI initialization failed")
            return 1
            
        # Phase 5: Run main application loop
        system.run_main_loop()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Application interrupted by user")
        return 0
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        if system and system.logger:
            system.logger.error(f"Fatal error: {e}")
        return 1
        
    finally:
        if system:
            system.shutdown()


if __name__ == "__main__":
    sys.exit(main())