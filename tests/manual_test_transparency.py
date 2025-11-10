#!/usr/bin/env python3
"""
Quick test to verify main window clicking behavior
Run this and try clicking on the main window to see if transparency occurs
"""

import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

def main():
    """Create and show main window for manual testing"""
    print("🧪 Manual Test: Main Window Click Behavior")
    print("=" * 50)
    print("📝 Instructions:")
    print("1. Main window will appear")
    print("2. Click anywhere on the main window")
    print("3. Check if background becomes transparent")
    print("4. Press Ctrl+C to exit")
    print("=" * 50)
    
    # Create QApplication
    app = QApplication(['manual_test'])
    
    try:
        from ui.mainwindow import MainWindow
        
        # Create main window
        main_window = MainWindow()
        main_window.show()
        
        print("✅ Main window displayed")
        print("🖱️  Try clicking on the main window...")
        print("💡 If background stays solid, transparency issue is fixed!")
        
        # Run the application
        app.exec_()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == '__main__':
    main()