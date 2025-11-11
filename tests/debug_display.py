#!/usr/bin/env python3
"""
Display debug tool for Raspberry Pi fullscreen issues
Helps identify and fix specific display problems
"""

import sys
import os

# Add the UI directory to the path
sys.path.insert(0, '/home/taisys/Desktop/AI_inspection_system/src/ui')

try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                                QWidget, QPushButton, QHBoxLayout, QFrame, QTextEdit)
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QFont, QPalette
    from screen_utils import screen_manager, apply_fullscreen_to_window, force_fullscreen_refresh
    
    class DisplayDebugWindow(QMainWindow):
        """Debug window to identify display issues"""
        
        def __init__(self):
            super().__init__()
            self.init_ui()
            self.setup_timers()
        
        def init_ui(self):
            """Initialize the debug interface"""
            self.setWindowTitle("Display Debug Tool - Raspberry Pi")
            
            # Create central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Create main layout
            main_layout = QVBoxLayout()
            central_widget.setLayout(main_layout)
            
            # Title
            title_label = QLabel("🔍 DISPLAY DEBUG TOOL")
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #2196F3; margin: 10px; background-color: yellow; padding: 10px;")
            main_layout.addWidget(title_label)
            
            # Screen corners test
            self.create_corner_markers(main_layout)
            
            # System info
            self.create_system_info(main_layout)
            
            # Window geometry info
            self.geometry_info = QTextEdit()
            self.geometry_info.setMaximumHeight(120)
            self.geometry_info.setStyleSheet("font-family: monospace; font-size: 12px; background-color: #f0f0f0;")
            main_layout.addWidget(self.geometry_info)
            
            # Control buttons
            self.create_control_buttons(main_layout)
            
            # Apply fullscreen
            print("🚀 Applying fullscreen to debug window...")
            apply_fullscreen_to_window(self)
            
        def create_corner_markers(self, layout):
            """Create corner markers to test screen coverage"""
            # Corner frame
            corner_frame = QFrame()
            corner_frame.setFixedHeight(200)
            corner_frame.setStyleSheet("""
                QFrame {
                    border: 5px solid red;
                    background-color: rgba(255, 0, 0, 0.1);
                }
            """)
            
            corner_layout = QVBoxLayout()
            corner_frame.setLayout(corner_layout)
            
            # Top row
            top_layout = QHBoxLayout()
            
            top_left = QLabel("TOP-LEFT CORNER")
            top_left.setStyleSheet("background-color: red; color: white; padding: 10px; font-weight: bold;")
            top_left.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            
            top_right = QLabel("TOP-RIGHT CORNER")
            top_right.setStyleSheet("background-color: red; color: white; padding: 10px; font-weight: bold;")
            top_right.setAlignment(Qt.AlignRight | Qt.AlignTop)
            
            top_layout.addWidget(top_left)
            top_layout.addStretch()
            top_layout.addWidget(top_right)
            
            # Bottom row
            bottom_layout = QHBoxLayout()
            
            bottom_left = QLabel("BOTTOM-LEFT CORNER")
            bottom_left.setStyleSheet("background-color: red; color: white; padding: 10px; font-weight: bold;")
            bottom_left.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
            
            bottom_right = QLabel("BOTTOM-RIGHT CORNER")
            bottom_right.setStyleSheet("background-color: red; color: white; padding: 10px; font-weight: bold;")
            bottom_right.setAlignment(Qt.AlignRight | Qt.AlignBottom)
            
            bottom_layout.addWidget(bottom_left)
            bottom_layout.addStretch()
            bottom_layout.addWidget(bottom_right)
            
            corner_layout.addLayout(top_layout)
            corner_layout.addStretch()
            corner_layout.addLayout(bottom_layout)
            
            layout.addWidget(corner_frame)
            
        def create_system_info(self, layout):
            """Create system information display"""
            info_text = f"""
🖥️  SYSTEM INFO:
Screen: {screen_manager.screen_info['total_width'] if screen_manager.screen_info else 'Unknown'} x {screen_manager.screen_info['total_height'] if screen_manager.screen_info else 'Unknown'}
Raspberry Pi: {'Yes' if screen_manager.is_raspberry_pi else 'No'}
Display Server: {screen_manager.display_server}

📋 CHECK LIST:
✓ Can you see all four corner labels clearly?
✓ Is the red border visible completely around the screen?
✓ Are any parts of this window cut off or cropped?
✓ Does the window fill the entire screen?
            """
            
            info_label = QLabel(info_text.strip())
            info_label.setAlignment(Qt.AlignLeft)
            info_label.setStyleSheet("font-size: 14px; margin: 10px; background-color: #e8f5e8; padding: 15px; border-radius: 8px;")
            layout.addWidget(info_label)
            
        def create_control_buttons(self, layout):
            """Create control buttons"""
            button_layout = QHBoxLayout()
            
            # Refresh button
            refresh_btn = QPushButton("🔄 Refresh Fullscreen")
            refresh_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 6px;
                    margin: 5px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            refresh_btn.clicked.connect(self.refresh_fullscreen)
            
            # Info button
            info_btn = QPushButton("📊 Update Info")
            info_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 6px;
                    margin: 5px;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                }
            """)
            info_btn.clicked.connect(self.update_geometry_info)
            
            # Close button
            close_btn = QPushButton("❌ Close")
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 6px;
                    margin: 5px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            close_btn.clicked.connect(self.close)
            
            button_layout.addWidget(refresh_btn)
            button_layout.addWidget(info_btn)
            button_layout.addStretch()
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            
        def setup_timers(self):
            """Setup timers for automatic updates"""
            # Auto-update geometry info
            self.update_timer = QTimer()
            self.update_timer.timeout.connect(self.update_geometry_info)
            self.update_timer.start(2000)  # Update every 2 seconds
            
            # Initial delay then refresh
            QTimer.singleShot(1000, self.refresh_fullscreen)
            
        def refresh_fullscreen(self):
            """Force refresh fullscreen"""
            print("🔄 Manual fullscreen refresh requested...")
            force_fullscreen_refresh(self)
            self.update_geometry_info()
            
        def update_geometry_info(self):
            """Update window geometry information"""
            try:
                geo = self.geometry()
                frame_geo = self.frameGeometry()
                
                info = f"""WINDOW GEOMETRY:
