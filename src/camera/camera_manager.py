from enum import Enum
import cv2
import numpy as np
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, Qt
from PyQt5.QtGui import QImage
from dataclasses import dataclass
from typing import Optional, Dict, Tuple, List
import logging
import os
import json
from datetime import datetime
from pathlib import Path

class CameraState(Enum):
    STOPPED = 0
    PREVIEW = 1
    CAPTURED = 2
    ANALYZING = 3
    STREAMING = 4
    FREEZING = 5
    ERROR = 6

@dataclass
class InspectionResult:
    original: np.ndarray
    annotated: np.ndarray
    result: str
    status: Dict
    results: Dict

@dataclass
class CameraConfig:
    """Camera configuration loaded from JSON"""
    camera_id: int = 0
    simulation_mode: bool = False
    frame_width: int = 640
    frame_height: int = 480
    fps: int = 30
    exposure: int = 0
    flip_horizontal: bool = False
    flip_vertical: bool = False
    # Capture-specific (high-res) settings used when the user clicks Capture
    capture_frame_width: int = 1920
    capture_frame_height: int = 1080
    capture_flip_horizontal: bool = True
    capture_flip_vertical: bool = False
    auto_white_balance: bool = True
    brightness: int = 0
    contrast: int = 0
    saturation: int = 0
    capture_frames_for_averaging: int = 5
    save_path: str = "inspection_images"
    
    @classmethod
    def from_json(cls, config_path: str):
        """Load camera config from JSON file"""
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
            camera_settings = data.get('camera_settings', {})
            return cls(**camera_settings)
        except Exception as e:
            logging.warning(f"Failed to load camera config from {config_path}: {e}")
            return cls()  # Use defaults

