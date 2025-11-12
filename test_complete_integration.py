#!/usr/bin/env python3
"""
Complete Camera UI Integration Test
Demonstrates the full camera integration workflow with UI
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer

# Add the src directory to Python path  
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from ui.inline_inspection_window import INLINEInspectionWindow
from ui.eolt_inspection_window import EOLTInspectionWindow


class CameraIntegrationDemo:
    """Demo class to showcase camera integration features"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
    def run_inline_demo(self):
        """Run INLINE inspection demo with video streaming"""
        print("🔬 INLINE Inspection Camera Demo")
        print("=" * 50)
        
        self.window = INLINEInspectionWindow()
        self.window.show()
        
        # Auto-demo sequence
        QTimer.singleShot(1000, self._demo_barcode_entry)
        
        return self.app.exec_()
        
    def run_eolt_demo(self):
        """Run EOLT inspection demo with video streaming"""
        print("🔌 EOLT Inspection Camera Demo") 
        print("=" * 50)
        
        self.window = EOLTInspectionWindow()
        self.window.show()
        
        # Auto-demo sequence
        QTimer.singleShot(1000, self._demo_barcode_entry)
        
        return self.app.exec_()
    
    def _demo_barcode_entry(self):
        """Simulate barcode entry to trigger video streaming"""
        if not self.window:
            return
            
        print("📱 Auto-entering demo barcode...")
        
        # Set barcode in the input field
        self.window.barcode_input.setText("DEMO123456")
        
        # Trigger barcode submission after a delay
        QTimer.singleShot(500, self._submit_barcode)
    
    def _submit_barcode(self):
        """Submit the barcode to start video streaming"""
        if not self.window:
            return
            
        print("✅ Submitting barcode - Video streaming should start...")
        
        # Simulate clicking submit button
        self.window.submit_barcode()
        
        # Show capture demo after delay
        QTimer.singleShot(3000, self._demo_capture)
    
    def _demo_capture(self):
        """Demonstrate capture functionality"""
        if not self.window:
            return
            
        print("📸 Demo capture - Click the Capture button to test frame averaging...")
        
        # Show instruction dialog
        msg = QMessageBox(self.window)
        msg.setWindowTitle("Camera Integration Demo")
        msg.setText(
            "🎥 Video Streaming Active!\n\n"
            "What you should see:\n"
            "✅ Live video feed in camera panel\n" 
            "✅ Camera status showing 'Live Streaming'\n"
            "✅ Capture button enabled\n\n"
            "Demo Features:\n"
            "• Simulation mode with moving patterns\n"
            "• Real-time video display\n" 
            "• Frame averaging on capture\n"
            "• Algorithm processing integration\n\n"
            "Click 'Capture' to test the complete workflow!"
        )
        msg.setIcon(QMessageBox.Information)
        msg.exec_()


def main():
    """Main entry point for the demo"""
    os.chdir(Path(__file__).resolve().parent)
    
    demo = CameraIntegrationDemo()
    
    if len(sys.argv) > 1 and sys.argv[1] == "eolt":
        return demo.run_eolt_demo()
    else:
        return demo.run_inline_demo()


if __name__ == "__main__":
    print("🚀 Camera Integration Demo")
    print("Usage:")
    print("  python test_complete_integration.py        # INLINE demo")
    print("  python test_complete_integration.py eolt   # EOLT demo")
    print("\n🎬 Starting demo...")
    
    exit(main())