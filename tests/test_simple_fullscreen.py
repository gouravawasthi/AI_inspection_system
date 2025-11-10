#!/usr/bin/env python3
"""
Simple fullscreen test for Raspberry Pi
Tests the screen_utils functionality independently
"""

import sys
import os

# Add the UI directory to the path
sys.path.insert(0, '/home/taisys/Desktop/AI_inspection_system/src/ui')

try:
    from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
    from PyQt5.QtCore import Qt
    from screen_utils import apply_fullscreen_to_window, screen_manager
    
    class SimpleFullscreenTest(QMainWindow):
        """Simple test window for fullscreen functionality"""
        
        def __init__(self):
            super().__init__()
            self.init_ui()
        
        def init_ui(self):
            """Initialize the test interface"""
            self.setWindowTitle("Simple Fullscreen Test")
            
            # Create central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Create layout
            layout = QVBoxLayout()
            central_widget.setLayout(layout)
            
            # Add test content
            title_label = QLabel("🖥️ FULLSCREEN TEST")
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setStyleSheet("font-size: 36px; font-weight: bold; color: #2196F3; margin: 20px;")
            layout.addWidget(title_label)
            
            # Screen info
            if screen_manager.screen_info:
                info_text = f"""Screen: {screen_manager.screen_info['total_width']} x {screen_manager.screen_info['total_height']}
Available: {screen_manager.screen_info['available_width']} x {screen_manager.screen_info['available_height']}
Raspberry Pi: {'Yes' if screen_manager.is_raspberry_pi else 'No'}
Display: {screen_manager.display_server}"""
            else:
                info_text = "Screen info not available"
            
            info_label = QLabel(info_text)
            info_label.setAlignment(Qt.AlignCenter)
            info_label.setStyleSheet("font-size: 18px; margin: 20px; background-color: #f0f0f0; padding: 20px; border-radius: 10px;")
            layout.addWidget(info_label)
            
            # Test status
            status_label = QLabel("✅ If you can see all corners of this window\nwithout any cropping, the fullscreen fix is working!")
            status_label.setAlignment(Qt.AlignCenter)
            status_label.setStyleSheet("font-size: 16px; color: #4CAF50; margin: 20px; background-color: #e8f5e8; padding: 20px; border-radius: 10px;")
            layout.addWidget(status_label)
            
            # Instructions
            instructions = QLabel("Press ESC or click Close to exit")
            instructions.setAlignment(Qt.AlignCenter)
            instructions.setStyleSheet("font-size: 14px; color: #666; margin: 10px;")
            layout.addWidget(instructions)
            
            # Close button
            close_btn = QPushButton("Close Test")
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 8px;
                    margin: 10px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            close_btn.clicked.connect(self.close)
            layout.addWidget(close_btn, alignment=Qt.AlignCenter)
            
            # Apply fullscreen using our utility
            print("🚀 Applying fullscreen mode...")
            apply_fullscreen_to_window(self)
            
        def keyPressEvent(self, event):
            """Handle ESC key to close"""
            if event.key() == Qt.Key_Escape:
                self.close()
    
    def main():
        """Run the simple fullscreen test"""
        print("🔍 Simple Fullscreen Test for Raspberry Pi")
        print("=" * 45)
        
        app = QApplication(sys.argv)
        
        # Create and show test window
        window = SimpleFullscreenTest()
        window.show()
        
        print("📱 Test window displayed")
        print("💡 Check if the window fills the entire screen properly")
        print("💡 Press ESC or click 'Close Test' to exit")
        
        # Run the application
        try:
            sys.exit(app.exec_())
        except KeyboardInterrupt:
            print("\n👋 Test interrupted by user")
            app.quit()

    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure PyQt5 is installed: pip install PyQt5")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)