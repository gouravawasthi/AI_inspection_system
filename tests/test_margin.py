#!/usr/bin/env python3
"""
Test the 5% bottom margin functionality
"""

import sys
import os

# Add the UI directory to the path
sys.path.insert(0, '/home/taisys/Desktop/AI_inspection_system/src/ui')

try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                                QWidget, QPushButton, QFrame)
    from PyQt5.QtCore import Qt
    from screen_utils import apply_fullscreen_to_window, screen_manager
    
    class MarginTestWindow(QMainWindow):
        """Test window for 5% bottom margin"""
        
        def __init__(self):
            super().__init__()
            self.init_ui()
        
        def init_ui(self):
            """Initialize the test interface"""
            self.setWindowTitle("5% Bottom Margin Test")
            
            # Create central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Create layout
            layout = QVBoxLayout()
            central_widget.setLayout(layout)
            
            # Title
            title_label = QLabel("🖥️ 5% BOTTOM MARGIN TEST")
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #2196F3; margin: 10px; background-color: #e3f2fd; padding: 15px; border-radius: 10px;")
            layout.addWidget(title_label)
            
            # Screen info
            if screen_manager.screen_info:
                total_height = screen_manager.screen_info['total_height']
                margin_height = int(total_height * 0.05)
                usable_height = total_height - margin_height
                
                info_text = f"""
📏 SCREEN DIMENSIONS:
Total Screen Height: {total_height}px
5% Margin Height: {margin_height}px
Usable Window Height: {usable_height}px
Window Width: {screen_manager.screen_info['total_width']}px

✅ EXPECTED RESULT:
• Window should fill the screen width completely
• Window should NOT reach the bottom edge
• There should be {margin_height}px of empty space at the bottom
• You should be able to see the desktop/taskbar below this window
                """
            else:
                info_text = "Screen info not available"
            
            info_label = QLabel(info_text.strip())
            info_label.setAlignment(Qt.AlignLeft)
            info_label.setStyleSheet("font-size: 14px; margin: 15px; background-color: #f0f0f0; padding: 15px; border-radius: 8px; font-family: monospace;")
            layout.addWidget(info_label)
            
            # Visual indicator at bottom
            bottom_frame = QFrame()
            bottom_frame.setFixedHeight(80)
            bottom_frame.setStyleSheet("""
                QFrame {
                    background-color: #ff5722;
                    border: 3px solid #d32f2f;
                    border-radius: 10px;
                    margin: 10px;
                }
            """)
            
            bottom_layout = QVBoxLayout()
            bottom_frame.setLayout(bottom_layout)
            
            bottom_label = QLabel("⬇️ BOTTOM OF WINDOW ⬇️")
            bottom_label.setAlignment(Qt.AlignCenter)
            bottom_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; background: transparent; border: none; margin: 0;")
            bottom_layout.addWidget(bottom_label)
            
            instruction_label = QLabel("If you can see desktop/taskbar below this, margin is working!")
            instruction_label.setAlignment(Qt.AlignCenter)
            instruction_label.setStyleSheet("color: white; font-size: 12px; background: transparent; border: none; margin: 0;")
            bottom_layout.addWidget(instruction_label)
            
            layout.addWidget(bottom_frame)
            
            # Close button
            close_btn = QPushButton("Close Test")
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 8px;
                    margin: 15px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            close_btn.clicked.connect(self.close)
            layout.addWidget(close_btn, alignment=Qt.AlignCenter)
            
            # Apply fullscreen with 5% bottom margin
            print("🚀 Applying fullscreen with 5% bottom margin...")
            apply_fullscreen_to_window(self, bottom_margin_percent=5)
        
        def keyPressEvent(self, event):
            """Handle ESC key to close"""
            if event.key() == Qt.Key_Escape:
                self.close()
    
    def main():
        """Run the margin test"""
        print("🔍 Testing 5% Bottom Margin")
        print("=" * 40)
        
        app = QApplication(sys.argv)
        
        # Create and show test window
        window = MarginTestWindow()
        window.show()
        
        print("📱 Margin test window displayed")
        print("💡 Check if:")
        print("   - Window fills full width")
        print("   - 5% empty space at bottom")
        print("   - Desktop/taskbar visible below")
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
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)