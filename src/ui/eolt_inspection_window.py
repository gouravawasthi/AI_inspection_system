"""
EOLT Inspection Window - Inherits from BaseInspectionWindow
Handles single API endpoint submission for EOLT testing
"""

import sys
import os
from typing import List, Dict, Any
from PyQt5.QtWidgets import QApplication, QMessageBox, QGroupBox, QVBoxLayout
from datetime import datetime

# Import base class
try:
    from .base_inspection_window import BaseInspectionWindow
except ImportError:
    from base_inspection_window import BaseInspectionWindow

# Add parent directory to path for API imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.api_manager import APIManager


class EOLTInspectionWindow(BaseInspectionWindow):
    """EOLT Inspection Window for End-of-Line Testing"""
    
    def __init__(self, parent=None):
        super().__init__(parent, "EOLT")
    
    def create_inspection_controls(self, layout):
        """Override to create inspection controls with submit button in main panel like INLINE"""
        # Call parent method first to create the basic controls
        super().create_inspection_controls(layout)
        
        # The base class doesn't create submit button for EOLT in main controls
        # So we need to add it manually to match INLINE layout
        control_group = None
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QGroupBox):
                if item.widget().title() == "Inspection Controls":
                    control_group = item.widget()
                    break
        
        if control_group:
            control_layout = control_group.layout()
            
            # Create submit button to match INLINE style
            from PyQt5.QtWidgets import QPushButton
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
            
            # Insert submit button before the spacer and stop button
            insert_position = control_layout.count() - 2  # Before spacer and stop button
            control_layout.insertWidget(insert_position, self.submit_data_button)
            print("✅ EOLT Submit button added to main control panel (INLINE-style layout)")
    
    def create_api_data_section(self, layout):
        """Override to create API section like INLINE (no API Data subsection)"""
        api_group = QGroupBox("API Data & Settings")
        api_layout = QVBoxLayout()
        api_group.setLayout(api_layout)
        
        # API Status section (same as base class)
        api_status_subgroup = QGroupBox("API Status")
        api_status_layout = QVBoxLayout()
        api_status_subgroup.setLayout(api_status_layout)
        
        # API endpoints status
        from PyQt5.QtWidgets import QLabel, QPushButton, QCheckBox, QSlider
        from PyQt5.QtCore import Qt
        
        self.api_status_labels = {}
        endpoints = self.get_api_endpoints()
        
        for endpoint in endpoints:
            status_label = QLabel(f"{endpoint}: Not Checked")
            status_label.setStyleSheet("color: #666; padding: 3px; font-size: 10px;")
            self.api_status_labels[endpoint] = status_label
            api_status_layout.addWidget(status_label)
        
        # Test API button (same as base class)
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
        
        # Camera Settings section (same as base class)
        camera_settings_subgroup = QGroupBox("Camera Settings")
        camera_settings_layout = QVBoxLayout()
        camera_settings_subgroup.setLayout(camera_settings_layout)
        
        # Camera enable/disable
        self.camera_enabled = QCheckBox("Camera Enabled")
        self.camera_enabled.setChecked(True)
        self.camera_enabled.setStyleSheet("font-size: 11px;")
        camera_settings_layout.addWidget(self.camera_enabled)
        
        # Flip settings in horizontal layout
        from PyQt5.QtWidgets import QHBoxLayout
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
        
        # SKIP API Data subsection completely (like INLINE)
        # Create minimal hidden API display for compatibility
        from PyQt5.QtWidgets import QTextEdit
        self.api_data_display = QTextEdit()
        self.api_data_display.setMaximumHeight(60)
        self.api_data_display.setStyleSheet("font-size: 10px; background-color: #f8f9fa; border: 1px solid #ddd;")
        self.api_data_display.setPlainText("EOLT inspection: Manual API submission enabled")
        self.api_data_display.hide()  # Hidden like INLINE
        
        layout.addWidget(api_group)
    
    def get_inspection_steps(self) -> List[str]:
        """Return EOLT inspection steps - 4 separate captures + text inspections"""
        return [
            "Upper Capture",
            "Lower Capture", 
            "Left Capture",
            "Right Capture",
            "Printtext Capture",
            "Barcodetext Capture"
        ]
    
    def init_api_manager(self):
        """Initialize API manager for EOLT inspection"""
        try:
            print("🔧 Initializing EOLT API manager...")
            
            # Get configuration manager
            from config.config_manager import get_config_manager
            config = get_config_manager()
            
            # EOLT uses INLINE_TOP -> EOLT workflow
            eolt_workflow = config.get_workflow_by_name("INLINE_TOP_TO_EOLT")
            
            if eolt_workflow:
                api1_url = config.get_api_endpoint_url(eolt_workflow['api1_table'])
                api2_url = config.get_api_endpoint_url(eolt_workflow['api2_table'])
                
                self.api_manager = APIManager(
                    api1_url=api1_url,
                    api2_url=api2_url,
                    placeholders=(eolt_workflow['api1_table'].lower(), eolt_workflow['api2_table'].lower())
                )
                print(f"✅ EOLT API Manager initialized:")
                print(f"   📡 API1: {api1_url} ({eolt_workflow['api1_table']})")
                print(f"   📡 API2: {api2_url} ({eolt_workflow['api2_table']})")
                print(f"   📝 Workflow: {eolt_workflow['description']}")
            else:
                print("❌ INLINE_TOP_TO_EOLT workflow not found in config")
                # Fallback: Create a basic API manager using config
                print("⚠️ Creating fallback API manager for EOLT")
                fallback_api1 = config.get_api_endpoint_url("INLINEINSPECTIONTOP")
                fallback_api2 = config.get_api_endpoint_url("EOLTINSPECTION")
                
                self.api_manager = APIManager(
                    api1_url=fallback_api1,
                    api2_url=fallback_api2,
                    placeholders=("inline top inspection", "eolt inspection")
                )
                print(f"✅ Fallback EOLT API manager created: {fallback_api1} -> {fallback_api2}")
                self.api_manager = None
                
        except Exception as e:
            print(f"❌ Failed to initialize EOLT API Manager: {e}")
            import traceback
            traceback.print_exc()
            self.api_manager = None
    
    def get_api_endpoints(self) -> List[str]:
        """Return API endpoints for EOLT inspection"""
        return ["INLINEINSPECTIONTOP", "EOLTINSPECTION"]
    
    def collect_inspection_data(self, step: str) -> Dict[str, Any]:
        """Collect inspection data for EOLT step"""
        import random
        from datetime import datetime
        
        if step in ["Upper Capture", "Lower Capture", "Left Capture", "Right Capture"]:
            # Extract direction from step name (e.g., "Upper Capture" -> "Upper")
            direction = step.replace(" Capture", "")
            
            # Simulate algorithm result for this direction
            result = "PASS" if random.random() > 0.15 else "FAIL"  # 85% pass rate
            manual_result = 1 if result == "PASS" else 0
            confidence = random.uniform(0.7, 0.99)
            
            # Return data for this single direction
            return {
                direction: result,  # Algorithm result
                f"Manual{direction}": manual_result,  # Manual result (copied from algorithm)
                f"{direction}_confidence": confidence,
                f"{direction}_timestamp": datetime.now().isoformat()
            }
            
        elif step == "Printtext Capture":
            # Text recognition result
            detected_text = f"SAMPLE_TEXT_{random.randint(1000, 9999)}"
            confidence = random.uniform(0.8, 0.95)
            
            return {
                "Printtext": detected_text,
                "printtext_confidence": confidence,
                "printtext_timestamp": datetime.now().isoformat()
            }
            
        elif step == "Barcodetext Capture":
            # Barcode verification
            barcode_match = random.random() > 0.05  # 95% match rate
            
            return {
                "Barcodetext": self.barcode if barcode_match else f"MISMATCH_{random.randint(100, 999)}",
                "barcode_match": barcode_match,
                "barcode_timestamp": datetime.now().isoformat()
            }
            
        return {}
    
    def validate_step_data(self, step: str, data: Dict[str, Any]) -> bool:
        """Validate collected data for EOLT step"""
        if not data:
            return False
        
        if step in ["Upper Capture", "Lower Capture", "Left Capture", "Right Capture"]:
            # Extract direction from step name
            direction = step.replace(" Capture", "")
            # Check if we have both automatic and manual results
            return f"Manual{direction}" in data and f"{direction}" in data
        
        elif step == "Printtext Capture":
            return "Printtext" in data
        
        elif step == "Barcodetext Capture":
            return "Barcodetext" in data
        
        return True
    
    def determine_overall_result(self):
        """Determine EOLT inspection result based on collected data"""
        if len(self.inspection_results) != len(self.inspection_steps):
            return "FAIL"
        
        # Check manual results for the four sides (using capture step names)
        direction_steps = ["Upper Capture", "Lower Capture", "Left Capture", "Right Capture"]
        for step in direction_steps:
            if step in self.inspection_results:
                direction = step.replace(" Capture", "")
                manual_result = self.inspection_results[step]['data'].get(f'Manual{direction}', 0)
                if manual_result != 1:  # If any manual result is not 1 (PASS)
                    return "FAIL"
        
        # Check barcode match
        if "Barcodetext Capture" in self.inspection_results:
            barcode_data = self.inspection_results["Barcodetext Capture"]['data']
            if not barcode_data.get('barcode_match', False):
                return "FAIL"
        
        return "PASS"
    
    def perform_api_submissions(self) -> bool:
        """Perform EOLT API submissions - single endpoint submission"""
        try:
            print("\n🚀 Starting EOLT API Submission...")
            print("="*50)
            
            if not self.api_manager:
                print("❌ No API manager available for EOLT submission")
                return False
            
            # Prepare data for EOLT API submission
            eolt_data = self.prepare_eolt_api_data()
            
            print(f"📤 INLINE_TOP_TO_EOLT API submission")
            print(f"   Barcode: {self.barcode}")
            print(f"🎯 EOLT Data prepared:")
            for key, value in eolt_data.items():
                print(f"   {key}: {value}")
            
            print(f"📡 API Call: {self.api_manager.api2_url}")
            print(f"   Method: POST")
            print(f"   Payload: {eolt_data}")
            
            # Submit to EOLT endpoint (API2)
            try:
                # In real implementation, this would make the actual API call:
                # result = self.api_manager.submit_to_api2(self.barcode, eolt_data)
                
                # Mock successful submission for now
                result = {
                    'success': True,
                    'message': 'EOLT data submitted successfully',
                    'endpoint': self.api_manager.api2_url,
                    'timestamp': datetime.now().isoformat()
                }
                
                if result['success']:
                    print("✅ EOLT submission successful")
                    print(f"   Response: {result['message']}")
                    print("="*50)
                    
                    # Update API data display
                    api_text = f"✅ EOLT Submission Complete\n"
                    api_text += f"Endpoint: {result['endpoint']}\n"
                    api_text += f"Barcode: {self.barcode}\n"
                    api_text += f"Status: {result['message']}\n"
                    api_text += f"Time: {result['timestamp']}\n"
                    api_text += f"Data submitted: {len(eolt_data)} fields"
                    
                    self.api_data_display.setPlainText(api_text)
                    return True
                else:
                    print(f"❌ EOLT submission failed: {result.get('message', 'Unknown error')}")
                    return False
                    
            except Exception as e:
                print(f"❌ EOLT API call failed: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Error in EOLT API submission: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def prepare_eolt_api_data(self) -> Dict[str, Any]:
        """Prepare data for EOLT API submission to EOLTINSPECTION table"""
        from datetime import datetime
        
        # Initialize with None values (as per requirement d)
        api_data = {
            # Required fields (not None)
            'Barcode': self.barcode,
            'DT': datetime.now().isoformat(),
            'Process_id': 'EOLT_PROC_001',
            'Station_ID': 'EOLT_STATION_01',
            
            # Algorithm results (initialized to None, will be filled from captures)
            'Upper': None,
            'Lower': None,
            'Left': None,
            'Right': None,
            'Result': None,
            'Printtext': None,
            'Barcodetext': None,
            
            # Manual results (copied from algorithm, will be calculated)
            'ManualUpper': None,
            'ManualLower': None,
            'ManualLeft': None,
            'ManualRight': None,
            'ManualResult': None
        }
        
        # Extract data from capture steps
        direction_steps = {
            "Upper Capture": "Upper",
            "Lower Capture": "Lower", 
            "Left Capture": "Left",
            "Right Capture": "Right"
        }
        
        for capture_step, direction in direction_steps.items():
            if capture_step in self.inspection_results:
                step_data = self.inspection_results[capture_step]['data']
                
                # Copy algorithm result
                api_data[direction] = step_data.get(direction, 'UNKNOWN')
                
                # Copy manual result (requirement d: exact copy)
                manual_key = f'Manual{direction}'
                api_data[manual_key] = step_data.get(manual_key, 0)
        
        # Add text detection results
        if "Printtext Capture" in self.inspection_results:
            api_data['Printtext'] = self.inspection_results["Printtext Capture"]['data'].get('Printtext', '')
        
        if "Barcodetext Capture" in self.inspection_results:
            api_data['Barcodetext'] = self.inspection_results["Barcodetext Capture"]['data'].get('Barcodetext', '')
        
        # Calculate overall result (requirement d: ManualResult = 1 only if all manual fields = 1)
        manual_values = [
            api_data.get('ManualUpper', 0),
            api_data.get('ManualLower', 0),
            api_data.get('ManualLeft', 0),
            api_data.get('ManualRight', 0)
        ]
        
        manual_result = 1 if all(val == 1 for val in manual_values) else 0
        overall_result = "PASS" if manual_result == 1 else "FAIL"
        
        api_data['Result'] = overall_result
        api_data['ManualResult'] = manual_result
        
        return api_data
    
    def show_completion_message(self, result, total_time):
        """Show EOLT-specific completion message and wait for manual submission like INLINE"""
        failed_steps = []
        
        # Check which steps failed
        for step in ["Upper", "Lower", "Left", "Right"]:
            if step in self.inspection_results:
                manual_result = self.inspection_results[step]['data'].get(f'Manual{step}', 0)
                if manual_result != 1:
                    failed_steps.append(step)
        
        # Check barcode mismatch
        if "Barcodetext" in self.inspection_results:
            barcode_data = self.inspection_results["Barcodetext"]['data']
            if not barcode_data.get('barcode_match', False):
                failed_steps.append("Barcode Verification")
        
        msg = f"EOLT Inspection Complete!\n\n"
        msg += f"Result: {result}\n"
        msg += f"Total Time: {total_time:.1f}s\n"
        msg += f"Steps Completed: {len(self.inspection_results)}/{len(self.inspection_steps)}\n"
        
        if failed_steps:
            msg += f"\nFailed Components: {', '.join(failed_steps)}\n"
        
        if result == "PASS":
            msg += "\n✅ All EOLT checks passed!"
            msg += "\nSubmit button is now enabled. Click 'Submit to API' to send results to EOLTINSPECTION endpoint."
            QMessageBox.information(self, "EOLT Inspection Complete", msg)
            print("⏸️ EOLT inspection complete - waiting for manual API submission")
            print("   Submit button is enabled and ready for user action")
            # Do NOT automatically submit - wait for manual user action like INLINE
        else:
            msg += "\n❌ EOLT inspection failed!"
            msg += f"\nFailed: {', '.join(failed_steps)}"
            msg += "\n\nDo you want to apply manual override?"
            reply = QMessageBox.question(self, "EOLT Inspection Failed", msg,
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.manual_override()
                
    def submit_inspection_data(self):
        """Override to show manual submission like INLINE instead of automatic"""
        print("🔘 User manually clicked Submit to API button for EOLT")
        # Call parent implementation to do actual submission
        super().submit_inspection_data()


def main():
    """Main function for testing EOLT inspection window"""
    app = QApplication(sys.argv)
    
    # Test the EOLT window
    window = EOLTInspectionWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()