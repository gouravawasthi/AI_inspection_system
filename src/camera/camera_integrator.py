"""
Camera Integration Module for INLINE and EOLT Inspections
Handles camera streaming, frame capture, and algorithm integration
"""

import sys
import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from camera.camera_manager import CameraManager, CameraState, InspectionResult
from ml.algorithm_engine import AlgorithmEngine


class CameraIntegrator:
    """Integrates camera manager with algorithm engine for inspections"""
    
    def __init__(self, camera_config_path: Optional[str] = None, algo_config_path: Optional[str] = None):
        self.logger = logging.getLogger("CameraIntegrator")
        
        # Initialize camera manager
        self.camera = CameraManager(camera_config_path)
        
        # Initialize algorithm engine
        if algo_config_path is None:
            proj_root = Path(__file__).resolve().parents[2]
            algo_config_path = proj_root / "configs" / "algo.json"
        
        self.algorithm_engine = AlgorithmEngine(str(algo_config_path))
        
        # Connect signals
        self.camera.analysis_complete.connect(self._on_analysis_complete)
        self.camera.error_occurred.connect(self._on_camera_error)
        
        # Inspection state
        self._current_inspection_type = None
        self._current_inspection_params = {}
        
    def start_inspection_streaming(self, inspection_type: str, **params) -> bool:
        """Start camera streaming for inspection"""
        try:
            self._current_inspection_type = inspection_type.upper()
            self._current_inspection_params = params
            
            success = self.camera.start_streaming()
            if success:
                self.logger.info(f"Started {inspection_type} inspection streaming")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to start inspection streaming: {e}")
            return False
    
    def capture_and_analyze(self) -> bool:
        """Capture frames, average them, and run analysis"""
        if not self._current_inspection_type:
            self.logger.error("No inspection type set")
            return False
            
        try:
            # Trigger capture sequence
            success = self.camera.trigger_capture_and_average()
            if not success:
                return False
                
            # Analysis will be triggered automatically when capture completes
            # via the state machine in camera manager
            return True
            
        except Exception as e:
            self.logger.error(f"Capture and analyze failed: {e}")
            return False
    
    def _on_capture_completed(self):
        """Called when frame capture and averaging is complete"""
        try:
            if self._current_inspection_type == "INLINE":
                self._run_inline_analysis()
            elif self._current_inspection_type == "EOLT":
                self._run_eolt_analysis()
            else:
                self.logger.error(f"Unknown inspection type: {self._current_inspection_type}")
                
        except Exception as e:
            self.logger.error(f"Analysis execution failed: {e}")
    
    def _run_inline_analysis(self):
        """Run INLINE inspection analysis"""
        submode = self._current_inspection_params.get('submode', 'bottom')
        ref_key = self._current_inspection_params.get('reference', f'{submode}_ref')
        
        self.logger.info(f"Running INLINE analysis - submode: {submode}")
        
        result = self.camera.analyze_frame_with_algorithm(
            self.algorithm_engine,
            mode='inline',
            submode=submode,
            ref=ref_key
        )
        
        return result
    
    def _run_eolt_analysis(self):
        """Run EOLT inspection analysis"""
        side = self._current_inspection_params.get('side', 'front')
        ref_key = self._current_inspection_params.get('reference', f'{side}_ref')
        mask_key = self._current_inspection_params.get('mask', f'{side}_mask')
        
        self.logger.info(f"Running EOLT analysis - side: {side}")
        
        result = self.camera.analyze_frame_with_algorithm(
            self.algorithm_engine,
            mode='eolt',
            side=side,
            ref=ref_key,
            mask=mask_key
        )
        
        return result
    
    def _on_analysis_complete(self, result: InspectionResult):
        """Handle analysis completion"""
        self.logger.info(f"Analysis complete: {result.result}")
        # This signal is automatically forwarded to the inspection window
        # via the original signal connection in base_inspection_window.py
        
    def _on_camera_error(self, error_msg: str):
        """Handle camera errors"""
        self.logger.error(f"Camera error: {error_msg}")
    
    def stop_inspection(self):
        """Stop current inspection"""
        self.camera.stop()
        self._current_inspection_type = None
        self._current_inspection_params = {}
        self.logger.info("Inspection stopped")
    
    def get_camera_state(self) -> CameraState:
        """Get current camera state"""
        return self.camera._state
    
    def is_ready_for_capture(self) -> bool:
        """Check if camera is ready for capture"""
        return self.camera._state == CameraState.STREAMING
    
    def get_current_frame(self) -> Optional[Any]:
        """Get current live frame"""
        return self.camera.get_current_frame()
    
    def get_last_result(self) -> Optional[Any]:
        """Get last inspection result"""
        return getattr(self, '_last_result', None)


# Convenience functions for inspection windows
def create_camera_integrator() -> CameraIntegrator:
    """Create camera integrator with default configs"""
    return CameraIntegrator()

def start_inline_inspection(integrator: CameraIntegrator, submode: str = 'bottom') -> bool:
    """Start INLINE inspection"""
    return integrator.start_inspection_streaming('inline', submode=submode)

def start_eolt_inspection(integrator: CameraIntegrator, side: str = 'front') -> bool:
    """Start EOLT inspection"""
    return integrator.start_inspection_streaming('eolt', side=side)