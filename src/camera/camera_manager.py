from enum import Enum
import cv2
import numpy as np
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, Qt
from PyQt5.QtGui import QImage
from dataclasses import dataclass
from typing import Optional, Dict, Tuple
import logging
import os
from datetime import datetime

class CameraState(Enum):
    STOPPED = 0
    PREVIEW = 1
    CAPTURED = 2
    ANALYZING = 3
    ERROR = 4

@dataclass
class InspectionResult:
    original: np.ndarray
    annotated: np.ndarray
    result: str

class CameraManager(QObject):
    # Signals
    frame_ready = pyqtSignal(QImage)  # Emits concatenated display frame
    state_changed = pyqtSignal(CameraState)
    analysis_complete = pyqtSignal(InspectionResult)
    error_occurred = pyqtSignal(str)

    def __init__(self, 
                 camera_id: int = 0,
                 frame_width: int = 640,
                 frame_height: int = 480,
                 fps: int = 30,
                 save_path: str = "inspection_images"):
        super().__init__()
        
        # Camera settings
        self._camera_id = camera_id
        self._capture = None
        self.frame_width = frame_width
        self.frame_height = frame_height
        self._state = CameraState.STOPPED
        
        # Frame handling
        self._current_frame = None
        self._captured_frame = None
        self._display_frame = None
        
        # Display settings
        self.flip_horizontal = False
        self.flip_vertical = False
        self.exposure = 0
        
        # Timer for preview
        self._timer = QTimer()
        self._timer.timeout.connect(self._read_frame)
        self._timer.setInterval(1000 // fps)
        
        # Save settings
        self.save_path = save_path
        os.makedirs(save_path, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("CameraManager")

    def start_preview(self) -> bool:
        """Start camera preview"""
        try:
            if self._state != CameraState.STOPPED:
                self.stop()
                
            self._capture = cv2.VideoCapture(self._camera_id)
            if not self._capture.isOpened():
                raise RuntimeError("Failed to open camera")
                
            # Configure camera
            self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self._capture.set(cv2.CAP_PROP_EXPOSURE, self.exposure)
            
            self._state = CameraState.PREVIEW
            self.state_changed.emit(self._state)
            self._timer.start()
            self.logger.info("Camera preview started")
            return True
            
        except Exception as e:
            self._handle_error(f"Failed to start preview: {str(e)}")
            return False

    def capture_frame(self) -> bool:
        """Capture current frame for analysis"""
        if self._state != CameraState.PREVIEW:
            return False
            
        try:
            if self._current_frame is None:
                raise RuntimeError("No frame available")
                
            self._captured_frame = self._current_frame.copy()
            self._state = CameraState.CAPTURED
            self.state_changed.emit(self._state)
            self._timer.stop()
            
            # Show split view with waiting message
            waiting_frame = self._create_message_frame("Analysis in progress...")
            self._update_display(self._captured_frame, waiting_frame)
            
            self.logger.info("Frame captured successfully")
            return True
            
        except Exception as e:
            self._handle_error(f"Frame capture failed: {str(e)}")
            return False

    def analyze_frame(self, algorithm_func) -> Optional[InspectionResult]:
        """Run analysis algorithm on captured frame"""
        if self._state != CameraState.CAPTURED or self._captured_frame is None:
            return None
            
        try:
            self._state = CameraState.ANALYZING
            self.state_changed.emit(self._state)
            
            # Run algorithm
            result = algorithm_func(self._captured_frame)
            
            if not isinstance(result, dict) or 'annotated' not in result or 'result' not in result:
                raise ValueError("Invalid algorithm output format")
                
            # Create inspection result
            inspection_result = InspectionResult(
                original=self._captured_frame,
                annotated=result['annotated'],
                result=result['result'])
            
            # Update display
            self._update_display(inspection_result.original, inspection_result.annotated)
            
            # Save images if result is FAIL
            if inspection_result.result == "FAIL":
                self._save_inspection_images(inspection_result)
            
            self.analysis_complete.emit(inspection_result)
            return inspection_result
            
        except Exception as e:
            self._handle_error(f"Analysis failed: {str(e)}")
            return None

    def resume_preview(self):
        """Resume live preview"""
        if self._state in [CameraState.CAPTURED, CameraState.ANALYZING]:
            self._captured_frame = None
            self._state = CameraState.PREVIEW
            self.state_changed.emit(self._state)
            self._timer.start()
            self.logger.info("Preview resumed")

    def stop(self):
        """Stop camera and cleanup"""
        self._timer.stop()
        if self._capture:
            self._capture.release()
        self._capture = None
        self._current_frame = None
        self._captured_frame = None
        self._state = CameraState.STOPPED
        self.state_changed.emit(self._state)
        self.logger.info("Camera stopped")

    def _read_frame(self):
        """Read and process camera frame"""
        if not self._capture or self._state != CameraState.PREVIEW:
            return
            
        ret, frame = self._capture.read()
        if not ret:
            self._handle_error("Failed to read frame")
            return
            
        # Apply transformations
        if self.flip_horizontal:
            frame = cv2.flip(frame, 1)
        if self.flip_vertical:
            frame = cv2.flip(frame, 0)
            
        self._current_frame = frame
        
        # Show split view with waiting message
        waiting_frame = self._create_message_frame("Waiting for capture...")
        self._update_display(frame, waiting_frame)

    def _update_display(self, left: np.ndarray, right: np.ndarray):
        """Update split-screen display"""
        try:
            # Resize frames
            left = cv2.resize(left, (self.frame_width, self.frame_height))
            right = cv2.resize(right, (self.frame_width, self.frame_height))
            
            # Add separator
            separator = np.full((self.frame_height, 2, 3), 255, dtype=np.uint8)
            
            # Combine frames
            combined = np.hstack((left, separator, right))
            
            # Convert to QImage
            rgb = cv2.cvtColor(combined, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
            
            self.frame_ready.emit(qimg)
            
        except Exception as e:
            self._handle_error(f"Display update failed: {str(e)}")

    def _create_message_frame(self, text: str, color=(255, 255, 255)) -> np.ndarray:
        """Create message frame with text"""
        frame = np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)
        font = cv2.FONT_HERSHEY_SIMPLEX
        textsize = cv2.getTextSize(text, font, 1, 2)[0]
        
        x = (self.frame_width - textsize[0]) // 2
        y = (self.frame_height + textsize[1]) // 2
        
        cv2.putText(frame, text, (x, y), font, 1, color, 2)
        return frame

    def _save_inspection_images(self, result: InspectionResult):
        """Save inspection images for failed results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save original
        orig_path = os.path.join(self.save_path, f"fail_{timestamp}_original.jpg")
        cv2.imwrite(orig_path, result.original)
        
        # Save annotated
        annot_path = os.path.join(self.save_path, f"fail_{timestamp}_annotated.jpg")
        cv2.imwrite(annot_path, result.annotated)
        
        self.logger.info(f"Saved inspection images: {orig_path}, {annot_path}")

    def _handle_error(self, message: str):
        """Handle errors uniformly"""
        self.logger.error(message)
        self.error_occurred.emit(message)
        self._state = CameraState.ERROR
        self.state_changed.emit(self._state)
        
        # Show error in display
        if self._captured_frame is not None:
            error_frame = self._create_message_frame("ERROR!", (0, 0, 255))
            self._update_display(self._captured_frame, error_frame)