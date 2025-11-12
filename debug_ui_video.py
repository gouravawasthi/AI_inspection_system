#!/usr/bin/env python3
"""
Debug UI Video Display
Test if the UI is receiving and displaying video frames
"""

import sys
import os
import logging
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap
from camera.camera_manager import CameraManager

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class TestVideoWindow(QMainWindow):
    """Test window to display video frames"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Display Test")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create UI
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Video display label
        self.video_label = QLabel("Starting video test...")
        self.video_label.setMinimumSize(800, 480)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("border: 2px solid #ccc; background-color: #f0f0f0;")
        self.video_label.setScaledContents(True)
        layout.addWidget(self.video_label)
        
        # Control button
        self.start_button = QPushButton("Start Camera")
        self.start_button.clicked.connect(self.start_camera)
        layout.addWidget(self.start_button)
        
        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Camera manager
        self.camera = None
        self.frame_count = 0
        
    def start_camera(self):
        """Start camera streaming"""
        try:
            print("🚀 Starting camera...")
            self.camera = CameraManager()
            
            # Connect signals
            self.camera.frame_ready.connect(self.on_frame_ready)
            self.camera.state_changed.connect(self.on_state_changed)
            self.camera.error_occurred.connect(self.on_error)
            
            # Start streaming
            success = self.camera.start_streaming()
            if success:
                self.start_button.setText("Stop Camera")
                self.start_button.clicked.disconnect()
                self.start_button.clicked.connect(self.stop_camera)
                self.status_label.setText("Camera started successfully")
            else:
                self.status_label.setText("Failed to start camera")
                
        except Exception as e:
            print(f"❌ Error starting camera: {e}")
            self.status_label.setText(f"Error: {e}")
    
    def stop_camera(self):
        """Stop camera streaming"""
        if self.camera:
            self.camera.stop()
            self.start_button.setText("Start Camera")
            self.start_button.clicked.disconnect()
            self.start_button.clicked.connect(self.start_camera)
            self.status_label.setText("Camera stopped")
    
    def on_frame_ready(self, qimage):
        """Handle new video frame"""
        try:
            self.frame_count += 1
            print(f"📸 Frame {self.frame_count}: {qimage.width()}x{qimage.height()}")
            
            # Convert to QPixmap and display
            pixmap = QPixmap.fromImage(qimage)
            
            # Scale to fit label
            scaled_pixmap = pixmap.scaled(
                self.video_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Display the frame
            self.video_label.setPixmap(scaled_pixmap)
            
            # Update status
            self.status_label.setText(f"Frames received: {self.frame_count} | Size: {qimage.width()}x{qimage.height()}")
            
        except Exception as e:
            print(f"❌ Error displaying frame: {e}")
    
    def on_state_changed(self, state):
        """Handle camera state change"""
        print(f"🔄 Camera state: {state}")
    
    def on_error(self, error_msg):
        """Handle camera error"""
        print(f"❌ Camera error: {error_msg}")
        self.status_label.setText(f"Camera error: {error_msg}")


def main():
    """Run the video display test"""
    
    app = QApplication(sys.argv)
    
    window = TestVideoWindow()
    window.show()
    
    print("🎥 Video Display Test Window")
    print("=" * 40)
    print("1. Click 'Start Camera' button")
    print("2. Video should appear in the display area")
    print("3. Frame counter should increment")
    print("4. Click 'Stop Camera' to stop")
    
    return app.exec_()


if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parent)
    exit(main())