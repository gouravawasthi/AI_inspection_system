#!/usr/bin/env python3
"""
Debug Video Streaming Issues
Check if frames are being generated and signals are working
"""

import sys
import os
import logging
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from camera.camera_manager import CameraManager, CameraState
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_camera_signals():
    """Test if camera manager is properly emitting signals"""
    
    app = QApplication(sys.argv)
    
    print("🔧 Debug: Testing Camera Manager Signals")
    print("=" * 50)
    
    # Create camera manager
    camera = CameraManager()
    
    # Connect debug handlers
    def on_frame_ready(qimage):
        print(f"📸 DEBUG: Frame ready signal received! Image size: {qimage.width()}x{qimage.height()}")
    
    def on_state_changed(state):
        print(f"🔄 DEBUG: State changed to: {state}")
    
    def on_error(msg):
        print(f"❌ DEBUG: Error occurred: {msg}")
    
    camera.frame_ready.connect(on_frame_ready)
    camera.state_changed.connect(on_state_changed)
    camera.error_occurred.connect(on_error)
    
    # Start streaming
    print("🚀 Starting camera streaming...")
    success = camera.start_streaming()
    print(f"✅ Streaming started: {success}")
    
    # Set timer to stop after 10 seconds
    def stop_test():
        print("🛑 Stopping test...")
        camera.stop()
        app.quit()
    
    QTimer.singleShot(10000, stop_test)  # Stop after 10 seconds
    
    print("⏱️ Running for 10 seconds to check for frame signals...")
    return app.exec_()

if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parent)
    exit(test_camera_signals())