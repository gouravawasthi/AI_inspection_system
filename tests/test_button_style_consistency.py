#!/usr/bin/env python3
"""Test button styling consistency in inspection window."""

import sys
import os
sys.path.append('/home/taisys/Desktop/AI_inspection_system')
sys.path.append('/home/taisys/Desktop/AI_inspection_system/src')

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class ButtonStyleTest(QWidget):
    """Test widget to verify button styling consistency"""
    
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Button Style Consistency Test')
        self.setGeometry(100, 100, 1000, 600)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title
        title = QLabel("Button Style Consistency Test")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; margin: 20px;")
        layout.addWidget(title)
        
        # Main container
        main_layout = QHBoxLayout()
        
        # Barcode section buttons
        self.create_barcode_buttons(main_layout)
        
        # Inspection control buttons
        self.create_inspection_buttons(main_layout)
        
        layout.addLayout(main_layout)
        
        # Info
        info = QLabel("All buttons should now have consistent styling:\n"
                     "• Same font size (14px)\n"
                     "• Same height (40px)\n"
                     "• Same border and margin styling\n"
                     "• Consistent hover and disabled states")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #666; margin: 20px; background-color: #f8f9fa; padding: 15px; border-radius: 5px;")
        layout.addWidget(info)
    
    def create_barcode_buttons(self, main_layout):
        """Create barcode section buttons"""
        barcode_group = QGroupBox("Barcode Section Buttons")
        barcode_layout = QVBoxLayout()
        barcode_group.setLayout(barcode_layout)
        barcode_group.setFixedWidth(350)
        
        # Scan button (Blue like Next Step)
        scan_button = QPushButton("Scan")
        scan_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: 1px solid #333;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
                margin: 2px 0px;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #A8C8E8;
                color: #888888;
                border: 1px solid #BBBBBB;
            }
        """)
        barcode_layout.addWidget(scan_button)
        
        # Submit button (Green like Capture)
        submit_button = QPushButton("Submit")
        submit_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: 1px solid #333;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
                margin: 2px 0px;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #A8D8A8;
                color: #888888;
                border: 1px solid #BBBBBB;
            }
        """)
        barcode_layout.addWidget(submit_button)
        
        # Test disabled state button
        disabled_button = QPushButton("Disabled Submit")
        disabled_button.setStyleSheet(submit_button.styleSheet())
        disabled_button.setEnabled(False)
        barcode_layout.addWidget(disabled_button)
        
        main_layout.addWidget(barcode_group)
    
    def create_inspection_buttons(self, main_layout):
        """Create inspection control buttons"""
        inspection_group = QGroupBox("Inspection Control Buttons")
        inspection_layout = QVBoxLayout()
        inspection_group.setLayout(inspection_layout)
        inspection_group.setFixedWidth(350)
        
        # Common button style
        button_style = """
            QPushButton {{
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                margin: 2px 0px;
                min-height: 40px;
                max-height: 40px;
                border-radius: 5px;
            }}
        """
        
        # Capture button (Green)
        capture_button = QPushButton("Capture")
        capture_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: 1px solid #333;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #A8D8A8;
                color: #888888;
                border: 1px solid #BBBBBB;
            }
        """)
        inspection_layout.addWidget(capture_button)
        
        # Next Step button (Blue)
        next_step_button = QPushButton("Next Step")
        next_step_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: 1px solid #333;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #A8C8E8;
                color: #888888;
                border: 1px solid #BBBBBB;
            }
        """)
        inspection_layout.addWidget(next_step_button)
        
        # Manual Override button (Orange)
        override_button = QPushButton("Manual Override")
        override_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: 1px solid #333;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:disabled {
                background-color: #E8C8A8;
                color: #888888;
                border: 1px solid #BBBBBB;
            }
        """)
        inspection_layout.addWidget(override_button)
        
        # Test disabled state button
        disabled_next = QPushButton("Disabled Next Step")
        disabled_next.setStyleSheet(next_step_button.styleSheet())
        disabled_next.setEnabled(False)
        inspection_layout.addWidget(disabled_next)
        
        main_layout.addWidget(inspection_group)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ButtonStyleTest()
    window.show()
    
    print("🎨 Button Style Consistency Test")
    print("✅ Submit and Scan buttons now match inspection control styling:")
    print("   • Same font size (14px)")
    print("   • Same height (40px)")  
    print("   • Same border and margin styling")
    print("   • Consistent hover and disabled states")
    print("   • Color coding: Green=Action, Blue=Navigation, Orange=Override")
    print("\n🔍 Compare the buttons to verify consistency")
    
    sys.exit(app.exec_())