class CameraManager(QObject):
    # Signals
    frame_ready = pyqtSignal(QImage)  # Emits concatenated display frame
    state_changed = pyqtSignal(CameraState)
    analysis_complete = pyqtSignal(InspectionResult)
    error_occurred = pyqtSignal(str)
    capture_progress = pyqtSignal(int, int)  # current_frame, total_frames

    def __init__(self, config_path: Optional[str] = None):
        super().__init__()
        
        # Load configuration
        if config_path is None:
            # Look for camera_config.json in configs folder
            proj_root = Path(__file__).resolve().parents[2]
            config_path = proj_root / "configs" / "camera_config.json"
        
        self.config = CameraConfig.from_json(str(config_path))
        
        # Camera settings
        self._capture = None
        self._temp_capture = None
        self._state = CameraState.STOPPED
        self._simulation_mode = False
        
        # Frame handling
        self._current_frame = None
        self._captured_frames: List[np.ndarray] = []
        self._averaged_frame = None
        self._display_frame = None
        
        # Timer for preview
        self._timer = QTimer()
        self._timer.timeout.connect(self._read_frame)
        self._timer.setInterval(1000 // self.config.fps)
        
        # Timer for capture sequence
        self._capture_timer = QTimer()
        self._capture_timer.timeout.connect(self._capture_next_frame)
        self._capture_frame_count = 0
        
        # Create save directory
        os.makedirs(self.config.save_path, exist_ok=True)
        
        # Load display and capture settings from config
        self._load_additional_settings(config_path)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("CameraManager")

    def _load_additional_settings(self, config_path: str):
        """Load display and capture settings from config"""
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
            
            self.display_settings = data.get('display_settings', {})
            self.capture_settings = data.get('capture_settings', {})
            
        except Exception as e:
            self.logger.warning(f"Failed to load additional settings: {e}")
            self.display_settings = {}
            self.capture_settings = {}

    def start_streaming(self) -> bool:
        """Start camera streaming for inspection"""
        try:
            if self._state != CameraState.STOPPED:
                self.stop()
                
            # Check if simulation mode is enabled
            if getattr(self.config, 'simulation_mode', False):
                self._simulation_mode = True
                self._capture = None
                self.logger.info("Starting camera in simulation mode")
            else:
                self._simulation_mode = False
                self._capture = cv2.VideoCapture(self.config.camera_id)
                if not self._capture.isOpened():
                    self.logger.warning("Failed to open camera, falling back to simulation mode")
                    self._simulation_mode = True
                    self._capture = None
                else:
                    # Configure camera properties
                    self._configure_camera()
            
            self._state = CameraState.STREAMING
            self.state_changed.emit(self._state)
            self._timer.start()
            self.logger.info("Camera streaming started")
            return True
            
        except Exception as e:
            self._handle_error(f"Failed to start streaming: {str(e)}")
            return False

    def _configure_camera(self):
        """Configure camera properties from config"""
        if not self._capture:
            return
            
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.frame_width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.frame_height)
        self._capture.set(cv2.CAP_PROP_EXPOSURE, self.config.exposure)
        
        if hasattr(cv2, 'CAP_PROP_AUTO_WB'):
            self._capture.set(cv2.CAP_PROP_AUTO_WB, 1 if self.config.auto_white_balance else 0)
        
        if self.config.brightness != 0:
            self._capture.set(cv2.CAP_PROP_BRIGHTNESS, self.config.brightness)
        if self.config.contrast != 0:
            self._capture.set(cv2.CAP_PROP_CONTRAST, self.config.contrast)
        if self.config.saturation != 0:
            self._capture.set(cv2.CAP_PROP_SATURATION, self.config.saturation)

    def trigger_capture_and_average(self) -> bool:
        """Trigger capture sequence that will freeze feed and capture multiple frames for averaging"""
        if self._state != CameraState.STREAMING:
            self.logger.warning("Cannot capture - camera not streaming")
            return False
            
        try:
            # Clear previous captures
            self._captured_frames.clear()
            self._capture_frame_count = 0
            
            # Freeze the display
            self._state = CameraState.FREEZING
            self.state_changed.emit(self._state)
            
            # Show freeze message
            if self._current_frame is not None:
                self._update_display(self._current_frame)
            
            # If possible, open a dedicated high-resolution capture for the actual capture
            try:
                if not self._simulation_mode:
                    # Create temporary high-res capture so live stream can remain low-res for visualization
                    self._temp_capture = cv2.VideoCapture(self.config.camera_id)
                    # Set desired resolution for captured frames (from config)
                    try:
                        self._temp_capture.set(cv2.CAP_PROP_FRAME_WIDTH, int(self.config.capture_frame_width))
                        self._temp_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, int(self.config.capture_frame_height))
                    except Exception:
                        # ignore failures to set properties
                        pass
            except Exception:
                # If temporary capture fails, continue using the main capture
                self._temp_capture = None

            # Start capture sequence (captures from temp_capture if available)
            self._capture_timer.start(100)  # Capture every 100ms
            self.logger.info("Started capture sequence")
            return True
            
        except Exception as e:
            self._handle_error(f"Capture trigger failed: {str(e)}")
            return False

    def _capture_next_frame(self):
        """Capture next frame in the averaging sequence"""
        source_cap = self._temp_capture if self._temp_capture is not None else self._capture
        if not source_cap or self._capture_frame_count >= self.config.capture_frames_for_averaging:
            self._capture_timer.stop()
            self._finalize_capture()
            return
        ret, frame = source_cap.read()
        if not ret:
            self._handle_error("Failed to capture frame for averaging")
            return
        # If using the dedicated capture, apply user-requested flip
        # Apply capture-specific flip if using the temporary high-res capture
        try:
            if self._temp_capture is not None and getattr(self.config, 'capture_flip_horizontal', False):
                frame = cv2.flip(frame, 1)
            if self._temp_capture is not None and getattr(self.config, 'capture_flip_vertical', False):
                frame = cv2.flip(frame, 0)
        except Exception:
            pass

        # Apply transformations (config flip settings etc.)
        processed_frame = self._apply_transformations(frame)
        self._captured_frames.append(processed_frame.copy())
        self._capture_frame_count += 1
        
        # Emit progress
        self.capture_progress.emit(self._capture_frame_count, self.config.capture_frames_for_averaging)
        
        # Update display with just the captured frame
        self._update_display(processed_frame)

    def _finalize_capture(self):
        """Average the captured frames and prepare for analysis"""
        try:
            if len(self._captured_frames) == 0:
                raise RuntimeError("No frames captured")
                
            # Calculate averaged frame
            self._averaged_frame = self._calculate_frame_average(self._captured_frames)
            
            # Apply preprocessing if configured
            if self.capture_settings.get('preprocessing', {}).get('histogram_equalization', False):
                self._averaged_frame = self._apply_histogram_equalization(self._averaged_frame)
                
            if self.capture_settings.get('preprocessing', {}).get('noise_reduction', False):
                self._averaged_frame = self._apply_noise_reduction(self._averaged_frame)
            
            # Save averaged frame
            self._save_averaged_frame()
            
            # Update state
            self._state = CameraState.CAPTURED
            self.state_changed.emit(self._state)
            
            # Show captured result
            self._update_display(self._averaged_frame)
            
            self.logger.info(f"Captured and averaged {len(self._captured_frames)} frames")
            
        except Exception as e:
            self._handle_error(f"Frame averaging failed: {str(e)}")

    def _calculate_frame_average(self, frames: List[np.ndarray]) -> np.ndarray:
        """Calculate average of multiple frames"""
        method = self.capture_settings.get('averaging_method', 'mean')
        
        if method == 'mean':
            return np.mean(frames, axis=0).astype(np.uint8)
        elif method == 'median':
            return np.median(frames, axis=0).astype(np.uint8)
        else:
            # Default to mean
            return np.mean(frames, axis=0).astype(np.uint8)

    def _apply_histogram_equalization(self, frame: np.ndarray) -> np.ndarray:
        """Apply histogram equalization"""
        # Convert to YUV, equalize Y channel, convert back
        yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
        yuv[:,:,0] = cv2.equalizeHist(yuv[:,:,0])
        return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)

    def _apply_noise_reduction(self, frame: np.ndarray) -> np.ndarray:
        """Apply noise reduction"""
        kernel_size = self.capture_settings.get('preprocessing', {}).get('gaussian_blur_kernel', 3)
        return cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)

    def _save_averaged_frame(self):
        """Save the averaged frame"""
        if self._averaged_frame is not None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"averaged_capture_{timestamp}.jpg"
            filepath = os.path.join(self.config.save_path, filename)
            cv2.imwrite(filepath, self._averaged_frame)
            
            # Also save to configs for easy access
            config_path = Path(__file__).resolve().parents[2] / "configs" / "averaged_capture.jpg"
            cv2.imwrite(str(config_path), self._averaged_frame)

    def analyze_frame_with_algorithm(self, algorithm_engine, mode: str, **kwargs) -> Optional[InspectionResult]:
        """Run analysis algorithm on captured averaged frame"""
        if self._state != CameraState.CAPTURED or self._averaged_frame is None:
            self.logger.warning("Cannot analyze - no captured frame available")
            return None
            
        try:
            self._state = CameraState.ANALYZING
            self.state_changed.emit(self._state)
            
            # Show the frame being analyzed
            self._update_display(self._averaged_frame)
            
            # Run algorithm
            result = algorithm_engine.process(self._averaged_frame, mode, **kwargs)
            
            if not isinstance(result, dict):
                raise ValueError("Invalid algorithm output format")
                
            # Extract results
            original_frame = result.get('original_frame', self._averaged_frame)
            processed_frame = result.get('processed_annotated', self._averaged_frame)
            status = result.get('status', {'status_code': 1, 'message': 'Unknown status'})
            results = result.get('results', {})
            
            # Determine overall result
            overall_result = self._determine_overall_result(status, results)
            
            # Create inspection result
            inspection_result = InspectionResult(
                original=original_frame,
                annotated=processed_frame,
                result=overall_result,
                status=status,
                results=results
            )
            # Release temporary high-res capture if it was used
            try:
                if self._temp_capture is not None:
                    try:
                        self._temp_capture.release()
                    except Exception:
                        pass
                    self._temp_capture = None
            except Exception:
                pass
            
            # Update display with processed result
            self._update_display(processed_frame)
            
            # Save images if result is FAIL
            if overall_result == "FAIL":
                self._save_inspection_images(inspection_result)
            
            self.analysis_complete.emit(inspection_result)
            self.logger.info(f"Analysis completed: {overall_result}")
            return inspection_result
            
        except Exception as e:
            self._handle_error(f"Analysis failed: {str(e)}")
            return None

    def _determine_overall_result(self, status: Dict, results: Dict) -> str:
        """Determine overall result from algorithm output"""
        if status.get('status_code', 1) != 0:
            return "ERROR"
            
        # Check if any result is 0 (fail)
        for key, value in results.items():
            if isinstance(value, (int, float)) and value == 0:
                return "FAIL"
                
        return "PASS"

    def resume_streaming(self):
        """Resume live streaming after capture/analysis"""
        if self._state in [CameraState.CAPTURED, CameraState.ANALYZING]:
            self._captured_frames.clear()
            self._averaged_frame = None
            self._state = CameraState.STREAMING
            self.state_changed.emit(self._state)
            self._timer.start()
            self.logger.info("Streaming resumed")

    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get current live frame"""
        return self._current_frame.copy() if self._current_frame is not None else None

    def get_averaged_frame(self) -> Optional[np.ndarray]:
        """Get the last averaged captured frame"""
        return self._averaged_frame.copy() if self._averaged_frame is not None else None

    def stop(self):
        """Stop camera and cleanup"""
        self._timer.stop()
        self._capture_timer.stop()
        if self._capture:
            self._capture.release()
        self._capture = None
        self._current_frame = None
        self._captured_frames.clear()
        self._averaged_frame = None
        self._state = CameraState.STOPPED
        self.state_changed.emit(self._state)
        self.logger.info("Camera stopped")

    def _read_frame(self):
        """Read and process camera frame for live streaming"""
        if self._state != CameraState.STREAMING:
            return
            
        if self._simulation_mode:
            # Generate simulation frame
            frame = self._create_simulation_frame()
        else:
            if not self._capture:
                return
            ret, frame = self._capture.read()
            if not ret:
                self._handle_error("Failed to read frame")
                return
        
        # Apply transformations
        processed_frame = self._apply_transformations(frame)
        self._current_frame = processed_frame
        
        # Show live view without any message overlay
        self._update_display(processed_frame)

    def _apply_transformations(self, frame: np.ndarray) -> np.ndarray:
        """Apply flip and other transformations to frame"""
        if self.config.flip_horizontal:
            frame = cv2.flip(frame, 1)
        if self.config.flip_vertical:
            frame = cv2.flip(frame, 0)
        return frame

    def _pad_frame_to_display_size(self, frame: np.ndarray) -> np.ndarray:
        """Pad frame to display size while maintaining aspect ratio"""
        try:
            target_width = self.config.frame_width
            target_height = self.config.frame_height
            
            # Get original frame dimensions
            original_height, original_width = frame.shape[:2]
            
            # Calculate scaling factor to fit within target dimensions
            scale_w = target_width / original_width
            scale_h = target_height / original_height
            scale = min(scale_w, scale_h)  # Use smaller scale to fit within bounds
            
            # Calculate new dimensions
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
            
            # Resize frame with calculated dimensions
            resized_frame = cv2.resize(frame, (new_width, new_height))
            
            # Create padded frame with target dimensions
            padded_frame = np.zeros((target_height, target_width, 3), dtype=np.uint8)
            
            # Calculate padding offsets to center the image
            y_offset = (target_height - new_height) // 2
            x_offset = (target_width - new_width) // 2
            
            # Place resized frame in center of padded frame
            padded_frame[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized_frame
            
            return padded_frame
            
        except Exception as e:
            self.logger.error(f"Frame padding failed: {str(e)}")
            # Fallback to resize if padding fails
            return cv2.resize(frame, (target_width, target_height))

    def _update_display(self, frame: np.ndarray):
        """Update display with single frame"""
        try:
            # Pad frame to config dimensions while maintaining aspect ratio
            frame = self._pad_frame_to_display_size(frame)
            
            # Convert to QImage
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
            
            self.frame_ready.emit(qimg)
            
        except Exception as e:
            self._handle_error(f"Display update failed: {str(e)}")

    def _create_message_frame(self, text: str, color=(255, 255, 255)) -> np.ndarray:
        """Create message frame with text"""
        frame = np.zeros((self.config.frame_height, self.config.frame_width, 3), dtype=np.uint8)
        
        # Get text color from config
        text_color = tuple(self.display_settings.get('status_text_color', [255, 255, 255]))
        text_size = self.display_settings.get('status_text_size', 0.7)
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        textsize = cv2.getTextSize(text, font, text_size, 2)[0]
        
        x = (self.config.frame_width - textsize[0]) // 2
        y = (self.config.frame_height + textsize[1]) // 2
        
        cv2.putText(frame, text, (x, y), font, text_size, text_color, 2)
        return frame
    
    def _create_simulation_frame(self) -> np.ndarray:
        """Create a simulation frame when no camera is available"""
        import time
        import math
        
        # Create base frame
        frame = np.zeros((self.config.frame_height, self.config.frame_width, 3), dtype=np.uint8)
        
        # Add gradient background
        for y in range(self.config.frame_height):
            for x in range(self.config.frame_width):
                frame[y, x] = [
                    int(50 + 50 * math.sin(x * 0.01)),
                    int(50 + 50 * math.sin(y * 0.01)), 
                    int(100 + 50 * math.sin((x+y) * 0.005))
                ]
        
        # Add moving pattern
        t = time.time()
        center_x = int(self.config.frame_width / 2 + 100 * math.sin(t))
        center_y = int(self.config.frame_height / 2 + 50 * math.cos(t * 1.5))
        
        cv2.circle(frame, (center_x, center_y), 30, (255, 255, 255), -1)
        cv2.circle(frame, (center_x, center_y), 30, (0, 255, 0), 3)
        
        # Add text
        cv2.putText(frame, "SIMULATION MODE", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, f"Time: {int(t % 60)}s", 
                   (10, self.config.frame_height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame

    def _save_inspection_images(self, result: InspectionResult):
        """Save inspection images for failed results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save original
        orig_path = os.path.join(self.config.save_path, f"fail_{timestamp}_original.jpg")
        cv2.imwrite(orig_path, result.original)
        
        # Save annotated
        annot_path = os.path.join(self.config.save_path, f"fail_{timestamp}_annotated.jpg")
        cv2.imwrite(annot_path, result.annotated)
        
        # Save results as JSON
        json_path = os.path.join(self.config.save_path, f"fail_{timestamp}_results.json")
        with open(json_path, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'result': result.result,
                'status': result.status,
                'results': result.results
            }, f, indent=2)
        
        self.logger.info(f"Saved inspection images and results: {orig_path}, {annot_path}, {json_path}")

    def _handle_error(self, message: str):
        """Handle errors uniformly"""
        self.logger.error(message)
        self.error_occurred.emit(message)
        self._state = CameraState.ERROR
        self.state_changed.emit(self._state)
        
        # Show error in display
        if self._captured_frame is not None:
            self._update_display(self._captured_frame)