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
try:
    from .base_inspection_window import BaseInspectionWindow
except ImportError:
    from base_inspection_window import BaseInspectionWindow

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.api_manager import APIManager
from config.config_manager import get_config_manager
from ml.algorithm_engine import AlgorithmEngine 


class INLINEInspectionWindow(BaseInspectionWindow):
    """INLINE Inspection Window for both TOP and BOTTOM inspections"""
    
    def __init__(self, parent=None):
        super().__init__(parent, "INLINE")
        self.top_inspection_complete = False
        self.bottom_inspection_complete = False
        self.top_api_manager = None
        self.bottom_api_manager = None
        self.engine = AlgorithmEngine(config_path="configs/algo.json", debug=False)
        
        # Initialize API managers for INLINE workflow
        self.init_api_manager()
        
        # Override submit button connection to use INLINE custom method
        if hasattr(self, 'submit_data_button') and self.submit_data_button:
            # Disconnect base class connection
            self.submit_data_button.clicked.disconnect()
            # Connect to INLINE custom submit method
            self.submit_data_button.clicked.connect(self.submit_data)
    
    def get_inspection_steps(self) -> List[str]:
        """Return INLINE inspection steps - simplified to match capture requirements"""
        return [
            # BOTTOM inspection - single capture for all components
            "BOTTOM: Capture",  # Captures Antenna, Capacitor, Speaker in one step
            # TOP inspection - single capture for all components  
            "TOP: Capture"      # Captures Screw, Plate in one step
        ]
    
    def get_camera_inspection_params(self) -> dict:
        """Get camera parameters for INLINE inspection"""
        current_step_name = self.inspection_steps[self.current_step] if self.current_step < len(self.inspection_steps) else "BOTTOM: Capture"
        
        if "BOTTOM" in current_step_name:
            return {
                'submode': 'bottom',
                'reference': 'bottom_ref'
            }
        elif "TOP" in current_step_name:
            return {
                'submode': 'top', 
                'reference': 'top_ref'
            }
        else:
            # Default to bottom
            return {
                'submode': 'bottom',
                'reference': 'bottom_ref'
            }
    
    def init_api_manager(self):
        """Initialize API managers for both INLINE BOTTOM and TOP using configuration"""
        try:
            print("🔧 Initializing INLINE API managers...")
            
            # Get configuration manager
            config = get_config_manager()
            
            # Get all available workflows
            workflows = config.get_enabled_workflows()
            
            # Initialize BOTTOM inspection API manager (CHIP -> INLINE_BOTTOM)
            bottom_workflow = config.get_workflow_by_name("CHIP_TO_INLINE_BOTTOM")
            
            if bottom_workflow:
                api1_url = config.get_api_endpoint_url(bottom_workflow['api1_table'])
                api2_url = config.get_api_endpoint_url(bottom_workflow['api2_table'])
                
                self.bottom_api_manager = APIManager(
                    api1_url=api1_url,
                    api2_url=api2_url,
                    placeholders=(bottom_workflow['api1_table'].lower(), bottom_workflow['api2_table'].lower())
                )
                print(f"✅ INLINE BOTTOM API Manager initialized:")
                print(f"   📡 API1: {api1_url} ({bottom_workflow['api1_table']})")
                print(f"   📡 API2: {api2_url} ({bottom_workflow['api2_table']})")
            else:
                print("❌ CHIP_TO_INLINE_BOTTOM workflow not found in configuration")
            
            # Initialize TOP inspection API manager (INLINE_BOTTOM -> INLINE_TOP)
            top_workflow = config.get_workflow_by_name("INLINE_BOTTOM_TO_INLINE_TOP")
            
            if top_workflow:
                api1_url = config.get_api_endpoint_url(top_workflow['api1_table'])
                api2_url = config.get_api_endpoint_url(top_workflow['api2_table'])
                
                self.top_api_manager = APIManager(
                    api1_url=api1_url,
                    api2_url=api2_url,
                    placeholders=(top_workflow['api1_table'].lower(), top_workflow['api2_table'].lower())
                )
                print(f"✅ INLINE TOP API Manager initialized:")
                print(f"   📡 API1: {api1_url} ({top_workflow['api1_table']})")
                print(f"   📡 API2: {api2_url} ({top_workflow['api2_table']})")
            else:
                print("❌ INLINE_BOTTOM_TO_INLINE_TOP workflow not found in configuration")
                
            
            # Set the primary API manager for barcode validation
            # Priority: bottom_api_manager > top_api_manager > fallback to default
            if hasattr(self, 'bottom_api_manager') and self.bottom_api_manager:
                self.api_manager = self.bottom_api_manager
                print(f"🔧 Primary API manager set to BOTTOM for barcode validation")
            elif hasattr(self, 'top_api_manager') and self.top_api_manager:
                self.api_manager = self.top_api_manager
                print(f"🔧 Primary API manager set to TOP for barcode validation")
            else:
                # Fallback: Create a basic API manager for barcode validation using config
                print("⚠️ Creating fallback API manager for INLINE validation")
                fallback_api1 = config.get_api_endpoint_url("INLINEINSPECTIONBOTTOM")
                fallback_api2 = config.get_api_endpoint_url("INLINEINSPECTIONTOP")
                
                self.api_manager = APIManager(
                    api1_url=fallback_api1,
                    api2_url=fallback_api2,
                    placeholders=("inline bottom", "inline top")
                )
                print(f"✅ Fallback API manager created: {fallback_api1} -> {fallback_api2}")
            
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
        from datetime import datetime
        
        if step == "TOP: Capture":
            return self.collect_top_capture_data()
        elif step == "BOTTOM: Capture":
            return self.collect_bottom_capture_data()
        
        return {}
    
    def collect_top_capture_data(self) -> Dict[str, Any]:
        """Collect data for TOP inspection capture - Screw and Plate"""
        import random
        from datetime import datetime
        
        # Get configuration
        config = get_config_manager()
        
        # Get pass rates from configuration
        screw_pass_rate = config.get_component_pass_rate("SCREW")
        plate_pass_rate = config.get_component_pass_rate("PLATE")
        
        # Simulate algorithm results for components (1=PASS, 0=FAIL)
        screw_value = 1 if random.random() <= screw_pass_rate else 0
        plate_value = 1 if random.random() <= plate_pass_rate else 0
        
        # Get process and station IDs from configuration
        process_id = config.get_process_id("INLINE_TOP")
        station_id = config.get_station_id("INLINE_TOP")
        
        # Initialize data with None values (as per requirement d)
        data = {
            # Required fields
            "Barcode": None,  # Will be set during API submission
            "DT": datetime.now().isoformat(),
            "Process_id": process_id,
            "Station_ID": station_id,
            
            # Algorithm results (1/0 for database)
            "Screw": screw_value,
            "Plate": plate_value,
            "Result": None,  # Will be calculated
            
            # Manual fields (copied from algorithm results)
            "ManualScrew": screw_value,  # Copy algorithm result
            "ManualPlate": plate_value,  # Copy algorithm result
            "ManualResult": None  # Will be calculated
        }
        
        # Calculate overall result (requirement d: ManualResult = 1 only if all manual fields = 1)
        manual_result = 1 if (screw_value == 1 and plate_value == 1) else 0
        overall_result = 1 if manual_result == 1 else 0  # Store as 1/0 for database
        
        data["Result"] = overall_result
        data["ManualResult"] = manual_result
        
        # Store display-friendly versions for UI (keep the numeric values for API)
        data["_display"] = {
            "Screw": "PASS" if screw_value == 1 else "FAIL",
            "Plate": "PASS" if plate_value == 1 else "FAIL",
            "Result": "PASS" if overall_result == 1 else "FAIL"
        }
        
        return data
    
    def collect_bottom_capture_data(self) -> Dict[str, Any]:
        """Collect data for BOTTOM inspection capture step"""
        import random
        from datetime import datetime
        
        # Get configuration
        config = get_config_manager()
        
        # Get pass rates from configuration  
        antenna_pass_rate = config.get_component_pass_rate("ANTENNA")
        capacitor_pass_rate = config.get_component_pass_rate("CAPACITOR")
        speaker_pass_rate = config.get_component_pass_rate("SPEAKER")
        
        # Simulate algorithm results for components (1=PASS, 0=FAIL)
        antenna_value = 1 if random.random() <= antenna_pass_rate else 0
        capacitor_value = 1 if random.random() <= capacitor_pass_rate else 0
        speaker_value = 1 if random.random() <= speaker_pass_rate else 0
        
        # Get process and station IDs from configuration
        process_id = config.get_process_id("INLINE_BOTTOM")
        station_id = config.get_station_id("INLINE_BOTTOM")
        
        # Initialize data with None values (as per requirement d)
        data = {
            # Required fields
            "Barcode": None,  # Will be set during API submission
            "DT": datetime.now().isoformat(),
            "Process_id": process_id,
            "Station_ID": station_id,
            
            # Algorithm results (1/0 for database)
            "Antenna": antenna_value,
            "Capacitor": capacitor_value,
            "Speaker": speaker_value,
            "Result": None,  # Will be calculated
            
            # Manual fields (copied from algorithm results)
            "ManualAntenna": antenna_value,  # Copy algorithm result
            "ManualCapacitor": capacitor_value,  # Copy algorithm result
            "ManualSpeaker": speaker_value,  # Copy algorithm result
            "ManualResult": None  # Will be calculated
        }
        
        # Calculate overall result (requirement d: ManualResult = 1 only if all manual fields = 1)
        manual_result = 1 if (antenna_value == 1 and capacitor_value == 1 and speaker_value == 1) else 0
        overall_result = 1 if manual_result == 1 else 0  # Store as 1/0 for database
        
        data["Result"] = overall_result
        data["ManualResult"] = manual_result
        
        # Store display-friendly versions for UI (keep the numeric values for API)
        data["_display"] = {
            "Antenna": "PASS" if antenna_value == 1 else "FAIL",
            "Capacitor": "PASS" if capacitor_value == 1 else "FAIL", 
            "Speaker": "PASS" if speaker_value == 1 else "FAIL",
            "Result": "PASS" if overall_result == 1 else "FAIL"
        }
        
        return data
    
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
        
        if step == "TOP: Capture":
            # Validate that TOP capture has Screw and Plate data
            required_fields = ["Screw", "Plate", "ManualScrew", "ManualPlate", "Result", "ManualResult"]
            return all(field in data for field in required_fields)
        
        elif step == "BOTTOM: Capture":
            # Validate that BOTTOM capture has Antenna, Capacitor, Speaker data
            required_fields = ["Antenna", "Capacitor", "Speaker", "ManualAntenna", "ManualCapacitor", "ManualSpeaker", "Result", "ManualResult"]
            return all(field in data for field in required_fields)
        
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
        """Override to handle two-phase completion - only complete when both stages are submitted"""
        # Check if both stages have been submitted to API  
        bottom_submitted = hasattr(self, 'bottom_submitted') and self.bottom_submitted
        top_submitted = hasattr(self, 'top_submitted') and self.top_submitted
        
        # Only allow completion if both stages have been submitted
        if bottom_submitted and top_submitted:
            print("🎉 INLINE inspection complete - both stages submitted to API")
            super().complete_inspection()
        else:
            print("⏸️ INLINE inspection not completing automatically - waiting for API submissions")
            print(f"   BOTTOM submitted: {bottom_submitted}")
            print(f"   TOP submitted: {top_submitted}")
            
            # Just update the display without completing the inspection
            self.top_inspection_complete = self.check_top_inspection_complete()
            self.bottom_inspection_complete = self.check_bottom_inspection_complete()
            
            # Update API data display with both phases
            api_text = f"INLINE Inspection Status:\n"
            api_text += f"TOP: {'✅ Complete' if self.top_inspection_complete else '❌ Incomplete'}\n"
            api_text += f"BOTTOM: {'✅ Complete' if self.bottom_inspection_complete else '❌ Incomplete'}\n"
            api_text += f"Overall: {self.determine_overall_result()}\n"
            
            if self.top_inspection_complete and self.bottom_inspection_complete:
                api_text += "\nReady for sequential API submission\nClick Submit to API to proceed"
            
            self.api_data_display.setPlainText(api_text)
            
            # Enable submit button for the appropriate stage
            submit_enabled = self._should_enable_submit_for_inline()
            if hasattr(self, 'submit_data_button') and self.submit_data_button:
                self.submit_data_button.setEnabled(submit_enabled)
    
    def check_top_inspection_complete(self) -> bool:
        """Check if TOP inspection is complete"""
        top_steps = ["TOP: Setup", "TOP: Screw", "TOP: Plate"]
        return all(step in self.inspection_results for step in top_steps)
    
    def check_bottom_inspection_complete(self) -> bool:
        """Check if BOTTOM inspection is complete"""
        bottom_steps = ["BOTTOM: Setup", "BOTTOM: Antenna", "BOTTOM: Capacitor", "BOTTOM: Speaker"]
        
        # Debug: Print what we have vs what we expect
        print(f"\n🔍 DEBUG: Checking bottom inspection completion")
        print(f"Expected steps: {bottom_steps}")
        print(f"Available inspection results: {list(self.inspection_results.keys())}")
        
        for step in bottom_steps:
            is_present = step in self.inspection_results
            print(f"  Step '{step}': {'✅ Found' if is_present else '❌ Missing'}")
        
        result = all(step in self.inspection_results for step in bottom_steps)
        print(f"Bottom inspection complete: {result}")
        return result
    
    def perform_api_submissions(self) -> bool:
        """Perform INLINE API submissions - ONE stage per call for two-stage submission process"""
        try:
            print("\n🚀 Starting INLINE API Submissions...")
            print("="*50)
            
            # Determine which stage we're in
            bottom_complete = "BOTTOM: Capture" in self.inspection_results
            top_complete = "TOP: Capture" in self.inspection_results
            bottom_submitted = hasattr(self, 'bottom_submitted') and self.bottom_submitted
            top_submitted = hasattr(self, 'top_submitted') and self.top_submitted
            
            # Stage 1: BOTTOM inspection data submission to INLINEINSPECTIONBOTTOM
            if bottom_complete and not bottom_submitted:
                print(f"📤 Stage 1: INLINEINSPECTIONBOTTOM submission")
                success = self.submit_bottom_inspection()
                if success:
                    self.bottom_submitted = True
                    print("✅ BOTTOM inspection submitted successfully")
                    print("ℹ️ BOTTOM submitted successfully. Click Submit again for TOP when ready.")
                    return True  # Success - BOTTOM done, stop here for user to click again
                else:
                    print("❌ BOTTOM inspection submission failed")
                    return False
            
            # Stage 2: TOP inspection data submission to INLINEINSPECTIONTOP  
            elif top_complete and bottom_submitted and not top_submitted:
                print(f"📤 Stage 2: INLINEINSPECTIONTOP submission")
                success = self.submit_top_inspection()
                if success:
                    self.top_submitted = True
                    print("✅ TOP inspection submitted successfully")
                    print("🎉 All INLINE inspections completed!")
                    return True
                else:
                    print("❌ TOP inspection submission failed")
                    return False
            
            # Check if both are already submitted (complete success)
            elif bottom_submitted and top_submitted:
                print("✅ Both BOTTOM and TOP inspections already submitted")
                return True
            
            # Handle waiting states (not failures)
            elif bottom_submitted and not top_complete:
                print("ℹ️ BOTTOM already submitted. Waiting for TOP inspection to complete.")
                return True  # Not a failure, just waiting
            
            if not bottom_complete and not top_complete:
                print("⚠️ No inspections complete yet")
                return False
            elif not bottom_complete:
                print("⚠️ Waiting for BOTTOM inspection to complete")
                return False
                
            print("⚠️ Unexpected submission state")
            return False
            
        except Exception as e:
            print(f"❌ Error in INLINE API submission: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def submit_bottom_inspection(self) -> bool:
        """Submit BOTTOM inspection data to INLINEINSPECTIONBOTTOM table using CHIP_TO_INLINE_BOTTOM workflow"""
        try:
            # Prepare BOTTOM inspection data
            bottom_data = self.prepare_bottom_api_data()
            print(f"🎯 BOTTOM Data for INLINEINSPECTIONBOTTOM:")
            for key, value in bottom_data.items():
                print(f"   {key}: {value}")
            
            # Use bottom_api_manager with CHIP_TO_INLINE_BOTTOM workflow
            if self.bottom_api_manager:
                print(f"📡 Submitting to: {self.bottom_api_manager.api2_url} (INLINEINSPECTIONBOTTOM)")
                # Direct API call using the _call_api method to avoid data wrapping
                success, response = self.bottom_api_manager._call_api("post", self.bottom_api_manager.api2_url, bottom_data)
                
                if success:
                    print(f"✅ BOTTOM data successfully submitted to INLINEINSPECTIONBOTTOM table")
                else:
                    print(f"❌ BOTTOM data submission failed: {response}")
            else:
                print(f"❌ No BOTTOM API manager available for CHIP_TO_INLINE_BOTTOM workflow")
                success = False
            
            if success:
                # Update API display to show BOTTOM submission with display-friendly values
                antenna_display = "PASS" if bottom_data.get('Antenna', 0) == 1 else "FAIL"
                capacitor_display = "PASS" if bottom_data.get('Capacitor', 0) == 1 else "FAIL"
                speaker_display = "PASS" if bottom_data.get('Speaker', 0) == 1 else "FAIL"
                result_display = "PASS" if bottom_data.get('Result', 0) == 1 else "FAIL"
                
                self._update_api_display(f"✅ BOTTOM Submitted (INLINEINSPECTIONBOTTOM)\nAntenna: {antenna_display}\nCapacitor: {capacitor_display}\nSpeaker: {speaker_display}\nResult: {result_display}")
                
                # Set the BOTTOM submitted flag
                self.bottom_submitted = True
                
                # Update submit button state after successful BOTTOM submission
                self._set_submit_button_enabled(self._should_enable_submit_for_inline())
            
            return success
            
        except Exception as e:
            print(f"❌ BOTTOM submission error: {e}")
            return False
    
    def submit_top_inspection(self) -> bool:
        """Submit TOP inspection data to INLINEINSPECTIONTOP table using INLINE_BOTTOM_TO_INLINE_TOP workflow"""
        try:
            # Prepare TOP inspection data
            top_data = self.prepare_top_api_data()
            print(f"🎯 TOP Data for INLINEINSPECTIONTOP:")
            for key, value in top_data.items():
                print(f"   {key}: {value}")
            
            # Use top_api_manager with INLINE_BOTTOM_TO_INLINE_TOP workflow
            if self.top_api_manager:
                print(f"📡 Submitting to: {self.top_api_manager.api2_url} (INLINEINSPECTIONTOP)")
                # Direct API call using the _call_api method to avoid data wrapping
                success, response = self.top_api_manager._call_api("post", self.top_api_manager.api2_url, top_data)
                
                if success:
                    print(f"✅ TOP data successfully submitted to INLINEINSPECTIONTOP table")
                else:
                    print(f"❌ TOP data submission failed: {response}")
            else:
                print(f"❌ No TOP API manager available for INLINE_BOTTOM_TO_INLINE_TOP workflow")
                success = False
            
            if success:
                # Update API display to show both submissions complete with display-friendly values
                result_display = "PASS" if top_data.get('Result', 0) == 1 else "FAIL"
                self._update_api_display(f"✅ INLINE Complete\nBOTTOM: INLINEINSPECTIONBOTTOM ✓\nTOP: INLINEINSPECTIONTOP ✓\nOverall: {result_display}")
                
                # Set the TOP submitted flag
                self.top_submitted = True
                
                # Update submit button state after successful TOP submission
                self._set_submit_button_enabled(self._should_enable_submit_for_inline())
            
            return success
            
        except Exception as e:
            print(f"❌ TOP submission error: {e}")
            return False
    
    def prepare_top_api_data(self) -> Dict[str, Any]:
        """Prepare data for TOP API submission to INLINEINSPECTIONTOP table"""
        # Get the capture data from TOP inspection
        capture_step = "TOP: Capture"
        if capture_step not in self.inspection_results:
            raise ValueError("TOP inspection data not found")
        
        capture_data = self.inspection_results[capture_step]['data']
        
        # Prepare API data with barcode from current inspection
        api_data = capture_data.copy()  # Start with capture data
        api_data['Barcode'] = self.barcode  # Override with current barcode
        
        return api_data
    
    def prepare_bottom_api_data(self) -> Dict[str, Any]:
        """Prepare data for BOTTOM API submission to INLINEINSPECTIONBOTTOM table"""
        # Get the capture data from BOTTOM inspection
        capture_step = "BOTTOM: Capture"
        if capture_step not in self.inspection_results:
            raise ValueError("BOTTOM inspection data not found")
        
        capture_data = self.inspection_results[capture_step]['data']
        
        # Prepare API data with barcode from current inspection
        api_data = capture_data.copy()  # Start with capture data
        api_data['Barcode'] = self.barcode  # Override with current barcode
        
        return api_data

    def submit_data(self):
        """Custom submission method for INLINE inspection - handles two-stage submission"""
        try:
            if not self.api_manager:
                QMessageBox.warning(self, "API Error", "API Manager not available")
                return
            
            success = self.perform_api_submissions()
            bottom_complete = "BOTTOM: Capture" in self.inspection_results
            top_complete = "TOP: Capture" in self.inspection_results
            bottom_submitted = hasattr(self, 'bottom_submitted') and self.bottom_submitted
            top_submitted = hasattr(self, 'top_submitted') and self.top_submitted
            
            # Determine the submission status and show appropriate message
            if success:
                if bottom_submitted and top_submitted:
                    # Both stages completed
                    QMessageBox.information(self, "INLINE Submission Complete", 
                                          f"✅ Both INLINE inspection stages successfully submitted!\n\n"
                                          f"BOTTOM → INLINEINSPECTIONBOTTOM: ✅\n"
                                          f"TOP → INLINEINSPECTIONTOP: ✅\n\n"
                                          f"Barcode: {self.barcode}\n"
                                          f"Type: INLINE (Two-Stage)")
                    self.log_inspection_results()
                    self.reset_for_new_inspection()
                elif bottom_submitted and not top_complete:
                    # BOTTOM submitted, waiting for TOP inspection
                    QMessageBox.information(self, "BOTTOM Submitted - Stage 1/2 Complete", 
                                          f"✅ BOTTOM inspection data submitted to INLINEINSPECTIONBOTTOM!\n\n"
                                          f"📋 Status: Stage 1 of 2 Complete\n"
                                          f"⏳ Next: Complete TOP inspection, then click Submit again\n\n"
                                          f"🔄 The Submit button will re-enable for Stage 2\n"
                                          f"Barcode: {self.barcode}")
                elif bottom_submitted and top_complete and not top_submitted:
                    # TOP just submitted
                    QMessageBox.information(self, "TOP Submitted - Stage 2/2 Complete", 
                                          f"✅ TOP inspection data submitted to INLINEINSPECTIONTOP!\n\n"
                                          f"🎉 Both stages now complete!\n"
                                          f"BOTTOM → INLINEINSPECTIONBOTTOM: ✅\n"
                                          f"TOP → INLINEINSPECTIONTOP: ✅\n\n"
                                          f"Barcode: {self.barcode}")
                else:
                    # Some other success case
                    QMessageBox.information(self, "Data Submitted", 
                                          f"INLINE inspection data submitted successfully\n\n"
                                          f"Barcode: {self.barcode}\n"
                                          f"Type: INLINE")
            else:
                # Actual failure occurred
                QMessageBox.critical(self, "Submission Failed", 
                                   f"❌ Failed to submit INLINE inspection data\n\n"
                                   f"BOTTOM complete: {'✅' if bottom_complete else '❌'}\n"
                                   f"TOP complete: {'✅' if top_complete else '❌'}\n"
                                   f"BOTTOM submitted: {'✅' if bottom_submitted else '❌'}\n"
                                   f"TOP submitted: {'✅' if top_submitted else '❌'}\n\n"
                                   f"Please check the API connections and try again.")
            
            # Always update submit button state after any submission attempt
            self._set_submit_button_enabled(self._should_enable_submit_for_inline())
                
        except Exception as e:
            QMessageBox.critical(self, "Submission Error", f"Error submitting INLINE data: {e}")
            # Update submit button state even after errors
            self._set_submit_button_enabled(self._should_enable_submit_for_inline())
    
    def _should_enable_submit_for_inline(self) -> bool:
        """Custom INLINE submit button logic for two-stage submission"""
        bottom_complete = "BOTTOM: Capture" in self.inspection_results
        top_complete = "TOP: Capture" in self.inspection_results
        bottom_submitted = hasattr(self, 'bottom_submitted') and self.bottom_submitted
        top_submitted = hasattr(self, 'top_submitted') and self.top_submitted
        
        # Debug information
        print(f"🔍 INLINE Submit Button Check:")
        print(f"   BOTTOM complete: {bottom_complete}")
        print(f"   TOP complete: {top_complete}")
        print(f"   BOTTOM submitted: {bottom_submitted}")
        print(f"   TOP submitted: {top_submitted}")
        
        # Enable submit button for:
        # 1. First submission: BOTTOM complete but not yet submitted
        # 2. Second submission: BOTTOM submitted AND TOP complete but not yet submitted
        # 3. Failure cases: any component has failures (for manual override)
        
        # Check for failures (always enable submit for manual override)
        bottom_failures = self._inline_bottom_has_failures()
        top_failures = self._inline_top_has_failures()
        
        if bottom_failures or top_failures:
            print(f"   Submit enabled: True (failures detected)")
            return True
        
        # Stage 1: BOTTOM complete, not yet submitted
        if bottom_complete and not bottom_submitted:
            print(f"   Submit enabled: True (BOTTOM ready for first submission)")
            return True
            
        # Stage 2: BOTTOM submitted, TOP complete, not yet submitted
        if bottom_submitted and top_complete and not top_submitted:
            print(f"   Submit enabled: True (TOP ready for second submission)")
            return True
        
        # Both stages completed
        if bottom_submitted and top_submitted:
            print(f"   Submit enabled: False (both stages already submitted)")
            return False
        
        # Waiting for inspections to complete
        if not bottom_complete:
            print(f"   Submit enabled: False (waiting for BOTTOM inspection)")
        elif bottom_submitted and not top_complete:
            print(f"   Submit enabled: False (waiting for TOP inspection)")
        else:
            print(f"   Submit enabled: False (unexpected state)")
        
        return False
    
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