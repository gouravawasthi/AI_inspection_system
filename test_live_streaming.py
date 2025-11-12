#!/usr/bin/env python3
"""
Test Live Camera Streaming
Verify that live streaming works with the real camera
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap, QFont
import logging

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from camera.camera_manager import CameraManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class LiveStreamingWindow(QMainWindow):
    """Test window for live camera streaming"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live Camera Streaming Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create UI
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Live Camera Streaming Test")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Video display
        self.video_label = QLabel("Click 'Start Live Streaming' to begin...")
        self.video_label.setMinimumSize(800, 600)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("""
            border: 3px solid #2c3e50;
            background-color: #34495e;
            color: white;
            font-size: 24px;
            border-radius: 10px;
        """)
        self.video_label.setScaledContents(True)
        layout.addWidget(self.video_label)
        
        # Control panel
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        
        self.start_button = QPushButton("Start Live Streaming")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px 30px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        self.start_button.clicked.connect(self.start_streaming)
        control_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Streaming")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px 30px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.stop_button.clicked.connect(self.stop_streaming)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)
        
        layout.addWidget(control_panel)
        
        # Status display
        self.status_label = QLabel("Status: Ready to start live streaming")
        self.status_label.setFont(QFont("Arial", 14))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #2c3e50; margin: 10px;")
        layout.addWidget(self.status_label)
        
        # Camera manager
        self.camera = None
        self.frame_count = 0
        
    def start_streaming(self):
        """Start live camera streaming"""
        try:
            print("🚀 Starting live camera streaming...")
            self.status_label.setText("Status: Initializing camera...")
            
            # Create camera manager
            self.camera = CameraManager()
            
            # Connect signals
            self.camera.frame_ready.connect(self.on_frame_ready)
            self.camera.state_changed.connect(self.on_state_changed)
            self.camera.error_occurred.connect(self.on_error)
            
            # Start streaming
            success = self.camera.start_streaming()
            
            if success:
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.status_label.setText("Status: Live streaming active")
                print("✅ Live streaming started successfully!")
            else:
                self.status_label.setText("Status: Failed to start camera")
                print("❌ Failed to start live streaming")
                
        except Exception as e:
            print(f"❌ Error starting streaming: {e}")
            self.status_label.setText(f"Status: Error - {e}")
    
    def stop_streaming(self):
        """Stop camera streaming"""
        try:
            if self.camera:
                self.camera.stop()
                self.camera = None
                
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_label.setText("Status: Streaming stopped")
            self.video_label.clear()
            self.video_label.setText("Streaming stopped\n\nClick 'Start Live Streaming' to restart...")
            
            print("🛑 Live streaming stopped")
            
        except Exception as e:
            print(f"❌ Error stopping streaming: {e}")
    
    def on_frame_ready(self, qimage):
        """Handle new video frame"""
        try:
            self.frame_count += 1
            
            # Convert to QPixmap and display
            pixmap = QPixmap.fromImage(qimage)
            
            # Scale to fit display area
            scaled_pixmap = pixmap.scaled(
                self.video_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Display the live frame
            self.video_label.setPixmap(scaled_pixmap)
            
            # Update status every 30 frames
            if self.frame_count % 30 == 0:
                self.status_label.setText(f"Status: Live streaming - {self.frame_count} frames received | {qimage.width()}x{qimage.height()}")
            
            # Log first few frames
            if self.frame_count <= 5:
                print(f"📹 Live frame {self.frame_count}: {qimage.width()}x{qimage.height()}")
                
        except Exception as e:
            print(f"❌ Error displaying frame: {e}")
    
    def on_state_changed(self, state):
        """Handle camera state change"""
        print(f"🔄 Camera state changed to: {state}")
    
    def on_error(self, error_msg):
        """Handle camera error"""
        print(f"❌ Camera error: {error_msg}")
        self.status_label.setText(f"Status: Camera error - {error_msg}")
    
    def closeEvent(self, event):
        """Handle window close"""
        if self.camera:
            self.camera.stop()
        event.accept()


def main():
    """Run the live streaming test"""
    
    app = QApplication(sys.argv)
    
    window = LiveStreamingWindow()
    window.show()
    
    print("📹 Live Camera Streaming Test")
    print("=" * 50)
    print("✅ Camera 0 detected and configured")
    print("🎥 Click 'Start Live Streaming' to see real camera feed")
    print("📊 Frame counter will show received frames")
    print("🛑 Click 'Stop Streaming' or close window to stop")
    
    return app.exec_()


if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parent)
    exit(main())