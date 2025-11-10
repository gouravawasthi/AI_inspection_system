#!/usr/bin/env python3
"""Simple test for button layout without full configuration."""

import sys
sys.path.append('/home/taisys/Desktop/AI_inspection_system')

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class SimpleButtonTest(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Button Layout Test')
        self.setGeometry(100, 100, 400, 600)
        
        layout = QVBoxLayout()
        
        # Test the buttons with same styling as in base_inspection_window.py
        buttons_data = [
            ("Capture", "capture", "#4CAF50"),
            ("Skip Step", "skip_step", "#2196F3"),
            ("Previous Step", "previous_step", "#2196F3"),
            ("Next Step", "next_step", "#2196F3"),
            ("Repeat Step", "repeat_step", "#2196F3"),
            ("Manual Override", "manual_override", "#FF9800"),
            ("Stop Test", "stop_test", "#f44336"),
            ("Main Menu", "back_to_main", "#9E9E9E"),
            ("Quit Application", "quit_app", "#8B0000")
        ]
        
        for text, object_name, color in buttons_data:
            btn = QPushButton(text)
            btn.setObjectName(object_name)
            
            # Apply the exact styling from base_inspection_window.py
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: 1px solid #333;
                    padding: 8px 16px;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 4px;
                    margin: 2px 0px;
                    min-height: 40px;
                }}
                QPushButton:hover {{
                    background-color: {color}CC;
                }}
                QPushButton:pressed {{
                    background-color: {color}99;
                }}
            """)
            
            layout.addWidget(btn)
            print(f"Button '{text}': Height={btn.minimumSizeHint().height()}, Font Size=14px")
        
        self.setLayout(layout)
        print("\nButton Layout Test Created Successfully!")
        print("All buttons should have:")
        print("- Equal height (40px minimum)")
        print("- Same font size (14px)")
        print("- Consistent margins (2px 0px)")
        print("- Renamed labels: 'Capture' and 'Main Menu'")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SimpleButtonTest()
    window.show()
    
    print("\nTest window opened. Check button appearance and sizing.")
    print("Close the window to exit.")
    
    sys.exit(app.exec_())