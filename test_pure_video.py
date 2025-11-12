#!/usr/bin/env python3
"""
Test script to verify pure video streaming without split-screen concatenation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QPixmap
import cv2

from camera.camera_manager import CameraManager

class PureVideoTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pure Video Stream Test - No Concatenation")
        self.setGeometry(100, 100, 680, 520)
        
        # Create UI
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        self.video_label = QLabel("Waiting for video...")
        self.video_label.setFixedSize(640, 480)
        self.video_label.setStyleSheet("border: 1px solid black;")
        layout.addWidget(self.video_label)
        
        # Initialize camera
        self.camera_manager = CameraManager()
        self.camera_manager.frame_ready.connect(self.update_video)
        
        # Start streaming
        self.camera_manager.start_streaming()
        print("🎥 Starting pure video stream test...")
        print("✅ Should show single video stream without any message overlay")
        print("🛑 Close window to exit")
    
    @pyqtSlot(object)
    def update_video(self, qimg):
        """Update video display with QImage"""
        pixmap = QPixmap.fromImage(qimg)
        self.video_label.setPixmap(pixmap)
    
    def closeEvent(self, event):
        """Clean shutdown"""
        self.camera_manager.stop_streaming()
        print("✅ Pure video test completed")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    test_window = PureVideoTest()
    test_window.show()
    sys.exit(app.exec_())