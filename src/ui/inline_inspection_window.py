"""
INLINE Inspection Window - Inherits from BaseInspectionWindow
Handles two sequential API endpoint submissions for INLINE testing
First: INLINE_TOP, then: INLINE_BOTTOM
"""

import sys
import os
from typing import List, Dict, Any
from PyQt5.QtWidgets import QApplication, QMessageBox
from datetime import datetime

# Import base class
from .base_inspection_window import BaseInspectionWindow

# Add parent directory to path for API imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.api_manager import APIManager


class INLINEInspectionWindow(BaseInspectionWindow):
    """INLINE Inspection Window for both TOP and BOTTOM inspections"""
    
    def __init__(self, parent=None):
        super().__init__(parent, "INLINE")
        self.top_inspection_complete = False
        self.bottom_inspection_complete = False
        self.top_api_manager = None
        self.bottom_api_manager = None
    
    def get_inspection_steps(self) -> List[str]:
        """Return INLINE inspection steps"""
        return [
            # TOP inspection steps
            "TOP: Setup", "TOP: Screw", "TOP: Plate", 
            # BOTTOM inspection steps  
            "BOTTOM: Setup", "BOTTOM: Antenna", "BOTTOM: Capacitor", "BOTTOM: Speaker"
        ]
    
    def init_api_manager(self):
        """Initialize API managers for both INLINE BOTTOM and TOP"""
        try:
            print("🔧 Initializing INLINE API managers...")
            
            # Load configuration to get API endpoints
            from config import config_manager
            config = config_manager.load_config()
            
            # Initialize BOTTOM inspection API manager (CHIP -> INLINE_BOTTOM)
            bottom_workflow = None
            for wf in config.workflows:
                if wf.name == "CHIP_TO_INLINE_BOTTOM":
                    bottom_workflow = wf
                    break
            
            if bottom_workflow:
                api1_url = f"{config.api.base_url}/{bottom_workflow.api1_table}"
                api2_url = f"{config.api.base_url}/{bottom_workflow.api2_table}"
                
                self.bottom_api_manager = APIManager(
                    api1_url=api1_url,
                    api2_url=api2_url,
                    placeholders=(bottom_workflow.api1_table.lower(), bottom_workflow.api2_table.lower())
                )
                print(f"✅ INLINE BOTTOM API Manager initialized:")
                print(f"   📡 API1: {api1_url} ({bottom_workflow.api1_table})")
                print(f"   📡 API2: {api2_url} ({bottom_workflow.api2_table})")
            else:
                print("❌ CHIP_TO_INLINE_BOTTOM workflow not found")
            
            # Initialize TOP inspection API manager (INLINE_BOTTOM -> INLINE_TOP)
            top_workflow = None
            for wf in config.workflows:
                if wf.name == "INLINE_BOTTOM_TO_INLINE_TOP":
                    top_workflow = wf
                    break
            
            if top_workflow:
                api1_url = f"{config.api.base_url}/{top_workflow.api1_table}"
                api2_url = f"{config.api.base_url}/{top_workflow.api2_table}"
                
                self.top_api_manager = APIManager(
                    api1_url=api1_url,
                    api2_url=api2_url,
                    placeholders=(top_workflow.api1_table.lower(), top_workflow.api2_table.lower())
                )
                print(f"✅ INLINE TOP API Manager initialized:")
                print(f"   📡 API1: {api1_url} ({top_workflow.api1_table})")
                print(f"   📡 API2: {api2_url} ({top_workflow.api2_table})")
            else:
                print("❌ INLINE_BOTTOM_TO_INLINE_TOP workflow not found")
            
            # Set the primary API manager for barcode validation (use bottom for initial validation)
            self.api_manager = self.bottom_api_manager
            print(f"🔧 Primary API manager set to BOTTOM for barcode validation")
            
        except Exception as e:
            print(f"❌ Error initializing INLINE API managers: {e}")
            import traceback
            traceback.print_exc()
            self.api_manager = None
    
    def get_api_endpoints(self) -> List[str]:
        """Return API endpoints for INLINE inspection"""
        return ["INLINEINSPECTIONBOTTOM", "INLINEINSPECTIONTOP"]
    
    def collect_inspection_data(self, step: str) -> Dict[str, Any]:
        """Collect inspection data for INLINE step"""
        import random
        
        if "TOP:" in step:
            step_name = step.replace("TOP: ", "")
            return self.collect_top_inspection_data(step_name)
        elif "BOTTOM:" in step:
            step_name = step.replace("BOTTOM: ", "")
            return self.collect_bottom_inspection_data(step_name)
        
        return {}
    
    def collect_top_inspection_data(self, step: str) -> Dict[str, Any]:
        """Collect data for TOP inspection steps"""
        import random
        
        if step == "Setup":
            return {
                "setup_complete": True,
                "setup_timestamp": datetime.now().isoformat(),
                "camera_position": "TOP"
            }
        elif step == "Screw":
            result = "PASS" if random.random() > 0.1 else "FAIL"  # 90% pass rate
            confidence = random.uniform(0.75, 0.95)
            return {
                "Screw": result,
                "ManualScrew": 1 if result == "PASS" else 0,
                "screw_confidence": confidence,
                "screw_count": random.randint(2, 4),
                "screw_timestamp": datetime.now().isoformat()
            }
        elif step == "Plate":
            result = "PASS" if random.random() > 0.05 else "FAIL"  # 95% pass rate
            confidence = random.uniform(0.80, 0.98)
            return {
                "Plate": result,
                "ManualPlate": 1 if result == "PASS" else 0,
                "plate_confidence": confidence,
                "plate_alignment": random.uniform(0.85, 1.0),
                "plate_timestamp": datetime.now().isoformat()
            }
        
        return {}
    
    def collect_bottom_inspection_data(self, step: str) -> Dict[str, Any]:
        """Collect data for BOTTOM inspection steps"""
        import random
        
        if step == "Setup":
            return {
                "setup_complete": True,
                "setup_timestamp": datetime.now().isoformat(),
                "camera_position": "BOTTOM"
            }
        elif step == "Antenna":
            result = "PASS" if random.random() > 0.08 else "FAIL"  # 92% pass rate
            confidence = random.uniform(0.70, 0.92)
            return {
                "Antenna": result,
                "ManualAntenna": 1 if result == "PASS" else 0,
                "antenna_confidence": confidence,
                "antenna_connection": random.choice(["GOOD", "WEAK", "NONE"]),
                "antenna_timestamp": datetime.now().isoformat()
            }
        elif step == "Capacitor":
            result = "PASS" if random.random() > 0.12 else "FAIL"  # 88% pass rate
            confidence = random.uniform(0.78, 0.94)
            return {
                "Capacitor": result,
                "ManualCapacitor": 1 if result == "PASS" else 0,
                "capacitor_confidence": confidence,
                "capacitor_value": random.uniform(0.95, 1.05),  # Should be close to 1.0
                "capacitor_timestamp": datetime.now().isoformat()
            }
        elif step == "Speaker":
            result = "PASS" if random.random() > 0.06 else "FAIL"  # 94% pass rate
            confidence = random.uniform(0.82, 0.97)
            return {
                "Speaker": result,
                "ManualSpeaker": 1 if result == "PASS" else 0,
                "speaker_confidence": confidence,
                "speaker_impedance": random.uniform(7.8, 8.2),  # Should be around 8 ohms
                "speaker_timestamp": datetime.now().isoformat()
            }
        
        return {}
    
    def validate_step_data(self, step: str, data: Dict[str, Any]) -> bool:
        """Validate collected data for INLINE step"""
        if not data:
            return False
        
        if "Setup" in step:
            return data.get("setup_complete", False)
        
        if "TOP:" in step:
            step_name = step.replace("TOP: ", "")
            if step_name in ["Screw", "Plate"]:
                return f"Manual{step_name}" in data and step_name in data
        
        if "BOTTOM:" in step:
            step_name = step.replace("BOTTOM: ", "")
            if step_name in ["Antenna", "Capacitor", "Speaker"]:
                return f"Manual{step_name}" in data and step_name in data
        
        return True
    
    def determine_overall_result(self):
        """Determine INLINE inspection result for both TOP and BOTTOM"""
        if len(self.inspection_results) != len(self.inspection_steps):
            return "FAIL"
        
        # Check TOP inspection results
        top_passed = self.check_top_results()
        
        # Check BOTTOM inspection results
        bottom_passed = self.check_bottom_results()
        
        # Both must pass for overall PASS
        if top_passed and bottom_passed:
            return "PASS"
        else:
            return "FAIL"
    
    def check_top_results(self) -> bool:
        """Check if TOP inspection passed"""
        for step in ["Screw", "Plate"]:
            step_key = f"TOP: {step}"
            if step_key in self.inspection_results:
                manual_result = self.inspection_results[step_key]['data'].get(f'Manual{step}', 0)
                if manual_result != 1:
                    return False
        return True
    
    def check_bottom_results(self) -> bool:
        """Check if BOTTOM inspection passed"""
        for step in ["Antenna", "Capacitor", "Speaker"]:
            step_key = f"BOTTOM: {step}"
            if step_key in self.inspection_results:
                manual_result = self.inspection_results[step_key]['data'].get(f'Manual{step}', 0)
                if manual_result != 1:
                    return False
        return True
    
    def complete_inspection(self):
        """Override to handle two-phase completion"""
        super().complete_inspection()
        
        # Determine which inspections are complete
        self.top_inspection_complete = self.check_top_inspection_complete()
        self.bottom_inspection_complete = self.check_bottom_inspection_complete()
        
        # Update API data display with both phases
        api_text = f"INLINE Inspection Status:\n"
        api_text += f"TOP: {'✅ Complete' if self.top_inspection_complete else '❌ Incomplete'}\n"
        api_text += f"BOTTOM: {'✅ Complete' if self.bottom_inspection_complete else '❌ Incomplete'}\n"
        api_text += f"Overall: {self.determine_overall_result()}\n"
        
        if self.top_inspection_complete and self.bottom_inspection_complete:
            api_text += "\nReady for sequential API submission"
        
        self.api_data_display.setPlainText(api_text)
    
    def check_top_inspection_complete(self) -> bool:
        """Check if TOP inspection is complete"""
        top_steps = ["TOP: Setup", "TOP: Screw", "TOP: Plate"]
        return all(step in self.inspection_results for step in top_steps)
    
    def check_bottom_inspection_complete(self) -> bool:
        """Check if BOTTOM inspection is complete"""
        bottom_steps = ["BOTTOM: Setup", "BOTTOM: Antenna", "BOTTOM: Capacitor", "BOTTOM: Speaker"]
        return all(step in self.inspection_results for step in bottom_steps)
    
    def perform_api_submissions(self) -> bool:
        """Perform INLINE API submissions - two sequential submissions"""
        try:
            print("\n🚀 Starting INLINE API Submissions...")
            print("="*50)
            
            success_count = 0
            total_submissions = 2
            
            # Step 1: Submit BOTTOM inspection data (CHIP -> INLINE_BOTTOM)
            print(f"📤 Step 1/2: CHIP_TO_INLINE_BOTTOM submission")
            print(f"   Barcode: {self.barcode}")
            
            if self.bottom_inspection_complete and self.bottom_api_manager:
                bottom_data = self.prepare_bottom_api_data()
                print(f"🎯 BOTTOM Data prepared:")
                for key, value in bottom_data.items():
                    print(f"   {key}: {value}")
                
                print(f"📡 API Call: {self.bottom_api_manager.api2_url}")
                print(f"   Method: POST")
                print(f"   Payload: {bottom_data}")
                
                # Simulate API call with debugging
                try:
                    # In real implementation, this would be:
                    # bottom_result = self.bottom_api_manager.submit_data(bottom_data)
                    
                    # Mock successful BOTTOM submission for now
                    bottom_result = {
                        'success': True,
                        'message': 'INLINE BOTTOM data submitted successfully',
                        'endpoint': self.bottom_api_manager.api2_url,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    if bottom_result['success']:
                        success_count += 1
                        print("✅ BOTTOM submission successful")
                        print(f"   Response: {bottom_result['message']}")
                    else:
                        print(f"❌ BOTTOM submission failed: {bottom_result.get('message', 'Unknown error')}")
                        return False
                        
                except Exception as e:
                    print(f"❌ BOTTOM API call failed: {e}")
                    return False
            else:
                print("⚠️ BOTTOM inspection not complete or API manager not available")
                return False
            
            print("\n" + "-"*50)
            
            # Step 2: Submit TOP inspection data (INLINE_BOTTOM -> INLINE_TOP)
            print(f"📤 Step 2/2: INLINE_BOTTOM_TO_INLINE_TOP submission")
            
            if self.top_inspection_complete and self.top_api_manager:
                top_data = self.prepare_top_api_data()
                print(f"🎯 TOP Data prepared:")
                for key, value in top_data.items():
                    print(f"   {key}: {value}")
                
                print(f"📡 API Call: {self.top_api_manager.api2_url}")
                print(f"   Method: POST")
                print(f"   Payload: {top_data}")
                
                # Simulate API call with debugging
                try:
                    # In real implementation, this would be:
                    # top_result = self.top_api_manager.submit_data(top_data)
                    
                    # Mock successful TOP submission for now
                    top_result = {
                        'success': True,
                        'message': 'INLINE TOP data submitted successfully',
                        'endpoint': self.top_api_manager.api2_url,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    if top_result['success']:
                        success_count += 1
                        print("✅ TOP submission successful")
                        print(f"   Response: {top_result['message']}")
                    else:
                        print(f"❌ TOP submission failed: {top_result.get('message', 'Unknown error')}")
                        return False
                        
                except Exception as e:
                    print(f"❌ TOP API call failed: {e}")
                    return False
            else:
                print("⚠️ TOP inspection not complete or API manager not available")
                return False
            
            print("\n" + "="*50)
            print(f"🎉 INLINE API Submissions Complete: {success_count}/{total_submissions}")
            
            # Update API data display with submission results
            if success_count == total_submissions:
                api_text = f"✅ INLINE Submission Complete\n"
                api_text += f"✅ TOP: INLINEINSPECTIONTOP\n"
                api_text += f"✅ BOTTOM: INLINEINSPECTIONBOTTOM\n"
                api_text += f"Barcode: {self.barcode}\n"
                api_text += f"Sequential submissions: {success_count}/{total_submissions}\n"
                api_text += f"Time: {datetime.now().isoformat()}"
                
                self.api_data_display.setPlainText(api_text)
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ Error in INLINE API submission: {e}")
            return False
    
    def prepare_top_api_data(self) -> Dict[str, Any]:
        """Prepare data for TOP API submission"""
        api_data = {
            'Barcode': self.barcode,
            'DT': datetime.now().isoformat(),
            'Process_id': 'INLINE_TOP_PROC_001',
            'Station_ID': 'INLINE_TOP_STATION_01'
        }
        
        # Add TOP inspection results
        for component in ["Screw", "Plate"]:
            step_key = f"TOP: {component}"
            if step_key in self.inspection_results:
                step_data = self.inspection_results[step_key]['data']
                
                # Add automatic result
                api_data[component] = step_data.get(component, 'UNKNOWN')
                
                # Add manual result (1/0)
                manual_key = f'Manual{component}'
                api_data[manual_key] = step_data.get(manual_key, 0)
        
        # Add overall TOP result
        top_result = "PASS" if self.check_top_results() else "FAIL"
        api_data['Result'] = top_result
        api_data['ManualResult'] = 1 if top_result == "PASS" else 0
        
        return api_data
    
    def prepare_bottom_api_data(self) -> Dict[str, Any]:
        """Prepare data for BOTTOM API submission"""
        api_data = {
            'Barcode': self.barcode,
            'DT': datetime.now().isoformat(),
            'Process_id': 'INLINE_BOTTOM_PROC_001',
            'Station_ID': 'INLINE_BOTTOM_STATION_01'
        }
        
        # Add BOTTOM inspection results
        for component in ["Antenna", "Capacitor", "Speaker"]:
            step_key = f"BOTTOM: {component}"
            if step_key in self.inspection_results:
                step_data = self.inspection_results[step_key]['data']
                
                # Add automatic result
                api_data[component] = step_data.get(component, 'UNKNOWN')
                
                # Add manual result (1/0)
                manual_key = f'Manual{component}'
                api_data[manual_key] = step_data.get(manual_key, 0)
        
        # Add overall BOTTOM result
        bottom_result = "PASS" if self.check_bottom_results() else "FAIL"
        api_data['Result'] = bottom_result
        api_data['ManualResult'] = 1 if bottom_result == "PASS" else 0
        
        return api_data
    
    def show_completion_message(self, result, total_time):
        """Show INLINE-specific completion message"""
        failed_top = []
        failed_bottom = []
        
        # Check TOP failures
        for component in ["Screw", "Plate"]:
            step_key = f"TOP: {component}"
            if step_key in self.inspection_results:
                manual_result = self.inspection_results[step_key]['data'].get(f'Manual{component}', 0)
                if manual_result != 1:
                    failed_top.append(component)
        
        # Check BOTTOM failures
        for component in ["Antenna", "Capacitor", "Speaker"]:
            step_key = f"BOTTOM: {component}"
            if step_key in self.inspection_results:
                manual_result = self.inspection_results[step_key]['data'].get(f'Manual{component}', 0)
                if manual_result != 1:
                    failed_bottom.append(component)
        
        msg = f"INLINE Inspection Complete!\n\n"
        msg += f"Overall Result: {result}\n"
        msg += f"Total Time: {total_time:.1f}s\n"
        msg += f"Steps Completed: {len(self.inspection_results)}/{len(self.inspection_steps)}\n\n"
        
        msg += f"TOP Inspection: {'✅ PASS' if not failed_top else '❌ FAIL'}\n"
        if failed_top:
            msg += f"  Failed: {', '.join(failed_top)}\n"
        
        msg += f"BOTTOM Inspection: {'✅ PASS' if not failed_bottom else '❌ FAIL'}\n"
        if failed_bottom:
            msg += f"  Failed: {', '.join(failed_bottom)}\n"
        
        if result == "PASS":
            msg += "\n✅ All INLINE checks passed!"
            msg += "\nClick 'Submit to API' to send results to both endpoints sequentially."
            QMessageBox.information(self, "INLINE Inspection Complete", msg)
        else:
            msg += "\n❌ INLINE inspection failed!"
            msg += "\n\nDo you want to apply manual override?"
            reply = QMessageBox.question(self, "INLINE Inspection Failed", msg,
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.manual_override()


def main():
    """Main function for testing INLINE inspection window"""
    app = QApplication(sys.argv)
    
    # Test the INLINE window
    window = INLINEInspectionWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()