Position: ({geo.x()}, {geo.y()})
Size: {geo.width()} x {geo.height()}
Frame Position: ({frame_geo.x()}, {frame_geo.y()})
Frame Size: {frame_geo.width()} x {frame_geo.height()}
Expected Size: {screen_manager.screen_info['total_width'] if screen_manager.screen_info else 'Unknown'} x {screen_manager.screen_info['total_height'] if screen_manager.screen_info else 'Unknown'}

Is Fullscreen: {self.isFullScreen()}
Is Maximized: {self.isMaximized()}
Is Visible: {self.isVisible()}
Is Active: {self.isActiveWindow()}
Window Flags: {self.windowFlags()}"""
                
                self.geometry_info.setPlainText(info)
                
            except Exception as e:
                self.geometry_info.setPlainText(f"Error getting geometry: {e}")
        
        def keyPressEvent(self, event):
            """Handle key press events"""
            if event.key() == Qt.Key_Escape:
                self.close()
            elif event.key() == Qt.Key_F11:
                self.refresh_fullscreen()
        
        def showEvent(self, event):
            """Handle show event"""
            super().showEvent(event)
            QTimer.singleShot(100, self.update_geometry_info)
    
    def main():
        """Run the display debug tool"""
        print("🔍 Display Debug Tool for Raspberry Pi")
        print("=" * 50)
        print("This tool will help identify display issues:")
        print("• Check if fullscreen is working properly")
        print("• Verify all screen corners are visible")
        print("• Display window geometry information")
        print("• Test fullscreen refresh functionality")
        print("=" * 50)
        
        app = QApplication(sys.argv)
        
        # Create and show debug window
        window = DisplayDebugWindow()
        window.show()
        
        print("📱 Debug window displayed")
        print("💡 Look for:")
        print("   - Can you see all four red corner markers?")
        print("   - Is the entire red border visible?")
        print("   - Is any content cropped or cut off?")
        print("💡 Press F11 to refresh fullscreen, ESC to close")
        
        # Run the application
        try:
            sys.exit(app.exec_())
        except KeyboardInterrupt:
            print("\n👋 Debug tool interrupted by user")
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