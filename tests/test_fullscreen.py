#!/usr/bin/env python3
"""
Test script to verify fullscreen functionality on Raspberry Pi
"""

import sys
import os
sys.path.insert(0, '/home/taisys/Desktop/AI_inspection_system/src')

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import Qt
from ui.screen_utils import apply_fullscreen_to_window, screen_manager


class FullscreenTestWindow(QMainWindow):
    """Test window to verify fullscreen functionality"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the test interface"""
        self.setWindowTitle("Fullscreen Test - AI Inspection System")
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Add test content
        title_label = QLabel("🖥️ FULLSCREEN TEST")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 48px; font-weight: bold; color: #2196F3; margin: 20px;")
        layout.addWidget(title_label)
        
        # Screen info
        if screen_manager.screen_info:
            info_text = f"""
Screen Resolution: {screen_manager.screen_info['total_width']} x {screen_manager.screen_info['total_height']}
Available Space: {screen_manager.screen_info['available_width']} x {screen_manager.screen_info['available_height']}
Platform: {'Raspberry Pi' if screen_manager.is_raspberry_pi else 'Desktop'}
            """
        else:
            info_text = "Screen info not available"
        
        info_label = QLabel(info_text)
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-size: 24px; margin: 20px; background-color: #f0f0f0; padding: 20px; border-radius: 10px;")
        layout.addWidget(info_label)
        
        # Test status
        status_label = QLabel("✅ Fullscreen Mode Active\n\nIf you can see this message clearly\nwithout cropping, the fix is working!")
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet("font-size: 20px; color: #4CAF50; margin: 20px; background-color: #e8f5e8; padding: 20px; border-radius: 10px;")
        layout.addWidget(status_label)
        
        # Close button
        close_btn = QPushButton("Close Test")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 18px;
                font-weight: bold;
                border-radius: 10px;
                margin: 20px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        
        # Apply fullscreen using our utility
        apply_fullscreen_to_window(self)
        
        print("🚀 Test window created - applying fullscreen mode")


def main():
    """Run the fullscreen test"""
    print("🔍 Starting Fullscreen Test...")
    print("=" * 50)
    
    app = QApplication(sys.argv)
    
    # Create and show test window
    window = FullscreenTestWindow()
    window.show()
    
    print("📱 Test window displayed")
    print("💡 Check if the window displays properly without cropping")
    print("💡 Press 'Close Test' button or Ctrl+C to exit")
    
    # Run the application
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
        app.quit()


if __name__ == "__main__":
    main()