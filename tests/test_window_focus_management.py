#!/usr/bin/env python3
"""Test window focus management between main window and inspection windows."""

import sys
import os
sys.path.append('/home/taisys/Desktop/AI_inspection_system')
sys.path.append('/home/taisys/Desktop/AI_inspection_system/src')

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMainWindow
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

class MockInspectionWindow(QWidget):
    """Mock inspection window to test focus management"""
    
    window_closed = pyqtSignal()
    
    def __init__(self, inspection_type):
        super().__init__()
        self.inspection_type = inspection_type
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle(f"{self.inspection_type} Inspection Window")
        self.setGeometry(200, 200, 800, 600)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title
        title = QLabel(f"{self.inspection_type} Inspection")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; margin: 30px;")
        layout.addWidget(title)
        
        # Status
        status = QLabel("This window should come to foreground when opened\nfrom the main window inspection buttons.")
        status.setAlignment(Qt.AlignCenter)
        status.setStyleSheet("color: #666; font-size: 16px; margin: 20px;")
        layout.addWidget(status)
        
        # Main Menu button
        main_menu_button = QPushButton("Main Menu")
        main_menu_button.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px 30px;
                border-radius: 8px;
                margin: 20px;
            }
            QPushButton:hover {
                background-color: #455A64;
            }
        """)
        main_menu_button.clicked.connect(self.back_to_main)
        layout.addWidget(main_menu_button)
        
        # Instructions
        instructions = QLabel("Click 'Main Menu' to test automatic\nfocus return to the main window.")
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setStyleSheet("color: #999; font-size: 14px; margin: 20px; font-style: italic;")
        layout.addWidget(instructions)
        
        self.setStyleSheet("background-color: #f0f0f0;")
    
    def back_to_main(self):
        """Return to main window"""
        print(f"🏠 {self.inspection_type}: Returning to main menu...")
        self.window_closed.emit()
        self.close()
    
    def show(self):
        """Override show to ensure foreground focus"""
        super().show()
        self.raise_()
        self.activateWindow()
        QTimer.singleShot(100, self.ensure_foreground)
        print(f"📱 {self.inspection_type} window shown and brought to foreground")
    
    def ensure_foreground(self):
        """Ensure window stays in foreground"""
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.raise_()
        self.activateWindow()
        print(f"   🎯 {self.inspection_type} window focus ensured")

class TestMainWindow(QMainWindow):
    """Test main window with focus management"""
    
    def __init__(self):
        super().__init__()
        self.eolt_window = None
        self.inline_window = None
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("AI Inspection System - Focus Test")
        self.setGeometry(100, 100, 1000, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Title
        title = QLabel("Window Focus Management Test")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; margin: 30px;")
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("""
🎯 Test Focus Management:

1. Click 'Inspect EOLT' or 'Inspect INLINE' buttons
   → Inspection window should come to FOREGROUND automatically

2. In the inspection window, click 'Main Menu' button  
   → Main window should come to FOREGROUND automatically

3. Test multiple times to verify consistent behavior

✅ Expected Behavior:
• Inspection buttons → Inspection window foreground
• Main Menu button → Main window foreground
• No need to manually click or Alt-Tab between windows
        """)
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setStyleSheet("color: #666; font-size: 14px; margin: 20px; background-color: #f8f9fa; padding: 20px; border-radius: 8px;")
        layout.addWidget(instructions)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        # EOLT button
        eolt_button = QPushButton("Inspect EOLT")
        eolt_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 20px 40px;
                border-radius: 10px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        eolt_button.clicked.connect(self.open_eolt)
        buttons_layout.addWidget(eolt_button)
        
        # INLINE button
        inline_button = QPushButton("Inspect INLINE")
        inline_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 20px 40px;
                border-radius: 10px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        inline_button.clicked.connect(self.open_inline)
        buttons_layout.addWidget(inline_button)
        
        layout.addLayout(buttons_layout)
        
        # Status
        self.status_label = QLabel("Main window ready - Click inspection buttons to test focus management")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #27ae60; font-size: 16px; font-weight: bold; margin: 20px;")
        layout.addWidget(self.status_label)
        
        self.setStyleSheet("background-color: #ffffff;")
    
    def open_eolt(self):
        """Open EOLT inspection window"""
        print("🔍 Opening EOLT inspection window...")
        
        # Close any existing inspection windows
        if self.inline_window:
            self.inline_window.close()
            self.inline_window = None
        
        # Create and show EOLT window
        self.eolt_window = MockInspectionWindow("EOLT")
        self.eolt_window.window_closed.connect(self.restore_main_window)
        
        # Hide main window and show inspection window
        self.hide()
        self.eolt_window.show()
        
        self.status_label.setText("EOLT inspection window opened - should be in FOREGROUND")
        print("✅ EOLT window created and should be in foreground")
    
    def open_inline(self):
        """Open INLINE inspection window"""
        print("🔍 Opening INLINE inspection window...")
        
        # Close any existing inspection windows
        if self.eolt_window:
            self.eolt_window.close()
            self.eolt_window = None
        
        # Create and show INLINE window
        self.inline_window = MockInspectionWindow("INLINE")
        self.inline_window.window_closed.connect(self.restore_main_window)
        
        # Hide main window and show inspection window
        self.hide()
        self.inline_window.show()
        
        self.status_label.setText("INLINE inspection window opened - should be in FOREGROUND")
        print("✅ INLINE window created and should be in foreground")
    
    def restore_main_window(self):
        """Restore main window to foreground"""
        print("🔄 Restoring main window to foreground...")
        
        # Clear window references
        if self.eolt_window:
            self.eolt_window = None
        if self.inline_window:
            self.inline_window = None
        
        # Show and bring main window to foreground
        self.show()
        self.raise_()
        self.activateWindow()
        
        # Extra focus management for reliability
        QTimer.singleShot(50, self.force_main_focus)
        
        self.status_label.setText("✅ Main window restored to FOREGROUND - test successful!")
        print("✅ Main window should now be in foreground")
    
    def force_main_focus(self):
        """Force main window focus"""
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.raise_()
        self.activateWindow()
        print("   🎯 Main window focus forced")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TestMainWindow()
    window.show()
    
    print("🧪 Window Focus Management Test Started")
    print("📋 Test procedure:")
    print("   1. Click 'Inspect EOLT' → EOLT window should come to foreground")
    print("   2. Click 'Main Menu' in EOLT window → Main window should come to foreground")
    print("   3. Click 'Inspect INLINE' → INLINE window should come to foreground")
    print("   4. Click 'Main Menu' in INLINE window → Main window should come to foreground")
    print("\n🎯 Success criteria: All window transitions happen automatically without manual focus switching")
    
    sys.exit(app.exec_())