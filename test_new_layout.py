#!/usr/bin/env python3
"""
Test the new vertical camera layout
Live video on top, algorithm results below
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from ui.inline_inspection_window import INLINEInspectionWindow

def test_new_layout():
    """Test the new vertical camera layout"""
    
    app = QApplication(sys.argv)
    
    # Create inspection window
    window = INLINEInspectionWindow()
    window.show()
    
    print("📹 New Camera Layout Test")
    print("=" * 50)
    print("✅ Features to verify:")
    print("   📺 Live video streaming starts immediately")
    print("   🎥 Video appears in upper section")
    print("   📊 Result area in lower section (initially black)")
    print("   🔄 No barcode required for streaming")
    print("\n💡 The camera should start streaming as soon as the window opens!")
    print("🛑 Close window to exit test")
    
    return app.exec_()

if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parent)
    exit(test_new_layout())