#!/usr/bin/env python3
"""
Test Camera Streaming in Main Application
Automates the camera streaming workflow
"""

import sys
import os
import logging
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from ui.inline_inspection_window import INLINEInspectionWindow

# Enable debug logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class CameraStreamingTest:
    """Automated test for camera streaming in the inspection window"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
    def run_test(self):
        """Run the automated camera streaming test"""
        print("🎥 Camera Streaming Test in Main Application")
        print("=" * 60)
        
        # Create inspection window
        self.window = INLINEInspectionWindow()
        self.window.show()
        
        # Add debug logging to the camera update method
        original_update_video_frame = self.window.update_video_frame
        def debug_update_video_frame(qimage):
            print(f"📸 UI received frame: {qimage.width()}x{qimage.height()}")
            return original_update_video_frame(qimage)
        self.window.update_video_frame = debug_update_video_frame
        
        # Start automated workflow
        print("⏱️ Starting automated workflow in 2 seconds...")
        QTimer.singleShot(2000, self.auto_enter_barcode)
        
        return self.app.exec_()
    
    def auto_enter_barcode(self):
        """Automatically enter a test barcode"""
        print("📱 Entering test barcode: TEST123...")
        
        # Set barcode in input field
        self.window.barcode_input.setText("TEST123")
        
        # Submit barcode after a short delay
        QTimer.singleShot(500, self.submit_barcode)
    
    def submit_barcode(self):
        """Submit the barcode to start streaming"""
        print("✅ Submitting barcode - Camera streaming should start...")
        
        # Submit the barcode
        self.window.submit_barcode()
        
        # Check camera status after 3 seconds
        QTimer.singleShot(3000, self.check_streaming_status)
    
    def check_streaming_status(self):
        """Check if streaming is working"""
        print("🔍 Checking camera streaming status...")
        
        # Check camera integrator state
        if hasattr(self.window, 'camera_integrator'):
            state = self.window.camera_integrator.get_camera_state()
            print(f"📊 Camera state: {state}")
            
            ready = self.window.camera_integrator.is_ready_for_capture()
            print(f"📸 Ready for capture: {ready}")
            
            if ready:
                print("✅ Camera streaming is working! Video should be visible.")
                print("💡 Look for animated simulation frames in the camera panel.")
            else:
                print("⚠️ Camera not ready - check for errors.")
        
        # Show instructions
        print("\n" + "=" * 60)
        print("🎬 STREAMING TEST RESULTS:")
        print("✅ If you see animated simulation frames: SUCCESS!")
        print("⚠️ If camera panel shows text only: Need to debug")
        print("📹 Expected: Moving patterns with timestamp")
        print("🛑 Close window to end test")


def main():
    """Run the camera streaming test"""
    os.chdir(Path(__file__).resolve().parent)
    
    test = CameraStreamingTest()
    return test.run_test()


if __name__ == "__main__":
    exit(main())