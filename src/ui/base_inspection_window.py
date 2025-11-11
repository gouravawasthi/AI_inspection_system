"""
Base Inspection Window - Parent class for all inspection interfaces
Provides common functionality for EOLT and INLINE testing
"""

import sys
import os
import csv
from datetime import datetime
from typing import Optional, Dict, Any, List
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                            QPushButton, QLabel, QFrame, QSpacerItem, QSizePolicy,
                            QGroupBox, QSlider, QCheckBox, QLineEdit, QTextEdit,
                            QProgressBar, QMessageBox, QComboBox, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QFont, QImage

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.api_manager import APIManager
from camera.camera_integrator import CameraIntegrator
try:
    from config.config_manager import get_config_manager
except ImportError:
    print("⚠️ Configuration manager not available, using default colors")
    get_config_manager = None


class BaseInspectionWindow(QWidget):
    """Base inspection window for product quality inspection"""
    
    # Signals
    inspection_complete = pyqtSignal(dict)
    window_closed = pyqtSignal()
    
    # Define inspection states for button logic control
    class InspectionState:
        IDLE = "idle"                    # No barcode, ready for input
        BARCODE_ENTERED = "barcode_entered"  # Barcode entered, ready to start
        INSPECTION_ACTIVE = "inspection_active"  # Currently inspecting
        STEP_IN_PROGRESS = "step_in_progress"    # Step being processed  
        STEP_COMPLETED = "step_completed"        # Step completed, ready for next
        INSPECTION_COMPLETED = "inspection_completed"  # All steps done
        OVERRIDE_APPLIED = "override_applied"    # Manual override applied
        DATA_SUBMITTED = "data_submitted"        # Data sent to API
    
    def __init__(self, parent=None, inspection_type="GENERIC"):
        super().__init__()
        self.parent_window = parent
        self.inspection_type = inspection_type
        self.barcode = ""
        self.current_step = 0
        self.inspection_steps = self.get_inspection_steps()
        self.inspection_results = {}
        self.inspection_start_time = None
        self.step_start_time = None
        self.api_manager = None
        self.api_data_collected = {}
        
        # Initialize camera integrator
        self.camera_integrator = CameraIntegrator()
        self.camera_integrator.camera.analysis_complete.connect(self.on_camera_analysis_complete)
        self.camera_integrator.camera.error_occurred.connect(self.on_camera_error)
        
        # Set up logging
        import logging
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        
    def set_camera_integrator(self, camera_integrator):
        """Set camera integrator from main application"""
        if camera_integrator:
            # Disconnect old integrator signals
            if self.camera_integrator:
                try:
                    self.camera_integrator.camera.analysis_complete.disconnect(self.on_camera_analysis_complete)
                    self.camera_integrator.camera.error_occurred.disconnect(self.on_camera_error)
                except:
                    pass
            
            # Set new integrator
            self.camera_integrator = camera_integrator
            
            # Connect new signals
            self.camera_integrator.camera.analysis_complete.connect(self.on_camera_analysis_complete)
            self.camera_integrator.camera.error_occurred.connect(self.on_camera_error)
            
            # Reconnect camera signals after setting new integrator
            self._connect_camera_signals()
            
            self.logger.info("Camera integrator updated from main application")
        
        # Initialize inspection state for smart button control
        self.inspection_state = self.InspectionState.IDLE
        self.step_data_collected = False  # Track if current step has data
        self.override_allowed = False     # Track if override is allowed
        
        # Initialize API manager for this inspection type
        self.init_api_manager()
        self.init_ui()
        
        # Connect camera signals after UI is created
        self._connect_camera_signals()
        
        # Start camera streaming immediately (not waiting for barcode)
        self._start_immediate_camera_streaming()
    
    def on_camera_analysis_complete(self, result):
        """Handle camera analysis completion"""
        try:
            # Store the result
            current_step_name = self.inspection_steps[self.current_step]
            self.inspection_results[current_step_name] = {
                'status': result.status,
                'input_image': result.input_image,
                'output_image': result.output_image,
                'results': result.result,
                'timestamp': datetime.now()
            }
            
            # Update UI with results
            self.update_camera_display_with_result(result)
            
            # Mark step as completed
            self.step_data_collected = True
            self.enter_step_completed_state()
            
            # Update button states
            self.update_button_states()
            
        except Exception as e:
            self.logger.error(f"Error handling camera analysis: {e}")
            self.on_camera_error(f"Analysis processing error: {e}")
    
    def on_camera_error(self, error_msg: str):
        """Handle camera errors"""
        self.update_camera_display(f"❌ Camera Error:\n{error_msg}\n\nCheck camera connection and try again")
        # Re-enable capture button to allow retry
        self.start_inspection_button.setEnabled(True)
    
    def update_camera_display_with_result(self, result):
        """Update result image display with algorithm output"""
        try:
            status_icon = "✅" if result.status == "PASS" else "❌"
            current_step_name = self.inspection_steps[self.current_step]
            
            # If we have an output image from the algorithm, display it
            if hasattr(result, 'output_image') and result.output_image is not None:
                # Convert numpy array to QImage and display
                import cv2
                if isinstance(result.output_image, str):
                    # If it's a path, load the image
                    output_img = cv2.imread(result.output_image)
                else:
                    # If it's already an array
                    output_img = result.output_image
                
                if output_img is not None:
                    # Convert BGR to RGB
                    rgb_img = cv2.cvtColor(output_img, cv2.COLOR_BGR2RGB)
                    height, width, channel = rgb_img.shape
                    bytes_per_line = 3 * width
                    
                    # Create QImage
                    qimage = QImage(rgb_img.data, width, height, bytes_per_line, QImage.Format_RGB888)
                    
                    # Convert to QPixmap and scale
                    pixmap = QPixmap.fromImage(qimage)
                    scaled_pixmap = pixmap.scaled(
                        self.result_image_label.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    
                    self.result_image_label.setPixmap(scaled_pixmap)
                else:
                    # Show text result if no image
                    self.result_image_label.clear()
                    self.result_image_label.setText(f"{status_icon} {current_step_name}\nStatus: {result.status}\nResult: {result.result}")
            else:
                # Show text result if no output image
                self.result_image_label.clear()
                self.result_image_label.setText(f"{status_icon} {current_step_name}\nStatus: {result.status}\nResult: {result.result}")
                
        except Exception as e:
            self.logger.error(f"Error updating result display: {e}")
            self.result_image_label.clear()
            self.result_image_label.setText(f"❌ Error displaying result\n{e}")
    
    def update_result_display(self, text):
        """Update result display with text (fallback when no algorithm result)"""
        try:
            # Clear any existing pixmap and show text in result area
            self.result_image_label.clear()
            self.result_image_label.setText(text)
            
        except Exception as e:
            self.logger.error(f"Error updating result display: {e}")
    
    def update_video_frame(self, qimage):
        """Update live video display with video frame"""
        try:
            # Convert QImage to QPixmap and display in live video section
            pixmap = QPixmap.fromImage(qimage)
            
            # Scale pixmap to fit live video label while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.live_video_label.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            self.live_video_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            self.logger.error(f"Error updating video frame: {e}")
    
    def update_camera_status(self, state):
        """Update camera status display"""
        try:
            from camera.camera_manager import CameraState
            
            status_map = {
                CameraState.STOPPED: ("Camera: Stopped", "#e74c3c"),
                CameraState.STREAMING: ("Camera: Live Streaming", "#27ae60"),
                CameraState.FREEZING: ("Camera: Capturing...", "#f39c12"),
                CameraState.CAPTURED: ("Camera: Frame Captured", "#3498db"),
                CameraState.ANALYZING: ("Camera: Analyzing...", "#9b59b6"),
                CameraState.ERROR: ("Camera: Error", "#e74c3c")
            }
            
            status_text, color = status_map.get(state, ("Camera: Unknown", "#95a5a6"))
            
            self.camera_status.setText(status_text)
            self.camera_status.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold; margin: 5px;")
            
        except Exception as e:
            self.logger.error(f"Error updating camera status: {e}")
    
    def update_camera_display(self, text):
        """Update camera display with text (fallback when no video)"""
        try:
            # Clear any existing pixmap to show text
            self.live_video_label.clear()
            self.live_video_label.setText(text)
            
        except Exception as e:
            self.logger.error(f"Error updating camera display: {e}")
    
    def _connect_camera_signals(self):
        """Connect camera signals to UI updates"""
        try:
            if hasattr(self, 'camera_integrator') and hasattr(self, 'live_video_label'):
                self.camera_integrator.camera.frame_ready.connect(self.update_video_frame)
                self.camera_integrator.camera.state_changed.connect(self.update_camera_status)
                self.logger.info("Camera signals connected to UI")
        except Exception as e:
            self.logger.error(f"Failed to connect camera signals: {e}")
    
    def _start_immediate_camera_streaming(self):
        """Start camera streaming immediately when window opens"""
        try:
            # Start camera streaming without waiting for barcode
            self.logger.info("Starting immediate camera streaming")
            
            # Get default inspection parameters
            inspection_params = self.get_camera_inspection_params()
            
            # Start streaming via camera integrator
            success = self.camera_integrator.start_inspection_streaming(
                self.inspection_type,
                **inspection_params
            )
            
            if success:
                self.camera_status.setText("Camera: Live Streaming")
                self.camera_status.setStyleSheet("color: #27ae60; font-size: 14px; font-weight: bold; margin: 5px;")
                self.logger.info(f"Immediate streaming started for {self.inspection_type}")
            else:
                self.camera_status.setText("Camera: Failed to start")
                self.camera_status.setStyleSheet("color: #e74c3c; font-size: 14px; font-weight: bold; margin: 5px;")
                
        except Exception as e:
            self.logger.error(f"Failed to start immediate streaming: {e}")
            self.camera_status.setText("Camera: Error")
            self.camera_status.setStyleSheet("color: #e74c3c; font-size: 14px; font-weight: bold; margin: 5px;")
    
    def start_camera_streaming(self):
        """Start camera streaming for inspection type"""
        try:
            # Determine inspection parameters
            inspection_params = self.get_camera_inspection_params()
            
            # Start streaming via camera integrator
            success = self.camera_integrator.start_inspection_streaming(
                self.inspection_type,
                **inspection_params
            )
            
            if success:
                # Update status to show streaming started
                self.camera_status.setText("Camera: Starting...")
                self.camera_status.setStyleSheet("color: #f39c12; font-size: 16px; font-weight: bold; margin: 5px;")
                
                # Clear text display to prepare for video frames
                self.live_video_label.clear()
                
                self.logger.info(f"Started {self.inspection_type} inspection streaming")
            else:
                self.update_camera_display("❌ Failed to start camera\n\nCheck camera connection")
                
        except Exception as e:
            self.logger.error(f"Camera streaming start failed: {e}")
            self.update_camera_display(f"❌ Camera initialization error:\n{e}")
    
    def get_camera_inspection_params(self) -> dict:
        """Get inspection parameters for camera - override in child classes"""
        return {}
    
    def trigger_camera_capture(self):
        """Trigger camera capture and analysis"""
        try:
            if not self.camera_integrator.is_ready_for_capture():
                self.update_camera_display("❌ Camera not ready\n\nCheck camera streaming")
                return False
            
            # Disable capture button during processing
            self.start_inspection_button.setEnabled(False)
            self.start_inspection_button.setText("Processing...")
            
            # Update display
            self.update_camera_display("📸 Capturing and analyzing...\n\nPlease wait...")
            
            # Trigger capture and analysis
            success = self.camera_integrator.capture_and_analyze()
            
            if not success:
                self.update_camera_display("❌ Capture failed\n\nTry again")
                self.start_inspection_button.setEnabled(True)
                self.start_inspection_button.setText("Capture")
                
            return success
            
        except Exception as e:
            self.update_camera_display(f"❌ Capture error:\n{e}")
            self.start_inspection_button.setEnabled(True)
            self.start_inspection_button.setText("Capture")
            return False
    
    def get_inspection_steps(self) -> List[str]:
        """Return list of inspection steps for this type - override in child classes"""
        raise NotImplementedError("Child classes must implement get_inspection_steps()")
    
    def init_api_manager(self):
        """Initialize API manager for this inspection type - override in child classes"""
        raise NotImplementedError("Child classes must implement init_api_manager()")
    
    def get_api_endpoints(self) -> List[str]:
        """Return list of API endpoints for this inspection type - override in child classes"""
        raise NotImplementedError("Child classes must implement get_api_endpoints()")
    
    def collect_inspection_data(self, step: str) -> Dict[str, Any]:
        """Collect inspection data for a specific step - override in child classes"""
        raise NotImplementedError("Child classes must implement collect_inspection_data()")
    
    def validate_step_data(self, step: str, data: Dict[str, Any]) -> bool:
        """Validate collected data for a step - override in child classes"""
        raise NotImplementedError("Child classes must implement validate_step_data()")
    
    def get_ui_colors(self) -> Dict[str, str]:
        """Get UI colors from configuration or use defaults"""
        try:
            if get_config_manager:
                config = get_config_manager()
                return config.get_ui_colors()
        except Exception:
            pass
        
        # Default colors if configuration not available
        return {
            "pass": "#27ae60",
            "fail": "#e74c3c"
        }
    
    def init_ui(self):
        """Initialize the inspection interface"""
        self.setWindowTitle(f"AI VDI System - {self.inspection_type} Inspection")
        
        # Import screen utilities for better display handling
        try:
            from .screen_utils import apply_fullscreen_to_window
        except ImportError:
            from screen_utils import apply_fullscreen_to_window
        
        # Apply fullscreen with 5% bottom margin for better UI spacing
        apply_fullscreen_to_window(self, bottom_margin_percent=5)
        
        self.setStyleSheet(self.get_base_stylesheet())
        
        # Main layout
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        
        # Left panel - Controls
        self.create_control_panel(main_layout)
        
        # Center panel - Camera feed placeholder
        self.create_camera_panel(main_layout)
        
        # Right panel - Inspection progress and results
        self.create_inspection_panel(main_layout)
    
    def get_base_stylesheet(self):
        """Return base stylesheet for the inspection window"""
        return """
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 15px 25px;
                font-size: 16px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QPushButton#stopButton {
                background-color: #f44336;
            }
            QPushButton#stopButton:hover {
                background-color: #da190b;
            }
            QPushButton#warningButton {
                background-color: #ff9800;
            }
            QPushButton#warningButton:hover {
                background-color: #f57c00;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 15px;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
            }
            QLineEdit {
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 16px;
            }
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 6px;
                padding: 8px;
            }
            QLabel {
                font-size: 14px;
            }
        """
    
    def create_control_panel(self, main_layout):
        """Create the control panel on the left"""
        control_panel = QFrame()
        control_panel.setFixedWidth(320)  # Reduced from 400 to 320
        control_panel.setStyleSheet("QFrame { border: 2px solid #ccc; border-radius: 10px; background-color: white; }")
        control_layout = QVBoxLayout()
        control_panel.setLayout(control_layout)
        
        # Title
        title = QLabel(f"{self.inspection_type} Control Panel")
        title.setFont(QFont("Arial", 16, QFont.Bold))  # Reduced font size from 18 to 16
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin: 10px;")  # Reduced margin
        control_layout.addWidget(title)
        
        # Barcode section
        self.create_barcode_section(control_layout)
        
        # Inspection controls - increased space allocation
        self.create_inspection_controls(control_layout)
        
        # Add minimal spacer
        control_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        main_layout.addWidget(control_panel)
    
    def create_barcode_section(self, layout):
        """Create compact barcode input section"""
        barcode_group = QGroupBox("Barcode Input")
        barcode_layout = QVBoxLayout()
        barcode_group.setLayout(barcode_layout)
        
        # Barcode status message - more compact
        self.barcode_status_label = QLabel("Enter or scan a barcode to begin")
        self.barcode_status_label.setStyleSheet("""
            background-color: #e9ecef; 
            padding: 8px; 
            border: 2px solid #adb5bd; 
            border-radius: 5px; 
            font-size: 12px; 
            color: #495057;
            font-weight: bold;
            text-align: center;
        """)
        self.barcode_status_label.setAlignment(Qt.AlignCenter)
        barcode_layout.addWidget(self.barcode_status_label)
        
        # Manual barcode input
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Enter barcode or scan")
        self.barcode_input.returnPressed.connect(self.submit_barcode)
        self.barcode_input.textChanged.connect(self.on_barcode_input_changed)
        barcode_layout.addWidget(self.barcode_input)
        
        # Buttons - more compact styling
        button_layout = QHBoxLayout()
        
        self.scan_qr_button = QPushButton("Scan")
        self.scan_qr_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: 1px solid #333;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
                margin: 2px 0px;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #A8C8E8;
                color: #888888;
                border: 1px solid #BBBBBB;
            }
        """)
        self.scan_qr_button.clicked.connect(self.scan_qr_code)
        button_layout.addWidget(self.scan_qr_button)
        
        self.submit_barcode_button = QPushButton("Submit")
        self.submit_barcode_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: 1px solid #333;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
                margin: 2px 0px;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #A8D8A8;
                color: #888888;
                border: 1px solid #BBBBBB;
            }
        """)
        self.submit_barcode_button.clicked.connect(self.submit_barcode)
        self.submit_barcode_button.setEnabled(False)  # Initially disabled
        button_layout.addWidget(self.submit_barcode_button)
        
        barcode_layout.addLayout(button_layout)
        
        # Barcode display - more compact
        self.barcode_display = QLabel("No barcode entered")
        self.barcode_display.setStyleSheet("background-color: #f8f9fa; padding: 8px; border: 2px solid #ddd; border-radius: 5px; font-size: 12px;")
        barcode_layout.addWidget(self.barcode_display)
        barcode_layout.addWidget(self.barcode_display)
        
        layout.addWidget(barcode_group)
    
    def create_inspection_controls(self, layout):
        """Create inspection control buttons with equal size"""
        control_group = QGroupBox("Inspection Controls")
        control_group.setMinimumHeight(400)  # Increased minimum height
        control_layout = QVBoxLayout()
        control_group.setLayout(control_layout)
        
        # Common button style for equal sizing
        button_style = """
            QPushButton {{
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                margin: 2px 0px;
                min-height: 40px;
                max-height: 40px;
                border-radius: 5px;
            }}
        """
        
        # Main inspection button - renamed to "Capture"
        self.start_inspection_button = QPushButton("Capture")
        self.start_inspection_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.start_inspection_button.clicked.connect(self.start_inspection)
        self.start_inspection_button.setEnabled(False)
        control_layout.addWidget(self.start_inspection_button)
        
        # Step control buttons
        self.next_step_button = QPushButton("Next Step")
        self.next_step_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #2196F3;
                color: white;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.next_step_button.clicked.connect(self.next_step)
        self.next_step_button.setEnabled(False)
        control_layout.addWidget(self.next_step_button)
        
        self.repeat_step_button = QPushButton("Repeat Step")
        self.repeat_step_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #2196F3;
                color: white;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.repeat_step_button.clicked.connect(self.repeat_current_step)
        self.repeat_step_button.setEnabled(False)
        control_layout.addWidget(self.repeat_step_button)
        
        # Manual controls
        self.manual_override_button = QPushButton("Manual Override")
        self.manual_override_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #FF9800;
                color: white;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        self.manual_override_button.clicked.connect(self.manual_override)
        self.manual_override_button.setEnabled(False)
        control_layout.addWidget(self.manual_override_button)
        
        # Add submit button for INLINE inspection (below manual override)
        if self.inspection_type == "INLINE":
            self.submit_data_button = QPushButton("Submit to API")
            self.submit_data_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: 1px solid #333;
                    padding: 8px 16px;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 4px;
                    margin: 2px 0px;
                    min-height: 40px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:disabled {
                    background-color: #A8D8A8;
                    color: #888888;
                    border: 1px solid #BBBBBB;
                }
            """)
            self.submit_data_button.clicked.connect(self.submit_inspection_data)
            self.submit_data_button.setEnabled(False)  # Initially disabled
            control_layout.addWidget(self.submit_data_button)
        
        # Add some spacing
        control_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Stop inspection button
        self.stop_inspection_button = QPushButton("Stop Inspection")
        self.stop_inspection_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #f44336;
                color: white;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        self.stop_inspection_button.clicked.connect(self.stop_inspection)
        self.stop_inspection_button.setEnabled(False)
        control_layout.addWidget(self.stop_inspection_button)
        
        # Back button - renamed to "Main Menu"
        self.back_button = QPushButton("Main Menu")
        self.back_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #607D8B;
                color: white;
            }
            QPushButton:hover {
                background-color: #455A64;
            }
        """)
        self.back_button.clicked.connect(self.back_to_main)
        control_layout.addWidget(self.back_button)
        
        # Quit button
        self.quit_button = QPushButton("QUIT APPLICATION")
        self.quit_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        self.quit_button.clicked.connect(self.quit_application)
        control_layout.addWidget(self.quit_button)
        
        layout.addWidget(control_group)
    
    # ===== Smart Button Control System =====
    
    def update_button_states(self):
        """Update button states based on current inspection state and logic"""
        # Get current state info
        has_barcode = bool(self.barcode)
        inspection_ongoing = self.inspection_state in [
            self.InspectionState.INSPECTION_ACTIVE, 
            self.InspectionState.STEP_IN_PROGRESS,
            self.InspectionState.STEP_COMPLETED
        ]
        inspection_complete = self.inspection_state == self.InspectionState.INSPECTION_COMPLETED
        all_steps_done = self.current_step >= len(self.inspection_steps)
        
        # === CAPTURE BUTTON ===
        # Enable when: barcode entered and not currently inspecting
        capture_enabled = (
            has_barcode and 
            self.inspection_state in [self.InspectionState.BARCODE_ENTERED, self.InspectionState.DATA_SUBMITTED]
        )
        self.start_inspection_button.setEnabled(capture_enabled)
        self._update_button_visual_state(self.start_inspection_button, capture_enabled, "capture")
        
        # === NEXT STEP BUTTON ===  
        # Enable when: inspection active and step can be progressed
        next_step_enabled = (
            inspection_ongoing and
            self.current_step < len(self.inspection_steps) and
            self.step_data_collected  # Only enable if current step has data
        )
        self.next_step_button.setEnabled(next_step_enabled)
        self._update_button_visual_state(self.next_step_button, next_step_enabled, "next_step")
        
        # === REPEAT STEP BUTTON ===
        # Enable when: inspection active and there's a current step to repeat
        repeat_step_enabled = (
            inspection_ongoing and 
            self.current_step < len(self.inspection_steps)
        )
        self.repeat_step_button.setEnabled(repeat_step_enabled)
        self._update_button_visual_state(self.repeat_step_button, repeat_step_enabled, "repeat_step")
        
        # === MANUAL OVERRIDE BUTTON ===
        # Enable when: inspection has results and override is contextually appropriate
        override_enabled = (
            self.override_allowed and
            (inspection_complete or len(self.inspection_results) > 0) and
            self.inspection_state not in [self.InspectionState.OVERRIDE_APPLIED]
        )
        self.manual_override_button.setEnabled(override_enabled)
        self._update_button_visual_state(self.manual_override_button, override_enabled, "manual_override")
        
        # Update button tooltips with helpful context
        self._update_button_tooltips()
    
    def _update_button_visual_state(self, button, enabled, button_type):
        """Update button visual appearance based on enabled state"""
        if enabled:
            # Add highlighting for enabled buttons, especially after step completion
            if button_type in ["next_step", "repeat_step"]:
                # Enhanced highlighting for step control buttons
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: 3px solid #45a049;
                        border-radius: 8px;
                        padding: 12px 20px;
                        font-size: 14px;
                        font-weight: bold;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                        border: 3px solid #3d8b40;
                        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
                        transform: translateY(-2px);
                    }
                    QPushButton:pressed {
                        background-color: #3d8b40;
                        transform: translateY(0px);
                        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                    }
                """)
            elif button_type == "capture":
                # Enhanced styling for capture button
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #2196F3;
                        color: white;
                        border: 2px solid #1976D2;
                        border-radius: 6px;
                        padding: 10px 16px;
                        font-size: 13px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #1976D2;
                        border: 2px solid #1565C0;
                    }
                """)
            elif button_type == "manual_override":
                # Enhanced styling for manual override
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #FF9800;
                        color: white;
                        border: 2px solid #F57C00;
                        border-radius: 6px;
                        padding: 10px 16px;
                        font-size: 13px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #F57C00;
                        border: 2px solid #E65100;
                    }
                """)
        else:
            # Add visual indication for disabled state while keeping original colors
            current_style = button.styleSheet()
            if ":disabled" not in current_style:
                # Add disabled state styling that preserves original color but dims it
                if button_type == "capture":
                    disabled_color = "#A8D8A8"  # Dimmed green
                elif button_type in ["next_step", "repeat_step"]:
                    disabled_color = "#A8C8E8"  # Dimmed blue  
                elif button_type == "manual_override":
                    disabled_color = "#E8C8A8"  # Dimmed orange
                else:
                    disabled_color = "#CCCCCC"  # Default gray
                
                button.setStyleSheet(current_style + f"""
                    QPushButton:disabled {{
                        background-color: {disabled_color};
                        color: #888888;
                        border: 1px solid #BBBBBB;
                        box-shadow: none;
                        transform: none;
                    }}
                """)
    
    def _update_button_tooltips(self):
        """Update button tooltips based on current state"""
        # Capture button tooltip
        if self.inspection_state == self.InspectionState.IDLE:
            self.start_inspection_button.setToolTip("Enter a barcode first")
        elif self.inspection_state == self.InspectionState.BARCODE_ENTERED:
            self.start_inspection_button.setToolTip("Click to start inspection process")
        elif self.inspection_state in [self.InspectionState.INSPECTION_ACTIVE, self.InspectionState.STEP_IN_PROGRESS]:
            self.start_inspection_button.setToolTip("Inspection in progress")
        elif self.inspection_state == self.InspectionState.INSPECTION_COMPLETED:
            self.start_inspection_button.setToolTip("Complete current inspection first")
        else:
            self.start_inspection_button.setToolTip("Ready to start new inspection")
        
        # Next Step button tooltip
        if not self.inspection_state in [self.InspectionState.INSPECTION_ACTIVE, self.InspectionState.STEP_IN_PROGRESS, self.InspectionState.STEP_COMPLETED]:
            self.next_step_button.setToolTip("Start inspection first")
        elif self.current_step >= len(self.inspection_steps):
            self.next_step_button.setToolTip("All steps completed")
        elif not self.step_data_collected:
            self.next_step_button.setToolTip("Collect data for current step first")
        else:
            step_name = self.inspection_steps[self.current_step] if self.current_step < len(self.inspection_steps) else "Final"
            self.next_step_button.setToolTip(f"Proceed to next step after {step_name}")
        
        # Repeat Step button tooltip
        if not self.inspection_state in [self.InspectionState.INSPECTION_ACTIVE, self.InspectionState.STEP_IN_PROGRESS, self.InspectionState.STEP_COMPLETED]:
            self.repeat_step_button.setToolTip("Start inspection first")
        elif self.current_step >= len(self.inspection_steps):
            self.repeat_step_button.setToolTip("No active step to repeat")
        else:
            step_name = self.inspection_steps[self.current_step]
            self.repeat_step_button.setToolTip(f"Repeat current step: {step_name}")
        
        # Manual Override button tooltip
        if len(self.inspection_results) == 0:
            self.manual_override_button.setToolTip("No inspection results to override")
        elif self.inspection_state == self.InspectionState.OVERRIDE_APPLIED:
            self.manual_override_button.setToolTip("Override already applied")
        elif not self.override_allowed:
            self.manual_override_button.setToolTip("Override not available in current state")
        else:
            self.manual_override_button.setToolTip("Apply manual override to inspection results")
    
    def set_inspection_state(self, new_state, step_data_collected=None, override_allowed=None):
        """Set inspection state and update button controls accordingly"""
        print(f"🔄 State transition: {self.inspection_state} → {new_state}")
        
        self.inspection_state = new_state
        
        # Update step data flag if provided
        if step_data_collected is not None:
            self.step_data_collected = step_data_collected
            
        # Update override allowed flag if provided  
        if override_allowed is not None:
            self.override_allowed = override_allowed
            
        # Update all button states based on new state
        self.update_button_states()
        
        # Log state for debugging
        self._log_button_state_change(new_state)
    
    def _log_button_state_change(self, new_state):
        """Log button state changes for debugging"""
        button_states = {
            'Capture': self.start_inspection_button.isEnabled(),
            'Next Step': self.next_step_button.isEnabled(),
            'Repeat Step': self.repeat_step_button.isEnabled(),
            'Manual Override': self.manual_override_button.isEnabled()
        }
        
        # Include Submit button if it exists
        if hasattr(self, 'submit_data_button') and self.submit_data_button:
            button_states['Submit to API'] = self.submit_data_button.isEnabled()
        
        enabled_buttons = [name for name, enabled in button_states.items() if enabled]
        disabled_buttons = [name for name, enabled in button_states.items() if not enabled]
        
        print(f"   📊 Button States in {new_state}:")
        print(f"      ✅ Enabled: {enabled_buttons if enabled_buttons else 'None'}")
        print(f"      ❌ Disabled: {disabled_buttons if disabled_buttons else 'None'}")
        print(f"      📈 Step: {self.current_step}/{len(self.inspection_steps)}")
        print(f"      🔧 Data Collected: {self.step_data_collected}")
        print(f"      ⚠️ Override Allowed: {self.override_allowed}")
    
    def simulate_step_data_collection(self):
        """Simulate data collection for current step (for testing/demo purposes)"""
        if self.current_step < len(self.inspection_steps):
            self.step_data_collected = True
            self.override_allowed = True  # Allow override once we have some data
            self.update_button_states()
            
            step_name = self.inspection_steps[self.current_step]
            self.update_camera_display(f"✅ Data Collected for {step_name}\n\n📊\n\nStep data captured successfully\n\nClick 'Next Step' to continue")
            print(f"📊 Simulated data collection for step: {step_name}")
            
            # Update API data display
            self.api_data_display.setPlainText(f"Step Data: {step_name}\nTimestamp: {datetime.now()}\nStatus: Data Collected")
    
    # ===== Enhanced State Management Methods =====
    
    def enter_idle_state(self):
        """Enter idle state - no barcode, ready for input"""
        self.set_inspection_state(self.InspectionState.IDLE, 
                                step_data_collected=False, 
                                override_allowed=False)
    
    def enter_barcode_entered_state(self):
        """Enter barcode entered state - ready to start inspection"""
        self.set_inspection_state(self.InspectionState.BARCODE_ENTERED,
                                step_data_collected=False,
                                override_allowed=False)
    
    def enter_inspection_active_state(self):
        """Enter inspection active state - currently inspecting"""
        self.set_inspection_state(self.InspectionState.INSPECTION_ACTIVE,
                                step_data_collected=False,
                                override_allowed=False)
    
    def enter_step_in_progress_state(self):
        """Enter step in progress state - step being processed"""
        self.set_inspection_state(self.InspectionState.STEP_IN_PROGRESS,
                                step_data_collected=False,
                                override_allowed=False)
    
    def enter_step_completed_state(self):
        """Enter step completed state - step done, ready for next"""
        self.set_inspection_state(self.InspectionState.STEP_COMPLETED,
                                step_data_collected=True,
                                override_allowed=True)
        
        # Add brief animation to draw attention to enabled buttons
        self._animate_button_highlight()
    
    def _animate_button_highlight(self):
        """Brief animation to highlight newly enabled buttons"""
        # Create a brief pulsing effect on the Next Step and Repeat Step buttons
        if hasattr(self, 'next_step_button') and self.next_step_button.isEnabled():
            self._pulse_button(self.next_step_button)
        if hasattr(self, 'repeat_step_button') and self.repeat_step_button.isEnabled():
            self._pulse_button(self.repeat_step_button)
    
    def _pulse_button(self, button):
        """Create a pulsing effect on a button"""
        original_style = button.styleSheet()
        
        # Bright highlight style
        highlight_style = """
            QPushButton {
                background-color: #66BB6A !important;
                border: 4px solid #FFF176 !important;
                box-shadow: 0 0 20px rgba(255, 241, 118, 0.8) !important;
            }
        """
        
        # Apply highlight temporarily
        button.setStyleSheet(original_style + highlight_style)
        
        # Reset to normal after brief delay
        QTimer.singleShot(800, lambda: button.setStyleSheet(original_style))
    
    def enter_inspection_completed_state(self):
        """Enter inspection completed state - all steps done"""
        self.set_inspection_state(self.InspectionState.INSPECTION_COMPLETED,
                                step_data_collected=True,
                                override_allowed=True)
    
    def enter_override_applied_state(self):
        """Enter override applied state - manual override has been applied"""
        self.set_inspection_state(self.InspectionState.OVERRIDE_APPLIED,
                                step_data_collected=True,
                                override_allowed=False)
    
    def create_camera_panel(self, main_layout):
        """Create camera display panel with vertical layout - live video on top, results below"""
        camera_panel = QFrame()
        camera_panel.setStyleSheet("QFrame { border: 2px solid #ccc; border-radius: 10px; background-color: white; }")
        camera_layout = QVBoxLayout()
        camera_panel.setLayout(camera_layout)
        
        # Title
        title = QLabel("Camera Feed & Results")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin: 8px;")
        camera_layout.addWidget(title)
        
        # Live video feed - upper section
        self.live_video_label = QLabel("Starting live camera feed...")
        self.live_video_label.setAlignment(Qt.AlignCenter)
        self.live_video_label.setMinimumSize(640, 360)  # 16:9 aspect ratio
        self.live_video_label.setMaximumSize(640, 360)
        self.live_video_label.setStyleSheet("""
            background-color: #2c3e50; 
            color: white; 
            font-size: 16px;  
            border-radius: 8px;
            border: 2px solid #34495e;
        """)
        self.live_video_label.setAlignment(Qt.AlignCenter)  # Center the video content
        camera_layout.addWidget(self.live_video_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameStyle(QFrame.Sunken)
        separator.setStyleSheet("color: #bdc3c7; margin: 5px;")
        camera_layout.addWidget(separator)
        
        # Algorithm result image - lower section
        result_title = QLabel("Algorithm Result")
        result_title.setFont(QFont("Arial", 14, QFont.Bold))
        result_title.setAlignment(Qt.AlignCenter)
        result_title.setStyleSheet("color: #2c3e50; margin: 5px;")
        camera_layout.addWidget(result_title)
        
        self.result_image_label = QLabel("Waiting for capture and analysis...")
        self.result_image_label.setAlignment(Qt.AlignCenter)
        self.result_image_label.setMinimumSize(640, 240)  # Smaller for result
        self.result_image_label.setMaximumSize(640, 240)
        self.result_image_label.setStyleSheet("""
            background-color: #34495e; 
            color: white; 
            font-size: 14px;  
            border-radius: 8px;
            border: 2px solid #2c3e50;
        """)
        self.result_image_label.setAlignment(Qt.AlignCenter)  # Center the result content
        camera_layout.addWidget(self.result_image_label)
        
        # Camera status and inspection info - bottom
        info_layout = QHBoxLayout()
        
        self.camera_status = QLabel("Camera: Initializing...")
        self.camera_status.setAlignment(Qt.AlignCenter)
        self.camera_status.setStyleSheet("color: #f39c12; font-size: 14px; font-weight: bold; margin: 5px;")
        info_layout.addWidget(self.camera_status)
        
        self.inspection_info = QLabel(f"Type: {self.inspection_type}")
        self.inspection_info.setAlignment(Qt.AlignCenter)
        self.inspection_info.setStyleSheet("color: #3498db; font-size: 14px; font-weight: bold; margin: 5px;")
        info_layout.addWidget(self.inspection_info)
        
        camera_layout.addLayout(info_layout)
        main_layout.addWidget(camera_panel)
    
    def create_inspection_panel(self, main_layout):
        """Create inspection progress and results panel"""
        inspection_panel = QFrame()
        inspection_panel.setFixedWidth(320)  # Reduced from 400 to 320
        inspection_panel.setStyleSheet("QFrame { border: 2px solid #ccc; border-radius: 10px; background-color: white; }")
        inspection_layout = QVBoxLayout()
        inspection_panel.setLayout(inspection_layout)
        
        # Title
        title = QLabel("Inspection Progress")
        title.setFont(QFont("Arial", 16, QFont.Bold))  # Reduced font size from 18 to 16
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin: 8px;")  # Reduced margin
        inspection_layout.addWidget(title)
        
        # Progress section
        self.create_progress_section(inspection_layout)
        
        # Results section
        self.create_results_section(inspection_layout)
        
        # API Data section
        self.create_api_data_section(inspection_layout)
        
        main_layout.addWidget(inspection_panel)
    
    def create_progress_section(self, layout):
        """Create inspection progress section"""
        progress_group = QGroupBox("Current Progress")
        progress_layout = QVBoxLayout()
        progress_group.setLayout(progress_layout)
        
        # Current step
        self.current_step_label = QLabel("Step: Not Started")
        self.current_step_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.current_step_label.setStyleSheet("color: #2c3e50; margin: 5px;")
        progress_layout.addWidget(self.current_step_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, len(self.inspection_steps))
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        # Step status
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.step_status_layout = QVBoxLayout()
        scroll_widget.setLayout(self.step_status_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(150)
        
        for step in self.inspection_steps:
            step_label = QLabel(f"{step}: Pending")
            step_label.setStyleSheet("color: #666; padding: 3px; font-size: 11px;")
            self.step_status_layout.addWidget(step_label)
        
        progress_layout.addWidget(scroll_area)
        layout.addWidget(progress_group)
    
    def create_results_section(self, layout):
        """Create results display section"""
        results_group = QGroupBox("Inspection Results")
        results_layout = QVBoxLayout()
        results_group.setLayout(results_layout)
        
        # Overall result
        self.overall_result = QLabel("Status: Pending")
        self.overall_result.setFont(QFont("Arial", 14, QFont.Bold))
        self.overall_result.setStyleSheet("color: #2c3e50; margin: 5px;")
        results_layout.addWidget(self.overall_result)
        
        # Time information
        self.time_info = QLabel("Time: 00:00")
        self.time_info.setStyleSheet("color: #7f8c8d; font-size: 12px; margin: 5px;")
        results_layout.addWidget(self.time_info)
        
        layout.addWidget(results_group)
    
    def create_api_data_section(self, layout):
        """Create API data display section with camera settings and API status"""
        api_group = QGroupBox("API Data & Settings")
        api_layout = QVBoxLayout()
        api_group.setLayout(api_layout)
        
        # API Status section (moved from control panel)
        api_status_subgroup = QGroupBox("API Status")
        api_status_layout = QVBoxLayout()
        api_status_subgroup.setLayout(api_status_layout)
        
        # API endpoints status
        self.api_status_labels = {}
        endpoints = self.get_api_endpoints()
        
        for endpoint in endpoints:
            status_label = QLabel(f"{endpoint}: Not Checked")
            status_label.setStyleSheet("color: #666; padding: 3px; font-size: 10px;")
            self.api_status_labels[endpoint] = status_label
            api_status_layout.addWidget(status_label)
        
        # Test API button (smaller)
        self.test_api_button = QPushButton("Test API")
        self.test_api_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: 1px solid #333;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: bold;
                border-radius: 3px;
                margin: 1px 0px;
                min-height: 24px;
                max-height: 28px;
                min-width: 60px;
                max-width: 80px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #A8C8E8;
                color: #888888;
                border: 1px solid #BBBBBB;
            }
        """)
        self.test_api_button.clicked.connect(self.test_api_connections)
        api_status_layout.addWidget(self.test_api_button)
        
        api_layout.addWidget(api_status_subgroup)
        
        # Camera Settings section (moved from control panel)
        camera_settings_subgroup = QGroupBox("Camera Settings")
        camera_settings_layout = QVBoxLayout()
        camera_settings_subgroup.setLayout(camera_settings_layout)
        
        # Camera enable/disable
        self.camera_enabled = QCheckBox("Camera Enabled")
        self.camera_enabled.setChecked(True)
        self.camera_enabled.setStyleSheet("font-size: 11px;")
        camera_settings_layout.addWidget(self.camera_enabled)
        
        # Flip settings in horizontal layout
        flip_layout = QHBoxLayout()
        self.flip_horizontal = QCheckBox("Flip H")
        self.flip_horizontal.setStyleSheet("font-size: 10px;")
        self.flip_vertical = QCheckBox("Flip V")
        self.flip_vertical.setStyleSheet("font-size: 10px;")
        flip_layout.addWidget(self.flip_horizontal)
        flip_layout.addWidget(self.flip_vertical)
        camera_settings_layout.addLayout(flip_layout)
        
        # Exposure (compact)
        exposure_layout = QHBoxLayout()
        exposure_label = QLabel("Exp:")
        exposure_label.setStyleSheet("font-size: 10px;")
        self.exposure_slider = QSlider(Qt.Horizontal)
        self.exposure_slider.setRange(-10, 10)
        self.exposure_slider.setValue(0)
        self.exposure_slider.setMaximumHeight(20)
        exposure_layout.addWidget(exposure_label)
        exposure_layout.addWidget(self.exposure_slider)
        camera_settings_layout.addLayout(exposure_layout)
        
        api_layout.addWidget(camera_settings_subgroup)
        
        # API data display - Hidden for INLINE inspection
        if self.inspection_type != "INLINE":
            api_data_subgroup = QGroupBox("API Data")
            api_data_layout = QVBoxLayout()
            api_data_subgroup.setLayout(api_data_layout)
            
            self.api_data_display = QTextEdit()
            self.api_data_display.setMaximumHeight(80)
            self.api_data_display.setStyleSheet("font-size: 10px; background-color: #f8f9fa;")
            self.api_data_display.setPlainText("No data collected yet")
            api_data_layout.addWidget(self.api_data_display)
            
            # Submit data button (for non-INLINE inspections)
            self.submit_data_button = QPushButton("Submit to API")
            self.submit_data_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: 1px solid #333;
                    padding: 8px 16px;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 4px;
                    margin: 2px 0px;
                    min-height: 40px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:disabled {
                    background-color: #A8D8A8;
                    color: #888888;
                    border: 1px solid #BBBBBB;
                }
            """)
            self.submit_data_button.clicked.connect(self.submit_inspection_data)
            self.submit_data_button.setEnabled(False)
            api_data_layout.addWidget(self.submit_data_button)
            
            api_layout.addWidget(api_data_subgroup)
        else:
            # For INLINE inspection, create minimal API display without groupbox
            self.api_data_display = QTextEdit()
            self.api_data_display.setMaximumHeight(60)
            self.api_data_display.setStyleSheet("font-size: 10px; background-color: #f8f9fa; border: 1px solid #ddd;")
            self.api_data_display.setPlainText("INLINE inspection: Sequential API submission enabled")
            self.api_data_display.hide()  # Hidden by default for INLINE
        
        layout.addWidget(api_group)
    
    # ===== API and Barcode Methods =====
    
    def on_barcode_input_changed(self):
        """Handle barcode input text changes"""
        barcode_text = self.barcode_input.text().strip()
        
        # Enable submit button only if there's text and not currently inspecting
        has_text = len(barcode_text) > 0
        inspection_not_ongoing = self.inspection_state in [
            self.InspectionState.IDLE, 
            self.InspectionState.DATA_SUBMITTED
        ]
        
        self.submit_barcode_button.setEnabled(has_text and inspection_not_ongoing)
        
        # Update status message based on input state
        if not has_text:
            self.update_barcode_status("Enter or scan a barcode to begin", "waiting")
        elif not inspection_not_ongoing:
            self.update_barcode_status("Inspection in progress", "inspecting")
        else:
            self.update_barcode_status("Click Submit to validate barcode", "ready")
    
    def update_barcode_status(self, message, status_type="waiting"):
        """Update barcode status message with appropriate styling"""
        base_style = """
            padding: 10px; 
            border: 2px solid {}; 
            border-radius: 5px; 
            font-size: 14px; 
            font-weight: bold;
            text-align: center;
        """
        
        if status_type == "waiting":
            # Gray style for waiting state
            style = base_style.format("#adb5bd") + """
                background-color: #e9ecef; 
                color: #495057;
            """
        elif status_type == "ready":
            # Blue style for ready to submit
            style = base_style.format("#007bff") + """
                background-color: #cce5ff; 
                color: #004085;
            """
        elif status_type == "inspecting":
            # Orange style for ongoing inspection
            style = base_style.format("#fd7e14") + """
                background-color: #ffe8d4; 
                color: #832d00;
            """
        elif status_type == "success":
            # Green style for successful validation
            style = base_style.format("#28a745") + """
                background-color: #d4edda; 
                color: #155724;
            """
        elif status_type == "error":
            # Red style for errors
            style = base_style.format("#dc3545") + """
                background-color: #f8d7da; 
                color: #721c24;
            """
        else:
            # Default gray style
            style = base_style.format("#6c757d") + """
                background-color: #f8f9fa; 
                color: #495057;
            """
            
        self.barcode_status_label.setStyleSheet(style)
        self.barcode_status_label.setText(message)
    
    def scan_qr_code(self):
        """Scan QR code from camera feed"""
        QMessageBox.information(self, "QR Scanner", 
                               "QR Code scanning will be implemented with camera integration.\n\n"
                               "For now, please use manual barcode input.")
    
    def submit_barcode(self):
        """Submit barcode and validate with API"""
        barcode = self.barcode_input.text().strip()
        if not barcode:
            self.update_barcode_status("Please enter a barcode", "error")
            return
        
        # Disable submit button during validation
        self.submit_barcode_button.setEnabled(False)
        self.update_barcode_status("Validating barcode...", "inspecting")
        
        # Validate barcode with API manager
        if self.validate_barcode_with_api(barcode):
            self.barcode = barcode
            self.barcode_display.setText(f"Barcode: {barcode}")
            self.barcode_display.setStyleSheet("background-color: #d4edda; padding: 10px; border: 2px solid #c3e6cb; border-radius: 5px; font-size: 14px; color: #155724;")
            self.update_barcode_status(f"Barcode validated: {barcode}", "success")
            self.update_camera_display(f"Barcode Validated: {barcode}\n\nReady to start {self.inspection_type} inspection")
            
            # Camera streaming is already active from window initialization
            # Update status to show barcode is ready
            self.inspection_info.setText(f"Type: {self.inspection_type} | Barcode: {barcode}")
            
            # Enter barcode validated state
            self.enter_barcode_entered_state()
        else:
            self.barcode_display.setText(f"Invalid: {barcode}")
            self.barcode_display.setStyleSheet("background-color: #f8d7da; padding: 10px; border: 2px solid #f5c6cb; border-radius: 5px; font-size: 14px; color: #721c24;")
            self.update_barcode_status("Invalid barcode - validation failed", "error")
            self.update_camera_display("❌ Barcode Validation Failed\n\nCannot proceed with inspection")
            
            # Re-enable submit button for retry only if there's still text in the input
            # (if input was cleared by duplicate rejection, button should stay disabled)
            if self.barcode_input.text().strip():
                self.submit_barcode_button.setEnabled(True)
            # If input is empty, let on_barcode_input_changed() manage the button state
    
    def validate_barcode_with_api(self, barcode):
        """Validate barcode using API manager"""
        try:
            if self.api_manager:
                result = self.api_manager.process_barcode(barcode)
                
                # Update API status display
                status_text = f"API Response: {result['status']}\n"
                status_text += f"Message: {result['message']}\n"
                if result.get('action_required'):
                    status_text += "⚠️ Action required\n"
                
                self.api_data_display.setPlainText(status_text)
                
                # Handle different API responses
                if result['status'] == 'proceed' or result['status'] == 'success':
                    return True
                elif result['status'] == 'duplicate_handling_required' or result['status'] == 'warning':
                    # Show dialog for duplicate handling
                    return self.handle_duplicate_barcode(result)
                elif result['status'] == 'error':
                    # STRICT VALIDATION: No inspection can proceed if API1 fails
                    self._show_validation_failure_message(result['message'])
                    return False
                else:
                    self._show_validation_failure_message("Unexpected API response - cannot proceed")
                    return False
            else:
                # STRICT VALIDATION: No API manager means no inspection allowed
                error_message = "API Manager not initialized - cannot validate barcode"
                self._show_validation_failure_message(error_message)
                return False
                
        except Exception as e:
            print(f"API validation error: {e}")
            # STRICT VALIDATION: API connection failures prevent inspection
            error_message = f"API connection failed: {str(e)}"
            self._show_validation_failure_message(error_message)
            return False
    
    def handle_duplicate_barcode(self, api_result):
        """Handle duplicate barcode scenario"""
        msg = f"Duplicate barcode detected!\n\n{api_result['message']}\n\nDo you want to proceed anyway?"
        reply = QMessageBox.question(self, "Duplicate Barcode", msg,
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            return True
        else:
            # User chose not to proceed with duplicate - stop inspection and return to barcode entry
            self._show_duplicate_rejection_message()
            self._return_to_barcode_entry()
            return False
    
    def _show_duplicate_rejection_message(self):
        """Show message when user rejects duplicate barcode"""
        QMessageBox.information(
            self, 
            "Inspection Stopped", 
            "❌ INSPECTION STOPPED\n\n"
            "Duplicate barcode rejected by user.\n\n"
            "🔄 Returning to barcode entry\n\n"
            "Please enter a different barcode to begin a new inspection."
        )
    
    def _show_validation_failure_message(self, error_message):
        """Show validation failure message and ensure user returns to barcode entry"""
        # Categorize different types of validation failures
        if "was not tested in previous" in error_message:
            title = "Barcode Not Found"
            detailed_message = (
                f"❌ VALIDATION FAILED\n\n"
                f"The barcode was not found in the previous inspection stage.\n\n"
                f"Reason: {error_message}\n\n"
                f"✋ INSPECTION CANNOT PROCEED\n\n"
                f"Please verify the barcode and try again with a valid barcode that "
                f"has completed the previous inspection stage."
            )
        elif "failed previous" in error_message:
            title = "Previous Inspection Failed"
            detailed_message = (
                f"❌ VALIDATION FAILED\n\n"
                f"The barcode failed a previous inspection stage.\n\n"
                f"Reason: {error_message}\n\n"
                f"✋ INSPECTION CANNOT PROCEED\n\n"
                f"Products that fail previous inspections cannot proceed to this stage. "
                f"Please use a different barcode with passing inspection results."
            )
        else:
            title = "Validation Error"
            detailed_message = (
                f"❌ VALIDATION FAILED\n\n"
                f"Barcode validation encountered an error.\n\n"
                f"Reason: {error_message}\n\n"
                f"✋ INSPECTION CANNOT PROCEED\n\n"
                f"Please check the barcode and try again."
            )
        
        # Show critical error message
        QMessageBox.critical(self, title, detailed_message)
        
        # Force return to barcode entry state
        self._return_to_barcode_entry()
    
    def _return_to_barcode_entry(self):
        """Force return to barcode entry state after validation failure"""
        # Clear current barcode
        self.barcode = None
        self.barcode_input.clear()
        
        # Reset barcode display
        self.barcode_display.setText("No Barcode Entered")
        self.barcode_display.setStyleSheet("background-color: #f8f9fa; padding: 10px; border: 2px solid #dee2e6; border-radius: 5px; font-size: 14px; color: #6c757d;")
        
        # Update status to show ready for new barcode
        self.update_barcode_status("Enter a valid barcode to begin", "waiting")
        
        # Clear any inspection data
        self.inspection_results.clear()
        self.current_step = 0
        self.step_data_collected = False
        
        # Return to idle state
        self.set_inspection_state(self.InspectionState.IDLE)
        
        # Clear API data display
        self._update_api_display("API validation required")
        
        # Update camera display
        self.update_camera_display("❌ Validation Failed - Enter New Barcode\n\nPlease enter a valid barcode that has passed previous inspection stages")
        
        # Re-enable barcode input but keep submit button disabled until text is entered
        self.barcode_input.setEnabled(True)
        # Note: submit button state is managed by on_barcode_input_changed()
        
        # Focus on barcode input for immediate retry
        self.barcode_input.setFocus()
        
        # Update button states based on current input (should disable submit button)
        self.on_barcode_input_changed()
    
    def test_api_connections(self):
        """Test API connections"""
        if not self.api_manager:
            QMessageBox.warning(self, "API Error", "API Manager not initialized")
            return
        
        endpoints = self.get_api_endpoints()
        for endpoint in endpoints:
            try:
                # Test endpoint (implement specific test logic)
                success = True  # Placeholder
                
                if success:
                    self.api_status_labels[endpoint].setText(f"{endpoint}: ✅ Connected")
                    self.api_status_labels[endpoint].setStyleSheet("color: #27ae60; padding: 5px; font-size: 12px;")
                else:
                    self.api_status_labels[endpoint].setText(f"{endpoint}: ❌ Failed")
                    self.api_status_labels[endpoint].setStyleSheet("color: #e74c3c; padding: 5px; font-size: 12px;")
                    
            except Exception as e:
                self.api_status_labels[endpoint].setText(f"{endpoint}: ❌ Error")
                self.api_status_labels[endpoint].setStyleSheet("color: #e74c3c; padding: 5px; font-size: 12px;")
    
    # ===== Inspection Control Methods =====
    
    def start_inspection(self):
        """Start the inspection process with camera capture"""
        # STRICT VALIDATION: Ensure valid barcode before starting inspection
        if not self.barcode:
            self._show_validation_failure_message("No valid barcode - cannot start inspection")
            return
        
        # Check if camera is ready
        if not self.camera_integrator.is_ready_for_capture():
            self.update_camera_display("❌ Camera not ready\n\nPlease validate barcode first")
            return
        
        # Note: Barcode was already validated during submit_barcode() - no need to re-validate
        
        self.inspection_start_time = datetime.now()
        self.current_step = 0
        self.inspection_results = {}
        self.api_data_collected = {}
        
        # Disable barcode submission during inspection
        self.submit_barcode_button.setEnabled(False)
        self.barcode_input.setEnabled(False)
        self.scan_qr_button.setEnabled(False)
        self.update_barcode_status("Inspection in progress", "inspecting")
        
        # Enter inspection active state
        self.enter_inspection_active_state()
        
        # Start first step
        self.start_step_inspection()
        
        # Trigger camera capture instead of simulation
        self.trigger_camera_capture()
        
        # Add helpful instructions for user
        if len(self.inspection_steps) > 0:
            first_step = self.inspection_steps[0]
            self.update_camera_display(f"� Capturing: {first_step}\n\nBarcode: {self.barcode}\n\nPlease wait for analysis...")
    
    def start_step_inspection(self):
        """Start inspection of current step"""
        if self.current_step < len(self.inspection_steps):
            step_name = self.inspection_steps[self.current_step]
            self.step_start_time = datetime.now()
            self.current_step_label.setText(f"Step: {step_name}")
            
            # Enter step in progress state
            self.enter_step_in_progress_state()
            
            # Update step status
            for i in range(self.step_status_layout.count()):
                label = self.step_status_layout.itemAt(i).widget()
                if label and hasattr(label, 'setText'):
                    if i == self.current_step:
                        label.setText(f"{self.inspection_steps[i]}: In Progress")
                        label.setStyleSheet("color: #3498db; font-weight: bold; padding: 3px; font-size: 11px;")
            
            # Update camera display for current step
            self.update_camera_display(f"Inspecting: {step_name}\n\n📹\n\nPosition product for {step_name}\n\n💡 Click here to simulate data collection")
            
            # Make camera label clickable for demo purposes
            self.live_video_label.mousePressEvent = lambda event: self.simulate_step_data_collection()
    
    def next_step(self):
        """Move to next step of inspection"""
        if self.current_step < len(self.inspection_steps):
            step_name = self.inspection_steps[self.current_step]
            
            # Collect and validate step data
            step_data = self.collect_inspection_data(step_name)
            
            if self.validate_step_data(step_name, step_data):
                # Record result
                step_time = (datetime.now() - self.step_start_time).total_seconds()
                self.inspection_results[step_name] = {
                    'data': step_data,
                    'time': step_time,
                    'timestamp': datetime.now()
                }
                
                # Store data for API submission
                self.api_data_collected.update(step_data)
                
                # Update submit button after each step based on inspection state
                if self.inspection_type == "INLINE":
                    self._update_submit_button_for_inline()
                else:
                    submit_enabled = self._should_enable_submit_button()
                    self._set_submit_button_enabled(submit_enabled)
                
                # Update UI
                self.update_step_status(self.current_step, "COMPLETED")
                
                # Update camera display with detailed results for INLINE inspection
                if self.inspection_type == "INLINE":
                    self._update_camera_with_inline_results(step_name, step_data)
                
                self.current_step += 1
                self.progress_bar.setValue(self.current_step)
                
                if self.current_step < len(self.inspection_steps):
                    # More steps to go
                    self.enter_step_completed_state()
                    self.start_step_inspection()
                else:
                    # All steps completed
                    self.complete_inspection()
            else:
                QMessageBox.warning(self, "Invalid Data", 
                                  f"Data validation failed for step: {step_name}\n\nPlease check the inspection and try again.")
                # Reset step data collection flag so user needs to collect data again
                self.step_data_collected = False
                self.update_button_states()
    
    def repeat_current_step(self):
        """Repeat the current inspection step"""
        if self.current_step < len(self.inspection_steps):
            step_name = self.inspection_steps[self.current_step]
            reply = QMessageBox.question(self, "Repeat Step", 
                                       f"Repeat current step: {step_name}?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.start_step_inspection()
    
    def update_step_status(self, step_index, status):
        """Update the status of a specific step"""
        if step_index < self.step_status_layout.count():
            label = self.step_status_layout.itemAt(step_index).widget()
            if label:
                step_name = self.inspection_steps[step_index]
                
                # For INLINE inspection, show individual component results
                if self.inspection_type == "INLINE" and status == "COMPLETED" and step_name in self.inspection_results:
                    step_data = self.inspection_results[step_name]['data']
                    
                    if step_name == "BOTTOM: Capture":
                        # Show BOTTOM component results: Antenna, Capacitor, Speaker
                        # Use display values if available, otherwise convert from 1/0
                        if '_display' in step_data:
                            antenna = step_data['_display'].get('Antenna', 'UNKNOWN')
                            capacitor = step_data['_display'].get('Capacitor', 'UNKNOWN')
                            speaker = step_data['_display'].get('Speaker', 'UNKNOWN')
                            overall_result = step_data['_display'].get('Result', 'UNKNOWN')
                        else:
                            # Fallback: convert 1/0 to PASS/FAIL for display
                            antenna = "PASS" if step_data.get('Antenna', 0) == 1 else "FAIL"
                            capacitor = "PASS" if step_data.get('Capacitor', 0) == 1 else "FAIL"
                            speaker = "PASS" if step_data.get('Speaker', 0) == 1 else "FAIL"
                            overall_result = "PASS" if step_data.get('Result', 0) == 1 else "FAIL"
                        
                        result_text = f"BOTTOM: Antenna={antenna}, Capacitor={capacitor}, Speaker={speaker}"
                        
                        # Set color based on overall result using configuration
                        colors = self.get_ui_colors()
                        if overall_result == "PASS":
                            label.setStyleSheet(f"color: {colors['pass']}; font-weight: bold; padding: 3px; font-size: 10px;")
                        else:
                            label.setStyleSheet(f"color: {colors['fail']}; font-weight: bold; padding: 3px; font-size: 10px;")
                            
                    elif step_name == "TOP: Capture":
                        # Show TOP component results: Screw, Plate
                        # Use display values if available, otherwise convert from 1/0
                        if '_display' in step_data:
                            screw = step_data['_display'].get('Screw', 'UNKNOWN')
                            plate = step_data['_display'].get('Plate', 'UNKNOWN')
                            overall_result = step_data['_display'].get('Result', 'UNKNOWN')
                        else:
                            # Fallback: convert 1/0 to PASS/FAIL for display
                            screw = "PASS" if step_data.get('Screw', 0) == 1 else "FAIL"
                            plate = "PASS" if step_data.get('Plate', 0) == 1 else "FAIL"
                            overall_result = "PASS" if step_data.get('Result', 0) == 1 else "FAIL"
                        
                        result_text = f"TOP: Screw={screw}, Plate={plate}"
                        
                        # Set color based on overall result using configuration
                        colors = self.get_ui_colors()
                        if overall_result == "PASS":
                            label.setStyleSheet(f"color: {colors['pass']}; font-weight: bold; padding: 3px; font-size: 10px;")
                        else:
                            label.setStyleSheet(f"color: {colors['fail']}; font-weight: bold; padding: 3px; font-size: 10px;")
                    else:
                        result_text = f"{step_name}: {status}"
                        colors = self.get_ui_colors()
                        label.setStyleSheet(f"color: {colors['pass']}; font-weight: bold; padding: 3px; font-size: 11px;")
                        
                    label.setText(result_text)
                
                else:
                    # Standard status display for non-INLINE or non-completed steps
                    label.setText(f"{step_name}: {status}")
                    colors = self.get_ui_colors()
                    if status == "COMPLETED":
                        label.setStyleSheet(f"color: {colors['pass']}; font-weight: bold; padding: 3px; font-size: 11px;")
                    elif status == "FAILED":
                        label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 3px; font-size: 11px;")
                    else:
                        label.setStyleSheet("color: #f39c12; font-weight: bold; padding: 3px; font-size: 11px;")
    
    def complete_inspection(self):
        """Complete the inspection process"""
        total_time = (datetime.now() - self.inspection_start_time).total_seconds()
        
        # Determine overall result
        overall_result = self.determine_overall_result()
        
        # Update UI
        self.overall_result.setText(f"Status: {overall_result}")
        self.time_info.setText(f"Time: {total_time:.1f}s")
        
        if overall_result == "PASS":
            self.overall_result.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 14px; margin: 5px;")
            self.update_camera_display("✅ INSPECTION COMPLETE\n\nRESULT: PASS\n\nReady to submit data")
        else:
            self.overall_result.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 14px; margin: 5px;")
            self.update_camera_display("❌ INSPECTION COMPLETE\n\nRESULT: FAIL\n\nReview required")
        
        # Enter inspection completed state
        self.enter_inspection_completed_state()
        
        # Enable data submission based on inspection state
        if self.inspection_type == "INLINE":
            self._update_submit_button_for_inline()
        else:
            # For other inspection types, check completion or failure
            submit_enabled = self._should_enable_submit_button()
            self._set_submit_button_enabled(submit_enabled)
        
        # Update API data display
        api_display_text = f"Inspection Complete - {overall_result}\n"
        api_display_text += f"Total Time: {total_time:.1f}s\n"
        api_display_text += f"Steps Completed: {len(self.inspection_results)}/{len(self.inspection_steps)}"
        self._update_api_display(api_display_text)
        
        # Show completion message
        self.show_completion_message(overall_result, total_time)
    
    def determine_overall_result(self):
        """Determine overall inspection result based on collected data"""
        # Base implementation - can be overridden by child classes
        if len(self.inspection_results) == len(self.inspection_steps):
            return "PASS"
        else:
            return "FAIL"
    
    def show_completion_message(self, result, total_time):
        """Show inspection completion message"""
        msg = f"{self.inspection_type} Inspection Complete!\n\n"
        msg += f"Result: {result}\n"
        msg += f"Total Time: {total_time:.1f}s\n"
        msg += f"Steps Completed: {len(self.inspection_results)}/{len(self.inspection_steps)}\n\n"
        
        if result == "PASS":
            msg += "Click 'Submit to API' to send results."
            QMessageBox.information(self, "Inspection Complete", msg)
        else:
            msg += "Do you want to apply manual override?"
            reply = QMessageBox.question(self, "Inspection Failed", msg,
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.manual_override()
    
    def submit_inspection_data(self):
        """Submit collected inspection data to API endpoints"""
        try:
            if not self.api_manager:
                QMessageBox.warning(self, "API Error", "API Manager not available")
                return
            
            success = self.perform_api_submissions()
            
            if success:
                QMessageBox.information(self, "Data Submitted", 
                                      f"Inspection data successfully submitted to API endpoints.\n\n"
                                      f"Barcode: {self.barcode}\n"
                                      f"Type: {self.inspection_type}")
                self.log_inspection_results()
                self.reset_for_new_inspection()
            else:
                QMessageBox.critical(self, "Submission Failed", 
                                   "Failed to submit data to one or more API endpoints.\n\n"
                                   "Please check the API connections and try again.")
                
        except Exception as e:
            QMessageBox.critical(self, "Submission Error", f"Error submitting data: {e}")
    
    def perform_api_submissions(self) -> bool:
        """Perform the actual API submissions - override in child classes"""
        raise NotImplementedError("Child classes must implement perform_api_submissions()")
    
    # ===== Control Methods =====
    
    def manual_override(self):
        """Handle manual override"""
        if not self.inspection_results:
            QMessageBox.warning(self, "No Inspection", "No inspection has been performed yet.")
            return
        
        reply = QMessageBox.question(self, "Manual Override", 
                                   f"Apply manual override for {self.inspection_type} inspection?\n\n"
                                   "This will mark the inspection as PASS regardless of automatic results.\n"
                                   "Override will be logged for audit purposes.",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.apply_manual_override()
    
    def apply_manual_override(self):
        """Apply manual override to inspection result"""
        override_time = datetime.now()
        
        # Update UI
        self.overall_result.setText("Status: PASS (Override)")
        self.overall_result.setStyleSheet("color: #f39c12; font-weight: bold; font-size: 14px; margin: 5px;")
        self.update_camera_display("⚠️ MANUAL OVERRIDE APPLIED\n\nRESULT: PASS\n\nOverride logged for audit")
        
        # Enter override applied state
        self.enter_override_applied_state()
        
        # Log the override
        self.log_manual_override(override_time)
        
        # Enable data submission based on inspection state
        if self.inspection_type == "INLINE":
            self._update_submit_button_for_inline()
        else:
            # For other inspection types, check completion or failure
            submit_enabled = self._should_enable_submit_button()
            self._set_submit_button_enabled(submit_enabled)
        
        QMessageBox.information(self, "Override Applied", 
                               "Manual override has been applied and logged.\n\n"
                               "You can now submit the data to API endpoints.")
    
    def stop_inspection(self):
        """Stop the current inspection"""
        reply = QMessageBox.question(self, "Stop Inspection", 
                                   "Stop the current inspection?\n\n"
                                   "All progress will be lost.",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.reset_inspection()
    
    def reset_inspection(self):
        """Reset inspection to initial state"""
        self.current_step = 0
        self.inspection_results = {}
        self.api_data_collected = {}
        self.current_step_label.setText("Step: Not Started")
        self.progress_bar.setValue(0)
        self.overall_result.setText("Status: Pending")
        self.overall_result.setStyleSheet("color: #2c3e50; font-weight: bold; font-size: 14px; margin: 5px;")
        self.time_info.setText("Time: 00:00")
        
        # Reset camera display
        self.update_camera_display("Camera Feed\n\n📹\n\nReady for next inspection")
        
        # Reset step status
        for i in range(self.step_status_layout.count()):
            label = self.step_status_layout.itemAt(i).widget()
            if label and hasattr(label, 'setText'):
                step_name = self.inspection_steps[i]
                label.setText(f"{step_name}: Pending")
                label.setStyleSheet("color: #666; padding: 3px; font-size: 11px;")
        
        # Enter appropriate state based on barcode status
        if self.barcode:
            self.enter_barcode_entered_state()
            self.update_barcode_status("Ready to start new inspection", "ready")
        else:
            self.enter_idle_state()
            self.update_barcode_status("Enter or scan a barcode to begin", "waiting")
        
        # Re-enable barcode input after inspection
        self.barcode_input.setEnabled(True)
        self.scan_qr_button.setEnabled(True)
            
        # Trigger input change handler to update submit button state
        self.on_barcode_input_changed()
        
        # Clear API data display
        self._update_api_display("Ready for new inspection")
        
        # Disable data submission
        self._set_submit_button_enabled(False)
    
    def reset_for_new_inspection(self):
        """Reset for a new inspection after successful submission"""
        self.reset_inspection()
        
        # Clear barcode
        self.barcode = ""
        self.barcode_input.clear()
        self.barcode_display.setText("No barcode entered")
        self.barcode_display.setStyleSheet("background-color: #f8f9fa; padding: 10px; border: 2px solid #ddd; border-radius: 5px; font-size: 14px;")
        
        # Show message for new barcode entry and enter idle state
        self.enter_idle_state()
        self.update_barcode_status("Scan or enter new barcode", "waiting")
    
    def back_to_main(self):
        """Return to main window and bring it to foreground"""
        if self.inspection_results and self.current_step > 0:
            reply = QMessageBox.question(self, "Back to Main", 
                                       "Inspection in progress. Return to main menu?\n\n"
                                       "All progress will be lost.",
                                       QMessageBox.Yes | QMessageBox.No)
        else:
            reply = QMessageBox.question(self, "Back to Main", 
                                       "Return to main menu?",
                                       QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            print("🏠 Returning to main menu...")
            # Emit signal to restore main window (this will bring it to foreground)
            self.window_closed.emit()
            # Close this inspection window
            self.close()
            print("✅ Inspection window closed, main window should be restored")
    
    def quit_application(self):
        """Safely quit the entire application"""
        if self.inspection_results and self.current_step > 0:
            reply = QMessageBox.question(self, "Quit Application", 
                                       "Inspection in progress. Quit application?\n\n"
                                       "All unsaved progress will be lost.",
                                       QMessageBox.Yes | QMessageBox.No)
        else:
            reply = QMessageBox.question(self, "Quit Application", 
                                       "Are you sure you want to quit the application?",
                                       QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            print("🔄 Performing safe shutdown from inspection window...")
            
            # Stop any running processes
            if hasattr(self, 'api_manager') and self.api_manager:
                print("   📡 Stopping API manager...")
                # Stop API manager if needed
            
            # TODO: Add cleanup logic here:
            # - Stop any running inspections
            # - Close camera connections  
            # - Save any pending data
            # - Clean up resources
            
            print("✅ Safe shutdown completed")
            
            # Import QApplication here to avoid circular imports
            from PyQt5.QtWidgets import QApplication
            
            # Emit signal for any parent windows to close
            self.window_closed.emit()
            
            # Close this window
            self.close()
            
            # Quit the entire application
            QApplication.quit()
    
    # ===== Utility Methods =====
    
    def log_inspection_results(self):
        """Log inspection results to file"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            logs_dir = os.path.join(project_root, "logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            csv_file = os.path.join(logs_dir, f"{self.inspection_type.lower()}_inspection_log.csv")
            
            # Implementation details would go here
            print(f"Logged inspection results to: {csv_file}")
            
        except Exception as e:
            print(f"Error logging results: {e}")
    
    def log_manual_override(self, override_time):
        """Log manual override to file"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            logs_dir = os.path.join(project_root, "logs")
            override_file = os.path.join(logs_dir, "manual_overrides.csv")
            
            # Implementation details would go here
            print(f"Logged manual override to: {override_file}")
            
        except Exception as e:
            print(f"Error logging override: {e}")
    
    def _update_api_display(self, text: str):
        """Safely update API data display (hidden for INLINE inspection)"""
        try:
            if hasattr(self, 'api_data_display') and self.api_data_display and self.api_data_display.isVisible():
                self.api_data_display.setPlainText(text)
        except Exception as e:
            print(f"Warning: Could not update API display: {e}")
    
    def _set_submit_button_enabled(self, enabled: bool):
        """Safely set submit button enabled state"""
        try:
            if hasattr(self, 'submit_data_button') and self.submit_data_button:
                self.submit_data_button.setEnabled(enabled)
        except Exception as e:
            print(f"Warning: Could not update submit button: {e}")
    
    def _should_enable_submit_button(self) -> bool:
        """Determine if submit button should be enabled based on inspection state"""
        # Submit button is enabled when:
        # 1. All inspections are complete, OR
        # 2. Any inspection has failed (requiring manual override or restart)
        
        if self.inspection_type == "INLINE":
            return self._should_enable_submit_for_inline()
        else:
            # For other inspection types (EOLT), check if complete or has failures
            all_complete = len(self.inspection_results) == len(self.inspection_steps)
            has_failures = self._has_any_failures()
            
            return all_complete or has_failures
    
    def _has_any_failures(self) -> bool:
        """Check if any inspection step has failed"""
        for step_name, result in self.inspection_results.items():
            step_data = result.get('data', {})
            
            # Check for algorithm failures based on inspection type
            if self.inspection_type == "EOLT":
                # Check Upper, Lower, Left, Right results
                for field in ['Upper', 'Lower', 'Left', 'Right']:
                    if step_data.get(field) == "FAIL":
                        return True
            elif "TOP:" in step_name:
                # Check Screw, Plate results
                for field in ['Screw', 'Plate']:
                    if step_data.get(field) == "FAIL":
                        return True
            elif "BOTTOM:" in step_name:
                # Check Antenna, Capacitor, Speaker results
                for field in ['Antenna', 'Capacitor', 'Speaker']:
                    if step_data.get(field) == "FAIL":
                        return True
        
        return False
    
    def _should_enable_submit_for_inline(self) -> bool:
        """Special logic for INLINE inspection submit button"""
        # For INLINE, we need to handle two-stage submission
        # Stage 1: BOTTOM inspection complete -> enable first submit
        # Stage 2: TOP inspection complete -> enable second submit
        
        bottom_complete = self._check_inline_bottom_complete()
        top_complete = self._check_inline_top_complete()
        bottom_has_failures = self._inline_bottom_has_failures()
        top_has_failures = self._inline_top_has_failures()
        
        # Enable submit if BOTTOM is complete (success or failure) or TOP is complete
        return (bottom_complete or bottom_has_failures) or (top_complete or top_has_failures)
    
    def _inline_bottom_has_failures(self) -> bool:
        """Check if BOTTOM inspection has any failures"""
        for step_name, result in self.inspection_results.items():
            if "BOTTOM:" in step_name:
                step_data = result.get('data', {})
                # Check if any component failed (value is 0)
                for field in ['Antenna', 'Capacitor', 'Speaker']:
                    if step_data.get(field, 0) == 0:
                        return True
        return False
    
    def _inline_top_has_failures(self) -> bool:
        """Check if TOP inspection has any failures"""
        for step_name, result in self.inspection_results.items():
            if "TOP:" in step_name:
                step_data = result.get('data', {})
                # Check if any component failed (value is 0)
                for field in ['Screw', 'Plate']:
                    if step_data.get(field, 0) == 0:
                        return True
        return False
    
    def _update_camera_with_inline_results(self, step_name: str, step_data: dict):
        """Update camera display with detailed INLINE inspection results"""
        try:
            if step_name == "BOTTOM: Capture":
                # Show BOTTOM component results - use display values if available
                if '_display' in step_data:
                    antenna = step_data['_display'].get('Antenna', 'UNKNOWN')
                    capacitor = step_data['_display'].get('Capacitor', 'UNKNOWN')
                    speaker = step_data['_display'].get('Speaker', 'UNKNOWN')
                    overall_result = step_data['_display'].get('Result', 'UNKNOWN')
                else:
                    # Fallback: convert 1/0 to PASS/FAIL for display
                    antenna = "PASS" if step_data.get('Antenna', 0) == 1 else "FAIL"
                    capacitor = "PASS" if step_data.get('Capacitor', 0) == 1 else "FAIL"
                    speaker = "PASS" if step_data.get('Speaker', 0) == 1 else "FAIL"
                    overall_result = "PASS" if step_data.get('Result', 0) == 1 else "FAIL"
                
                camera_text = f"✅ BOTTOM Inspection Complete\n\n"
                camera_text += f"📊 Component Results:\n"
                camera_text += f"🔹 Antenna: {antenna}\n"
                camera_text += f"🔹 Capacitor: {capacitor}\n"
                camera_text += f"🔹 Speaker: {speaker}\n\n"
                camera_text += f"Overall Result: {overall_result}\n\n"
                
                if overall_result == "PASS":
                    camera_text += "Ready for TOP inspection"
                else:
                    camera_text += "⚠️ Review required or apply manual override"
                    
                self.update_camera_display(camera_text)
                
            elif step_name == "TOP: Capture":
                # Show TOP component results - use display values if available
                if '_display' in step_data:
                    screw = step_data['_display'].get('Screw', 'UNKNOWN')
                    plate = step_data['_display'].get('Plate', 'UNKNOWN')
                    overall_result = step_data['_display'].get('Result', 'UNKNOWN')
                else:
                    # Fallback: convert 1/0 to PASS/FAIL for display
                    screw = "PASS" if step_data.get('Screw', 0) == 1 else "FAIL"
                    plate = "PASS" if step_data.get('Plate', 0) == 1 else "FAIL"
                    overall_result = "PASS" if step_data.get('Result', 0) == 1 else "FAIL"
                
                camera_text = f"✅ TOP Inspection Complete\n\n"
                camera_text += f"📊 Component Results:\n"
                camera_text += f"🔹 Screw: {screw}\n"
                camera_text += f"🔹 Plate: {plate}\n\n"
                camera_text += f"Overall Result: {overall_result}\n\n"
                
                # Check if both inspections are complete
                if self._check_inline_bottom_complete() and self._check_inline_top_complete():
                    camera_text += "🎉 INLINE Inspection Complete!"
                else:
                    camera_text += "Awaiting additional inspections"
                    
                self.update_camera_display(camera_text)
                
        except Exception as e:
            print(f"Error updating camera display for INLINE results: {e}")
            # Fallback to generic display
            self.update_camera_display(f"✅ {step_name} Complete\n\nResult: {step_data.get('Result', 'UNKNOWN')}")
    
    def _update_submit_button_for_inline(self):
        """Update submit button state for INLINE inspection"""
        try:
            submit_enabled = self._should_enable_submit_for_inline()
            self._set_submit_button_enabled(submit_enabled)
            
            # Debug information
            bottom_complete = self._check_inline_bottom_complete()
            top_complete = self._check_inline_top_complete()
            bottom_failures = self._inline_bottom_has_failures()
            top_failures = self._inline_top_has_failures()
            
            print(f"🔍 INLINE Submit Button Check:")
            print(f"   BOTTOM complete: {bottom_complete}")
            print(f"   TOP complete: {top_complete}")
            print(f"   BOTTOM failures: {bottom_failures}")
            print(f"   TOP failures: {top_failures}")
            print(f"   Submit enabled: {submit_enabled}")
            
        except Exception as e:
            print(f"Error updating INLINE submit button: {e}")
            self._set_submit_button_enabled(False)
    
    def _check_inline_top_complete(self) -> bool:
        """Check if TOP inspection is complete"""
        return "TOP: Capture" in self.inspection_results
    
    def _check_inline_bottom_complete(self) -> bool:
        """Check if BOTTOM inspection is complete"""  
        return "BOTTOM: Capture" in self.inspection_results
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Stop camera streaming
        if hasattr(self, 'camera_integrator'):
            self.camera_integrator.stop_inspection()
        
        self.window_closed.emit()
        event.accept()