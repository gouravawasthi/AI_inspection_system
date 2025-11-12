# Replace your existing CameraManager with this corrected implementation

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
    capture_progress = pyqtSignal(int, int) 
    capture_complete = pyqtSignal() # current_frame, total_frames

    def __init__(self, config_path: Optional[str] = None):
        super().__init__()

        # Load configuration
        if config_path is None:
            proj_root = Path(__file__).resolve().parents[2]
            config_path = proj_root / "configs" / "camera_config.json"

        self.config = CameraConfig.from_json(str(config_path))

        # Camera settings
        self._capture = None              # low-res preview capture
        self._temp_capture = None         # high-res capture used only for averaging
        self._state = CameraState.STOPPED
        self._simulation_mode = False

        # Frame handling
        self._current_frame: Optional[np.ndarray] = None
        self._captured_frames: List[np.ndarray] = []
        self._averaged_frame: Optional[np.ndarray] = None
        self._display_frame: Optional[np.ndarray] = None

        # Control whether high-res frames should be shown in GUI
        # We want GUI to show only low-res preview / frozen preview, not high-res frames
        self._suppress_display_during_capture = False

        # Timer for preview
        self._timer = QTimer()
        self._timer.timeout.connect(self._read_frame)
        self._timer.setInterval(max(1, 1000 // max(1, int(self.config.fps))))

        # Timer for capture sequence
        self._capture_timer = QTimer()
        self._capture_timer.timeout.connect(self._capture_next_frame)
        self._capture_frame_count = 0

        # Create save directory
        os.makedirs(self.config.save_path, exist_ok=True)

        # Load display and capture settings from config (if available)
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
            logging.warning(f"Failed to load additional settings: {e}")
            self.display_settings = {}
            self.capture_settings = {}

    def start_streaming(self) -> bool:
        """Start camera streaming for inspection (low-res preview)"""
        try:
            if self._state != CameraState.STOPPED:
                self.stop()

            # Simulation mode?
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
                    # release if partially opened
                    try:
                        if self._capture:
                            self._capture.release()
                    except Exception:
                        pass
                    self._capture = None
                else:
                    # Configure low-res preview properties
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
        """Configure low-res preview camera properties from config"""
        if not self._capture:
            return

        try:
            self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, int(self.config.frame_width))
            self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, int(self.config.frame_height))
            # Some backends don't accept exposure set; ignore failures
            try:
                self._capture.set(cv2.CAP_PROP_EXPOSURE, float(self.config.exposure))
            except Exception:
                pass

            if hasattr(cv2, 'CAP_PROP_AUTO_WB'):
                try:
                    self._capture.set(cv2.CAP_PROP_AUTO_WB, 1 if self.config.auto_white_balance else 0)
                except Exception:
                    pass

            if self.config.brightness != 0:
                try:
                    self._capture.set(cv2.CAP_PROP_BRIGHTNESS, float(self.config.brightness))
                except Exception:
                    pass
            if self.config.contrast != 0:
                try:
                    self._capture.set(cv2.CAP_PROP_CONTRAST, float(self.config.contrast))
                except Exception:
                    pass
            if self.config.saturation != 0:
                try:
                    self._capture.set(cv2.CAP_PROP_SATURATION, float(self.config.saturation))
                except Exception:
                    pass
        except Exception as e:
            self.logger.warning(f"Failed to configure camera: {e}")

    def trigger_capture_and_average(self) -> bool:
        """
        Trigger capture sequence:
           - freeze current preview in GUI
           - open a separate high-res capture (_temp_capture) to collect N frames
           - average them without streaming high-res frames to GUI
        """
        if self._state != CameraState.STREAMING:
            self.logger.warning("Cannot capture - camera not streaming")
            return False

        try:
            # Clear previous captures
            self._captured_frames.clear()
            self._capture_frame_count = 0

            # Freeze the display by showing the last preview frame (do not update with high-res frames)
            self._state = CameraState.FREEZING
            self.state_changed.emit(self._state)

            if self._current_frame is not None:
                # show current low-res frame (frozen)
                self._update_display(self._current_frame)

            # Try to open a dedicated high-res capture
            self._temp_capture = None
            if not self._simulation_mode:
                try:
                    self._temp_capture = cv2.VideoCapture(self.config.camera_id)
                    if not self._temp_capture.isOpened():
                        # fallback: release and set None
                        try:
                            self._temp_capture.release()
                        except Exception:
                            pass
                        self._temp_capture = None
                    else:
                        # set requested high-res capture dimensions if backend supports it
                        try:
                            self._temp_capture.set(cv2.CAP_PROP_FRAME_WIDTH, int(self.config.capture_frame_width))
                            self._temp_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, int(self.config.capture_frame_height))
                        except Exception:
                            pass
                except Exception:
                    self._temp_capture = None

            # If we have no separate temp capture, we will use the main capture for frames,
            # but we will still suppress showing those high-res frames in the GUI.
            # Mark suppression so _capture_next_frame won't push high-res frames to GUI.
            self._suppress_display_during_capture = True

            # Start capture sequence
            interval_ms = int(self.capture_settings.get('capture_interval_ms', 100))
            self._capture_timer.start(max(1, interval_ms))
            self.logger.info("Started capture sequence (averaging)")
            return True

        except Exception as e:
            self._handle_error(f"Capture trigger failed: {str(e)}")
            return False

    def _capture_next_frame(self):
        """Capture next frame in the averaging sequence (from temp_capture if exists, else main capture)"""
        source_cap = self._temp_capture if self._temp_capture is not None else self._capture

        # Stop if no source or completed requested number of frames
        if not source_cap or self._capture_frame_count >= int(self.config.capture_frames_for_averaging):
            try:
                self._capture_timer.stop()
            except Exception:
                pass
            self._finalize_capture()
            return

        ret, frame = source_cap.read()
        if not ret or frame is None:
            # don't kill the whole system for a single failed read; retry a few times could be added
            self._handle_error("Failed to capture frame for averaging")
            # continue - allow finalize to run if we've collected at least one frame
            try:
                self._capture_timer.stop()
            except Exception:
                pass
            self._finalize_capture()
            return

        # apply capture-specific flips if using temp capture
        try:
            if self._temp_capture is not None:
                if getattr(self.config, 'capture_flip_horizontal', False):
                    frame = cv2.flip(frame, 1)
                if getattr(self.config, 'capture_flip_vertical', False):
                    frame = cv2.flip(frame, 0)
        except Exception:
            pass

        # Apply general transformations (but do not change resolution here)
        processed_frame = self._apply_transformations(frame)

        # Store float32 copy for averaging to avoid overflow
        try:
            self._captured_frames.append(processed_frame.astype(np.float32))
        except Exception:
            # fallback: convert via np.array
            self._captured_frames.append(np.array(processed_frame, dtype=np.float32))

        self._capture_frame_count += 1

        # Emit progress
        try:
            self.capture_progress.emit(self._capture_frame_count, int(self.config.capture_frames_for_averaging))
        except Exception:
            pass

        # IMPORTANT: Do NOT update the GUI with high-res frames.
        # Keep showing the frozen low-res preview. Only change GUI when finalize completes.
        if not self._suppress_display_during_capture:
            # defensive: if suppression turned off unexpectedly, show the frame but scaled for display
            try:
                self._update_display(processed_frame)
            except Exception:
                pass

    def _finalize_capture(self):
        """Average the captured frames and prepare for analysis"""
        try:
            # Ensure suppression is off (we will update GUI now)
            self._suppress_display_during_capture = False

            if len(self._captured_frames) == 0:
                raise RuntimeError("No frames captured for averaging")

            # Calculate averaged frame safely (use float accumulator)
            # frames are float32 already; average then convert to uint8
            stacked = np.stack(self._captured_frames, axis=0)
            method = self.capture_settings.get('averaging_method', 'mean') if isinstance(self.capture_settings, dict) else 'mean'

            if method == 'median':
                averaged = np.median(stacked, axis=0).astype(np.uint8)
            else:
                averaged = np.mean(stacked, axis=0).round().astype(np.uint8)

            self._averaged_frame = averaged

            # Postprocessing if configured
            if self.capture_settings.get('preprocessing', {}).get('histogram_equalization', False):
                self._averaged_frame = self._apply_histogram_equalization(self._averaged_frame)

            if self.capture_settings.get('preprocessing', {}).get('noise_reduction', False):
                self._averaged_frame = self._apply_noise_reduction(self._averaged_frame)

            # Save averaged frame
            self._save_averaged_frame()

            # Update state and GUI
            self._state = CameraState.CAPTURED
            self.state_changed.emit(self._state)
            
            self.capture_complete.emit() 

            # Show averaged (high-res) result scaled/padded into the display area
            self._update_display(self._averaged_frame)

            self.logger.info(f"Captured and averaged {len(self._captured_frames)} frames")

        except Exception as e:
            self._handle_error(f"Frame averaging failed: {str(e)}")
        finally:
            # Release temp capture if used
            try:
                if self._temp_capture is not None:
                    try:
                        self._temp_capture.release()
                    except Exception:
                        pass
                    self._temp_capture = None
            except Exception:
                pass

            # clear captured frames buffer (we keep averaged_frame separately)
            try:
                self._captured_frames.clear()
            except Exception:
                pass

    def _apply_histogram_equalization(self, frame: np.ndarray) -> np.ndarray:
        """Apply histogram equalization to color image"""
        try:
            yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
            yuv[:, :, 0] = cv2.equalizeHist(yuv[:, :, 0])
            return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
        except Exception:
            return frame

    def _apply_noise_reduction(self, frame: np.ndarray) -> np.ndarray:
        """Apply gaussian blur as noise reduction"""
        kernel_size = int(self.capture_settings.get('preprocessing', {}).get('gaussian_blur_kernel', 3))
        if kernel_size % 2 == 0:
            kernel_size += 1
        try:
            return cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)
        except Exception:
            return frame

    def _save_averaged_frame(self):
        """Save the averaged frame to configured locations"""
        if self._averaged_frame is None:
            return
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"averaged_capture_{timestamp}.jpg"
            filepath = os.path.join(self.config.save_path, filename)
            cv2.imwrite(filepath, self._averaged_frame)

            # Also save to configs/averaged_capture.jpg for convenience (if folder exists)
            try:
                config_path = Path(__file__).resolve().parents[2] / "configs"
                os.makedirs(str(config_path), exist_ok=True)
                cv2.imwrite(str(config_path / "averaged_capture.jpg"), self._averaged_frame)
            except Exception:
                pass
        except Exception as e:
            self.logger.warning(f"Failed to save averaged frame: {e}")

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

            # Extract fields from algorithm output
            original_frame = result.get('original_frame', self._averaged_frame)
            processed_frame = result.get('processed_annotated', self._averaged_frame)
            status = result.get('status', {'status_code': 1, 'message': 'Unknown status'})
            results = result.get('results', {})

            overall_result = self._determine_overall_result(status, results)

            inspection_result = InspectionResult(
                original=original_frame,
                annotated=processed_frame,
                result=overall_result,
                status=status,
                results=results
            )

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

        for key, value in results.items():
            if isinstance(value, (int, float)) and value == 0:
                return "FAIL"
        return "PASS"

    def resume_streaming(self):
        """Resume live streaming after capture/analysis"""
        if self._state in [CameraState.CAPTURED, CameraState.ANALYZING, CameraState.FREEZING]:
            self._captured_frames.clear()
            self._averaged_frame = None
            self._state = CameraState.STREAMING
            self.state_changed.emit(self._state)
            self._timer.start()
            self.logger.info("Streaming resumed")

    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get current live frame copy"""
        return self._current_frame.copy() if self._current_frame is not None else None

    def get_averaged_frame(self) -> Optional[np.ndarray]:
        """Get the last averaged captured frame copy"""
        return self._averaged_frame.copy() if self._averaged_frame is not None else None

    def stop(self):
        """Stop camera and cleanup"""
        try:
            self._timer.stop()
        except Exception:
            pass
        try:
            self._capture_timer.stop()
        except Exception:
            pass
        try:
            if self._capture:
                self._capture.release()
        except Exception:
            pass
        try:
            if self._temp_capture:
                self._temp_capture.release()
        except Exception:
            pass

        self._capture = None
        self._temp_capture = None
        self._current_frame = None
        self._captured_frames.clear()
        self._averaged_frame = None
        self._state = CameraState.STOPPED
        self.state_changed.emit(self._state)
        self.logger.info("Camera stopped")

    def _read_frame(self):
        """Read and process camera frame for low-res live streaming"""
        if self._state != CameraState.STREAMING:
            return

        if self._simulation_mode:
            frame = self._create_simulation_frame()
        else:
            if not self._capture:
                return
            ret, frame = self._capture.read()
            if not ret or frame is None:
                self._handle_error("Failed to read frame from preview capture")
                return

        processed_frame = self._apply_transformations(frame)
        self._current_frame = processed_frame

        # Update GUI preview (low-res)
        self._update_display(processed_frame)

    def _apply_transformations(self, frame: np.ndarray) -> np.ndarray:
        """Apply flip and other transformations to frame"""
        try:
            # Work on a copy to avoid side-effects on callers
            out = frame
            if getattr(self.config, 'flip_horizontal', False):
                out = cv2.flip(out, 1)
            if getattr(self.config, 'flip_vertical', False):
                out = cv2.flip(out, 0)
            return out
        except Exception:
            return frame

    def _pad_frame_to_display_size(self, frame: np.ndarray) -> np.ndarray:
        """Pad frame to display size while maintaining aspect ratio"""
        target_width = int(self.config.frame_width)
        target_height = int(self.config.frame_height)

        try:
            original_height, original_width = frame.shape[:2]
            scale_w = target_width / original_width
            scale_h = target_height / original_height
            scale = min(scale_w, scale_h)
            new_width = max(1, int(original_width * scale))
            new_height = max(1, int(original_height * scale))
            resized_frame = cv2.resize(frame, (new_width, new_height))
            padded_frame = np.zeros((target_height, target_width, 3), dtype=np.uint8)
            y_offset = (target_height - new_height) // 2
            x_offset = (target_width - new_width) // 2
            padded_frame[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized_frame
            return padded_frame
        except Exception as e:
            self.logger.error(f"Frame padding failed: {str(e)}")
            try:
                return cv2.resize(frame, (target_width, target_height))
            except Exception:
                return frame

    def _update_display(self, frame: np.ndarray):
        """Update GUI display by emitting QImage (scaled/padded to display size)"""
        try:
            frame = self._pad_frame_to_display_size(frame)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            bytes_per_line = ch * w
            qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
            self.frame_ready.emit(qimg)
        except Exception as e:
            # Use current frame as fallback if possible
            self.logger.error(f"Display update failed: {str(e)}")
            # Do not call _handle_error here to avoid recursion

    def _create_message_frame(self, text: str, color=(255, 255, 255)) -> np.ndarray:
        frame = np.zeros((int(self.config.frame_height), int(self.config.frame_width), 3), dtype=np.uint8)
        text_color = tuple(self.display_settings.get('status_text_color', [255, 255, 255]))
        text_size = float(self.display_settings.get('status_text_size', 0.7))
        font = cv2.FONT_HERSHEY_SIMPLEX
        textsize = cv2.getTextSize(text, font, text_size, 2)[0]
        x = (int(self.config.frame_width) - textsize[0]) // 2
        y = (int(self.config.frame_height) + textsize[1]) // 2
        cv2.putText(frame, text, (x, y), font, text_size, text_color, 2)
        return frame

    def _create_simulation_frame(self) -> np.ndarray:
        import time, math
        frame = np.zeros((int(self.config.frame_height), int(self.config.frame_width), 3), dtype=np.uint8)
        for y in range(int(self.config.frame_height)):
            for x in range(int(self.config.frame_width)):
                frame[y, x] = [
                    int(50 + 50 * math.sin(x * 0.01)),
                    int(50 + 50 * math.sin(y * 0.01)),
                    int(100 + 50 * math.sin((x + y) * 0.005))
                ]
        t = time.time()
        center_x = int(self.config.frame_width / 2 + 100 * math.sin(t))
        center_y = int(self.config.frame_height / 2 + 50 * math.cos(t * 1.5))
        cv2.circle(frame, (center_x, center_y), 30, (255, 255, 255), -1)
        cv2.circle(frame, (center_x, center_y), 30, (0, 255, 0), 3)
        cv2.putText(frame, "SIMULATION MODE",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, f"Time: {int(t % 60)}s",
                    (10, int(self.config.frame_height) - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        return frame

    def _save_inspection_images(self, result: InspectionResult):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            orig_path = os.path.join(self.config.save_path, f"fail_{timestamp}_original.jpg")
            cv2.imwrite(orig_path, result.original)
            annot_path = os.path.join(self.config.save_path, f"fail_{timestamp}_annotated.jpg")
            cv2.imwrite(annot_path, result.annotated)
            json_path = os.path.join(self.config.save_path, f"fail_{timestamp}_results.json")
            with open(json_path, 'w') as f:
                json.dump({
                    'timestamp': timestamp,
                    'result': result.result,
                    'status': result.status,
                    'results': result.results
                }, f, indent=2)
            self.logger.info(f"Saved inspection images and results: {orig_path}, {annot_path}, {json_path}")
        except Exception as e:
            self.logger.warning(f"Failed to save inspection images: {e}")

    def _handle_error(self, message: str):
        """Handle errors uniformly"""
        self.logger.error(message)
        try:
            self.error_occurred.emit(message)
        except Exception:
            pass
        self._state = CameraState.ERROR
        try:
            self.state_changed.emit(self._state)
        except Exception:
            pass

        # Show an error/frozen frame if possible (use current preview frame)
        try:
            if self._current_frame is not None:
                self._update_display(self._current_frame)
        except Exception:
            pass
