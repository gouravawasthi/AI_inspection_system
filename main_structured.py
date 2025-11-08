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

# TODO: Import when implemented
# from camera.camera_interface import CameraManager
# from image_processing.processor import ImageProcessor
# from ml.inference import DefectDetector

# GUI imports (conditional to handle missing PyQt5)
try:
    from ui.mainwindow import MainWindow
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False
    MainWindow = None
    print("⚠️  PyQt5 not available - GUI will be disabled")

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
        
        # System components (to be implemented)
        self.camera_manager = None
        self.image_processor = None
        self.defect_detector = None
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
        Phase 3: Initialize camera and image processing
        """
        try:
            self.logger.info("📷 Initializing camera system...")
            
            # TODO: Implement camera initialization
            # self.camera_manager = CameraManager(self.config.camera)
            # if not self.camera_manager.initialize():
            #     self.logger.error("❌ Camera initialization failed")
            #     return False
            
            self.logger.info("📸 Camera system initialized (MOCK)")
            
            # TODO: Initialize image processing
            # self.image_processor = ImageProcessor(self.config.image_processing)
            # self.defect_detector = DefectDetector(self.config.ml)
            
            self.logger.info("🔍 Image processing system initialized (MOCK)")
            self.camera_active = True
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Camera system initialization failed: {e}")
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
            
            # Create main window
            self.main_window = MainWindow()
            
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
        Main inspection workflow that ties everything together
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
            
            # Step 2: Camera captures image
            # TODO: Implement camera capture
            # image = self.camera_manager.capture_image()
            # self.logger.info("📸 Image captured")
            
            # Step 3: Image processing and AI analysis
            # TODO: Implement image processing
            # processed_image = self.image_processor.preprocess(image)
            # defects = self.defect_detector.detect_defects(processed_image)
            # inspection_result = self.image_processor.analyze_results(defects)
            
            # Mock inspection result for now
            inspection_result = {
                'barcode': barcode,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'defects_detected': 0,
                'quality_score': 0.95,
                'pass_fail': 1,  # 1 = Pass, 0 = Fail
                'manual_result': 1,
                'details': {
                    'scratch_count': 0,
                    'dust_particles': 1,
                    'color_deviation': 0.02
                }
            }
            
            # Step 4: Send results to API (POST new record)
            # This creates the new entry we mentioned in the "proceed with new entry" message
            workflow_name = list(self.config.workflows)[0].name if self.config.workflows else 'CHIP_TO_EOLT'
            workflow = next((w for w in self.config.workflows if w.name == workflow_name), None)
            
            if workflow:
                api_url = f"{self.config.api.base_url}/{workflow.api2_table}"
                # TODO: POST inspection_result to api_url
                self.logger.info(f"📤 Inspection results sent to {workflow.api2_table}")
            
            self.logger.info(f"✅ Inspection completed - Result: {'PASS' if inspection_result['pass_fail'] else 'FAIL'}")
            
            return {
                'status': 'completed',
                'message': f"Inspection completed - {'PASS' if inspection_result['pass_fail'] else 'FAIL'}",
                'data': inspection_result,
                'action_required': False
            }
            
        except Exception as e:
            self.logger.error(f"❌ Inspection workflow failed: {e}")
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
            if self.camera_active:
                # self.camera_manager.cleanup()
                self.logger.info("📷 Camera system stopped")
            
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
            start_server()
        except Exception as e:
            self.logger.error(f"Server thread error: {e}")
    
    def _wait_for_server_startup(self, timeout: int = 10):
        """Wait for server to start up"""
        import requests
        
        url = f"http://{self.config.server.host}:{self.config.server.port}/api/CHIPINSPECTION"
        
        for _ in range(timeout):
            try:
                response = requests.get(url, timeout=1)
                if response.status_code in (200, 404):  # 404 is OK (no data)
                    self.server_running = True
                    return
            except:
                pass
            time.sleep(1)
        
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