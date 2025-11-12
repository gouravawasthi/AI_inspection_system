#!/usr/bin/env python3
"""
Test Video Streaming in UI
Tests the complete video streaming workflow in the inspection UI
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from PyQt5.QtWidgets import QApplication
from ui.inline_inspection_window import INLINEInspectionWindow


def test_video_streaming():
    """Test video streaming in INLINE inspection window"""
    
    app = QApplication(sys.argv)
    
    # Create inspection window
    window = INLINEInspectionWindow()
    
    # Show window
    window.show()
    
    print("🎥 Video Streaming Test")
    print("=" * 50)
    print("1. Window should display with camera panel")
    print("2. Enter a test barcode (e.g., 'TEST123')")
    print("3. Video streaming should start automatically")
    print("4. Camera status should show 'Live Streaming'")
    print("5. Live video feed should appear in camera panel")
    print("\n💡 Note: If no camera is connected, you'll see error messages")
    print("   but the UI framework should still work correctly.")
    print("\n🛑 Close window to exit test")
    
    # Run the application
    return app.exec_()


if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parent)
    exit(test_video_streaming())