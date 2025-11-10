"""
EOLT Inspection Window - Inherits from BaseInspectionWindow
Handles single API endpoint submission for EOLT testing
"""

import sys
import os
from typing import List, Dict, Any
from PyQt5.QtWidgets import QApplication, QMessageBox
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
    
    def get_inspection_steps(self) -> List[str]:
        """Return EOLT inspection steps"""
        return ["Upper", "Lower", "Left", "Right", "Printtext", "Barcodetext"]
    
    def init_api_manager(self):
        """Initialize API manager for EOLT inspection"""
        try:
            print("🔧 Initializing EOLT API manager...")
            
            # Load configuration to get API endpoints
            from config import config_manager
            config = config_manager.load_config()
            
            # EOLT uses CHIP -> EOLT workflow
            workflow = None
            for wf in config.workflows:
                if wf.name == "CHIP_TO_EOLT":
                    workflow = wf
                    break
            
            if workflow:
                api1_url = f"{config.api.base_url}/{workflow.api1_table}"
                api2_url = f"{config.api.base_url}/{workflow.api2_table}"
                
                self.api_manager = APIManager(
                    api1_url=api1_url,
                    api2_url=api2_url,
                    placeholders=(workflow.api1_table.lower(), workflow.api2_table.lower())
                )
                print(f"✅ EOLT API Manager initialized:")
                print(f"   📡 API1: {api1_url} ({workflow.api1_table})")
                print(f"   📡 API2: {api2_url} ({workflow.api2_table})")
                print(f"   📝 Workflow: {workflow.description}")
            else:
                print("❌ CHIP_TO_EOLT workflow not found in config")
                self.api_manager = None
                
        except Exception as e:
            print(f"❌ Failed to initialize EOLT API Manager: {e}")
            import traceback
            traceback.print_exc()
            self.api_manager = None
    
    def get_api_endpoints(self) -> List[str]:
        """Return API endpoints for EOLT inspection"""
        return ["CHIPINSPECTION", "EOLTINSPECTION"]
    
    def collect_inspection_data(self, step: str) -> Dict[str, Any]:
        """Collect inspection data for EOLT step"""
        # Mock data collection - in real implementation, this would interface with
        # camera system and ML models
        
        import random
        
        if step in ["Upper", "Lower", "Left", "Right"]:
            # These are Pass/Fail results for each side
            result = "PASS" if random.random() > 0.15 else "FAIL"  # 85% pass rate
            confidence = random.uniform(0.7, 0.99)
            
            return {
                f"Manual{step}": 1 if result == "PASS" else 0,  # Manual result (1/0)
                f"{step}": result,  # Automatic result
                f"{step}_confidence": confidence,
                f"{step}_timestamp": datetime.now().isoformat()
            }
            
        elif step == "Printtext":
            # Text recognition result
            detected_text = f"SAMPLE_TEXT_{random.randint(1000, 9999)}"
            confidence = random.uniform(0.8, 0.95)
            
            return {
                "Printtext": detected_text,
                "printtext_confidence": confidence,
                "printtext_timestamp": datetime.now().isoformat()
            }
            
        elif step == "Barcodetext":
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
        
        if step in ["Upper", "Lower", "Left", "Right"]:
            # Check if we have both automatic and manual results
            return f"Manual{step}" in data and f"{step}" in data
            
        elif step == "Printtext":
            # Check if text was detected
            return "Printtext" in data and len(data["Printtext"]) > 0
            
        elif step == "Barcodetext":
            # Check if barcode was read
            return "Barcodetext" in data and "barcode_match" in data
        
        return True
    
    def determine_overall_result(self):
        """Determine EOLT inspection result based on collected data"""
        if len(self.inspection_results) != len(self.inspection_steps):
            return "FAIL"
        
        # Check manual results for the four sides
        for step in ["Upper", "Lower", "Left", "Right"]:
            if step in self.inspection_results:
                manual_result = self.inspection_results[step]['data'].get(f'Manual{step}', 0)
                if manual_result != 1:  # If any manual result is not 1 (PASS)
                    return "FAIL"
        
        # Check barcode match
        if "Barcodetext" in self.inspection_results:
            barcode_data = self.inspection_results["Barcodetext"]['data']
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
            
            print(f"📤 CHIP_TO_EOLT API submission")
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
        """Prepare data for EOLT API submission"""
        # Combine all collected inspection data into EOLT format
        api_data = {
            'Barcode': self.barcode,
            'DT': datetime.now().isoformat(),
            'Process_id': 'EOLT_PROC_001',
            'Station_ID': 'EOLT_STATION_01'
        }
        
        # Add inspection results for each side
        for step in ["Upper", "Lower", "Left", "Right"]:
            if step in self.inspection_results:
                step_data = self.inspection_results[step]['data']
                
                # Add automatic result (for display/logging)
                api_data[step] = step_data.get(step, 'UNKNOWN')
                
                # Add manual result (the actual result that matters - 1/0)
                manual_key = f'Manual{step}'
                api_data[manual_key] = step_data.get(manual_key, 0)
        
        # Add overall result based on manual results
        overall_result = self.determine_overall_result()
        api_data['Result'] = overall_result
        api_data['ManualResult'] = 1 if overall_result == "PASS" else 0
        
        # Add text detection results
        if "Printtext" in self.inspection_results:
            api_data['Printtext'] = self.inspection_results["Printtext"]['data'].get('Printtext', '')
        
        if "Barcodetext" in self.inspection_results:
            api_data['Barcodetext'] = self.inspection_results["Barcodetext"]['data'].get('Barcodetext', '')
        
        return api_data
    
    def show_completion_message(self, result, total_time):
        """Show EOLT-specific completion message"""
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
            msg += "\nClick 'Submit to API' to send results to EOLTINSPECTION endpoint."
            QMessageBox.information(self, "EOLT Inspection Complete", msg)
        else:
            msg += "\n❌ EOLT inspection failed!"
            msg += f"\nFailed: {', '.join(failed_steps)}"
            msg += "\n\nDo you want to apply manual override?"
            reply = QMessageBox.question(self, "EOLT Inspection Failed", msg,
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.manual_override()


def main():
    """Main function for testing EOLT inspection window"""
    app = QApplication(sys.argv)
    
    # Test the EOLT window
    window = EOLTInspectionWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()