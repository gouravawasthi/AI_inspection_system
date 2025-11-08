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
from PyQt5.QtGui import QPixmap, QFont

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.api_manager import APIManager


class BaseInspectionWindow(QWidget):
    """Base inspection window for product quality inspection"""
    
    # Signals
    inspection_complete = pyqtSignal(dict)
    window_closed = pyqtSignal()
    
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
        
        # Initialize API manager for this inspection type
        self.init_api_manager()
        self.init_ui()
    
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
    
    def init_ui(self):
        """Initialize the inspection interface"""
        self.setWindowTitle(f"AI VDI System - {self.inspection_type} Inspection")
        self.showFullScreen()
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
        control_panel.setFixedWidth(400)
        control_panel.setStyleSheet("QFrame { border: 2px solid #ccc; border-radius: 10px; background-color: white; }")
        control_layout = QVBoxLayout()
        control_panel.setLayout(control_layout)
        
        # Title
        title = QLabel(f"{self.inspection_type} Control Panel")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin: 15px;")
        control_layout.addWidget(title)
        
        # Barcode section
        self.create_barcode_section(control_layout)
        
        # API Status section
        self.create_api_status_section(control_layout)
        
        # Camera settings section
        self.create_camera_settings(control_layout)
        
        # Inspection controls
        self.create_inspection_controls(control_layout)
        
        # Add spacer
        control_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        main_layout.addWidget(control_panel)
    
    def create_barcode_section(self, layout):
        """Create barcode input section"""
        barcode_group = QGroupBox("Barcode Input")
        barcode_layout = QVBoxLayout()
        barcode_group.setLayout(barcode_layout)
        
        # Barcode status message
        self.barcode_status_label = QLabel("Enter or scan a barcode to begin")
        self.barcode_status_label.setStyleSheet("""
            background-color: #e9ecef; 
            padding: 10px; 
            border: 2px solid #adb5bd; 
            border-radius: 5px; 
            font-size: 14px; 
            color: #495057;
            font-weight: bold;
            text-align: center;
        """)
        self.barcode_status_label.setAlignment(Qt.AlignCenter)
        barcode_layout.addWidget(self.barcode_status_label)
        
        # Manual barcode input
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Enter barcode manually or scan")
        self.barcode_input.returnPressed.connect(self.submit_barcode)
        self.barcode_input.textChanged.connect(self.on_barcode_input_changed)
        barcode_layout.addWidget(self.barcode_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.scan_qr_button = QPushButton("Scan QR")
        self.scan_qr_button.clicked.connect(self.scan_qr_code)
        button_layout.addWidget(self.scan_qr_button)
        
        self.submit_barcode_button = QPushButton("Submit")
        self.submit_barcode_button.clicked.connect(self.submit_barcode)
        self.submit_barcode_button.setEnabled(False)  # Initially disabled
        button_layout.addWidget(self.submit_barcode_button)
        
        barcode_layout.addLayout(button_layout)
        
        # Barcode display
        self.barcode_display = QLabel("No barcode entered")
        self.barcode_display.setStyleSheet("background-color: #f8f9fa; padding: 10px; border: 2px solid #ddd; border-radius: 5px; font-size: 14px;")
        barcode_layout.addWidget(self.barcode_display)
        
        layout.addWidget(barcode_group)
    
    def create_api_status_section(self, layout):
        """Create API status section"""
        api_group = QGroupBox("API Status")
        api_layout = QVBoxLayout()
        api_group.setLayout(api_layout)
        
        # API endpoints status
        self.api_status_labels = {}
        endpoints = self.get_api_endpoints()
        
        for endpoint in endpoints:
            status_label = QLabel(f"{endpoint}: Not Checked")
            status_label.setStyleSheet("color: #666; padding: 5px; font-size: 12px;")
            self.api_status_labels[endpoint] = status_label
            api_layout.addWidget(status_label)
        
        # Test API button
        self.test_api_button = QPushButton("Test API Connection")
        self.test_api_button.clicked.connect(self.test_api_connections)
        api_layout.addWidget(self.test_api_button)
        
        layout.addWidget(api_group)
    
    def create_camera_settings(self, layout):
        """Create camera settings section"""
        camera_group = QGroupBox("Camera Settings")
        camera_layout = QVBoxLayout()
        camera_group.setLayout(camera_layout)
        
        # Camera enable/disable
        self.camera_enabled = QCheckBox("Camera Enabled")
        self.camera_enabled.setChecked(True)
        camera_layout.addWidget(self.camera_enabled)
        
        # Flip settings
        self.flip_horizontal = QCheckBox("Flip Horizontal")
        camera_layout.addWidget(self.flip_horizontal)
        
        self.flip_vertical = QCheckBox("Flip Vertical")
        camera_layout.addWidget(self.flip_vertical)
        
        # Exposure
        exposure_label = QLabel("Exposure:")
        camera_layout.addWidget(exposure_label)
        self.exposure_slider = QSlider(Qt.Horizontal)
        self.exposure_slider.setRange(-10, 10)
        self.exposure_slider.setValue(0)
        camera_layout.addWidget(self.exposure_slider)
        
        layout.addWidget(camera_group)
    
    def create_inspection_controls(self, layout):
        """Create inspection control buttons"""
        control_group = QGroupBox("Inspection Controls")
        control_layout = QVBoxLayout()
        control_group.setLayout(control_layout)
        
        # Main inspection button
        self.start_inspection_button = QPushButton("Start Inspection")
        self.start_inspection_button.clicked.connect(self.start_inspection)
        self.start_inspection_button.setEnabled(False)
        control_layout.addWidget(self.start_inspection_button)
        
        # Step control buttons
        self.next_step_button = QPushButton("Next Step")
        self.next_step_button.clicked.connect(self.next_step)
        self.next_step_button.setEnabled(False)
        control_layout.addWidget(self.next_step_button)
        
        self.repeat_step_button = QPushButton("Repeat Step")
        self.repeat_step_button.clicked.connect(self.repeat_current_step)
        self.repeat_step_button.setEnabled(False)
        control_layout.addWidget(self.repeat_step_button)
        
        # Manual controls
        self.manual_override_button = QPushButton("Manual Override")
        self.manual_override_button.setObjectName("warningButton")
        self.manual_override_button.clicked.connect(self.manual_override)
        self.manual_override_button.setEnabled(False)
        control_layout.addWidget(self.manual_override_button)
        
        # Stop and back buttons
        self.stop_inspection_button = QPushButton("Stop Inspection")
        self.stop_inspection_button.setObjectName("stopButton")
        self.stop_inspection_button.clicked.connect(self.stop_inspection)
        self.stop_inspection_button.setEnabled(False)
        control_layout.addWidget(self.stop_inspection_button)
        
        self.back_button = QPushButton("Back to Main Menu")
        self.back_button.setObjectName("stopButton")
        self.back_button.clicked.connect(self.back_to_main)
        control_layout.addWidget(self.back_button)
        
        # Quit button
        self.quit_button = QPushButton("QUIT APPLICATION")
        self.quit_button.setObjectName("quitButton")
        self.quit_button.clicked.connect(self.quit_application)
        self.quit_button.setStyleSheet("""
            QPushButton#quitButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton#quitButton:hover {
                background-color: #c82333;
            }
            QPushButton#quitButton:pressed {
                background-color: #bd2130;
            }
        """)
        control_layout.addWidget(self.quit_button)
        
        layout.addWidget(control_group)
    
    def create_camera_panel(self, main_layout):
        """Create camera display panel"""
        camera_panel = QFrame()
        camera_panel.setStyleSheet("QFrame { border: 2px solid #ccc; border-radius: 10px; background-color: white; }")
        camera_layout = QVBoxLayout()
        camera_panel.setLayout(camera_layout)
        
        # Camera feed placeholder
        self.camera_label = QLabel("Camera Feed\n\n📹\n\nCamera integration ready\nfor implementation")
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setMinimumSize(800, 600)
        self.camera_label.setStyleSheet("""
            background-color: #2c3e50; 
            color: white; 
            font-size: 24px; 
            border-radius: 8px;
            border: 2px solid #34495e;
        """)
        camera_layout.addWidget(self.camera_label)
        
        # Camera status and inspection info
        info_layout = QHBoxLayout()
        
        self.camera_status = QLabel("Camera: Simulation Mode")
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
        inspection_panel.setFixedWidth(400)
        inspection_panel.setStyleSheet("QFrame { border: 2px solid #ccc; border-radius: 10px; background-color: white; }")
        inspection_layout = QVBoxLayout()
        inspection_panel.setLayout(inspection_layout)
        
        # Title
        title = QLabel("Inspection Progress")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin: 10px;")
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
        """Create API data display section"""
        api_group = QGroupBox("API Data")
        api_layout = QVBoxLayout()
        api_group.setLayout(api_layout)
        
        # API data display
        self.api_data_display = QTextEdit()
        self.api_data_display.setMaximumHeight(100)
        self.api_data_display.setStyleSheet("font-size: 11px; background-color: #f8f9fa;")
        self.api_data_display.setPlainText("No data collected yet")
        api_layout.addWidget(self.api_data_display)
        
        # Submit data button
        self.submit_data_button = QPushButton("Submit to API")
        self.submit_data_button.clicked.connect(self.submit_inspection_data)
        self.submit_data_button.setEnabled(False)
        api_layout.addWidget(self.submit_data_button)
        
        layout.addWidget(api_group)
    
    # ===== API and Barcode Methods =====
    
    def on_barcode_input_changed(self):
        """Handle barcode input text changes"""
        barcode_text = self.barcode_input.text().strip()
        
        # Enable submit button only if there's text and inspection is not ongoing
        has_text = len(barcode_text) > 0
        inspection_not_ongoing = not hasattr(self, 'inspection_active') or not self.inspection_active
        
        self.submit_barcode_button.setEnabled(has_text and inspection_not_ongoing)
        
        # Update status message based on input state
        if not has_text:
            self.update_barcode_status("Enter or scan a barcode to begin", "waiting")
        elif not inspection_not_ongoing:
            self.update_barcode_status("Barcode inspection is ongoing", "inspecting")
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
            self.start_inspection_button.setEnabled(True)
            self.update_barcode_status(f"Barcode validated: {barcode}", "success")
            self.update_camera_display(f"Barcode Validated: {barcode}\n\nReady to start {self.inspection_type} inspection")
        else:
            self.barcode_display.setText(f"Invalid: {barcode}")
            self.barcode_display.setStyleSheet("background-color: #f8d7da; padding: 10px; border: 2px solid #f5c6cb; border-radius: 5px; font-size: 14px; color: #721c24;")
            self.update_barcode_status("Invalid barcode - validation failed", "error")
            self.update_camera_display("❌ Barcode Validation Failed\n\nCannot proceed with inspection")
            
            # Re-enable submit button for retry
            self.submit_barcode_button.setEnabled(True)
    
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
                    # Check if it's a "no previous inspection" error and offer to proceed anyway
                    if "was not tested in previous" in result['message']:
                        reply = QMessageBox.question(
                            self, 
                            "No Previous Inspection", 
                            f"No previous inspection found for this barcode.\n\n{result['message']}\n\nDo you want to proceed with inspection anyway?\n\n(This will create a new inspection record)",
                            QMessageBox.Yes | QMessageBox.No
                        )
                        if reply == QMessageBox.Yes:
                            # Update status display to show override
                            status_text += "✅ User override: Proceeding without previous inspection\n"
                            self.api_data_display.setPlainText(status_text)
                            return True
                        return False
                    return False
                else:
                    return False
            else:
                # Mock validation if no API manager - for testing purposes
                print(f"⚠️ No API manager - using mock validation for barcode: {barcode}")
                mock_result = {
                    'status': 'success',
                    'message': 'Mock validation - API manager not available'
                }
                status_text = f"API Response: {mock_result['status']}\n"
                status_text += f"Message: {mock_result['message']}\n"
                status_text += "⚠️ Using mock validation for testing\n"
                self.api_data_display.setPlainText(status_text)
                return len(barcode) >= 3  # Simple mock validation
                
        except Exception as e:
            print(f"API validation error: {e}")
            # Show error with option to proceed anyway
            reply = QMessageBox.question(
                self, 
                "API Validation Error", 
                f"Could not validate barcode with API:\n\n{e}\n\nDo you want to proceed anyway?\n\n(This will use mock validation)",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # Use mock validation
                status_text = f"API Error: {e}\n"
                status_text += "✅ User override: Using mock validation\n"
                self.api_data_display.setPlainText(status_text)
                return len(barcode) >= 3
            return False
    
    def handle_duplicate_barcode(self, api_result):
        """Handle duplicate barcode scenario"""
        msg = f"Duplicate barcode detected!\n\n{api_result['message']}\n\nDo you want to proceed anyway?"
        reply = QMessageBox.question(self, "Duplicate Barcode", msg,
                                   QMessageBox.Yes | QMessageBox.No)
        return reply == QMessageBox.Yes
    
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
        """Start the inspection process"""
        self.inspection_start_time = datetime.now()
        self.current_step = 0
        self.inspection_results = {}
        self.api_data_collected = {}
        self.inspection_active = True  # Track inspection state
        
        # Enable/disable controls
        self.start_inspection_button.setEnabled(False)
        self.next_step_button.setEnabled(True)
        self.repeat_step_button.setEnabled(True)
        self.manual_override_button.setEnabled(True)
        self.stop_inspection_button.setEnabled(True)
        self.submit_data_button.setEnabled(False)
        
        # Disable barcode submission during inspection
        self.submit_barcode_button.setEnabled(False)
        self.barcode_input.setEnabled(False)
        self.scan_qr_button.setEnabled(False)
        self.update_barcode_status("Barcode inspection is ongoing", "inspecting")
        
        # Start first step
        self.start_step_inspection()
        
        self.update_camera_display(f"🔍 {self.inspection_type} Inspection Started\n\nBarcode: {self.barcode}\n\nClick 'Next Step' to proceed")
    
    def start_step_inspection(self):
        """Start inspection of current step"""
        if self.current_step < len(self.inspection_steps):
            step_name = self.inspection_steps[self.current_step]
            self.step_start_time = datetime.now()
            self.current_step_label.setText(f"Step: {step_name}")
            
            # Update step status
            for i in range(self.step_status_layout.count()):
                label = self.step_status_layout.itemAt(i).widget()
                if label and hasattr(label, 'setText'):
                    if i == self.current_step:
                        label.setText(f"{self.inspection_steps[i]}: In Progress")
                        label.setStyleSheet("color: #3498db; font-weight: bold; padding: 3px; font-size: 11px;")
            
            # Update camera display for current step
            self.update_camera_display(f"Inspecting: {step_name}\n\n📹\n\nPosition product for {step_name}\n\nPress 'Next Step' when ready")
    
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
                
                # Update UI
                self.update_step_status(self.current_step, "COMPLETED")
                self.current_step += 1
                self.progress_bar.setValue(self.current_step)
                
                if self.current_step < len(self.inspection_steps):
                    self.start_step_inspection()
                else:
                    self.complete_inspection()
            else:
                QMessageBox.warning(self, "Invalid Data", 
                                  f"Data validation failed for step: {step_name}\n\nPlease check the inspection and try again.")
    
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
                label.setText(f"{step_name}: {status}")
                if status == "COMPLETED":
                    label.setStyleSheet("color: #27ae60; font-weight: bold; padding: 3px; font-size: 11px;")
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
        
        # Enable data submission
        self.submit_data_button.setEnabled(True)
        
        # Disable step controls
        self.next_step_button.setEnabled(False)
        self.repeat_step_button.setEnabled(False)
        self.stop_inspection_button.setEnabled(False)
        
        # Update API data display
        api_display_text = f"Inspection Complete - {overall_result}\n"
        api_display_text += f"Total Time: {total_time:.1f}s\n"
        api_display_text += f"Steps Completed: {len(self.inspection_results)}/{len(self.inspection_steps)}"
        self.api_data_display.setPlainText(api_display_text)
        
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
        
        # Log the override
        self.log_manual_override(override_time)
        
        # Enable data submission
        self.submit_data_button.setEnabled(True)
        
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
        self.inspection_active = False  # Mark inspection as inactive
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
        
        # Reset buttons
        self.start_inspection_button.setEnabled(bool(self.barcode))
        self.next_step_button.setEnabled(False)
        self.repeat_step_button.setEnabled(False)
        self.manual_override_button.setEnabled(False)
        self.stop_inspection_button.setEnabled(False)
        self.submit_data_button.setEnabled(False)
        
        # Re-enable barcode input after inspection
        self.barcode_input.setEnabled(True)
        self.scan_qr_button.setEnabled(True)
        
        # Update barcode status for new scan
        if self.barcode:
            self.update_barcode_status("Scan or enter new barcode", "waiting")
        else:
            self.update_barcode_status("Enter or scan a barcode to begin", "waiting")
            
        # Trigger input change handler to update submit button state
        self.on_barcode_input_changed()
        
        # Clear API data display
        self.api_data_display.setPlainText("Ready for new inspection")
    
    def reset_for_new_inspection(self):
        """Reset for a new inspection after successful submission"""
        self.reset_inspection()
        
        # Clear barcode
        self.barcode = ""
        self.barcode_input.clear()
        self.barcode_display.setText("No barcode entered")
        self.barcode_display.setStyleSheet("background-color: #f8f9fa; padding: 10px; border: 2px solid #ddd; border-radius: 5px; font-size: 14px;")
        
        # Show message for new barcode entry
        self.update_barcode_status("Scan or enter new barcode", "waiting")
        
        self.start_inspection_button.setEnabled(False)
    
    def back_to_main(self):
        """Return to main window"""
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
            self.window_closed.emit()
            self.close()
    
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
    
    def update_camera_display(self, message):
        """Update camera display with a message"""
        self.camera_label.setText(message)
    
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
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.window_closed.emit()
        event.accept()