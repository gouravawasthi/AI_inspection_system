#!/usr/bin/env python3
"""Test the improved main window with resized brand images."""

import sys
import os
sys.path.append('/home/taisys/Desktop/AI_inspection_system')
sys.path.append('/home/taisys/Desktop/AI_inspection_system/src')

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QFrame, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont, QPainter, QColor, QPen

class TestMainWindow(QMainWindow):
    """Test main window with proper brand image resizing"""
    
    def __init__(self):
        super().__init__()
        
        # Mock branding config for testing
        class MockBranding:
            def __init__(self):
                self.logo_directory = "brand_images"
                self.taisys_logo = "Taisys.jpeg"
                self.avenya_logo = "Avenya.jpg"
                self.logo_width = 300
                self.logo_height = 200
                self.show_logos = True
                self.background_color = "#ffffff"
        
        self.branding = MockBranding()
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("AI Inspection System - Brand Image Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Title
        title_label = QLabel("AI Inspection System")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 36, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50; margin: 30px;")
        main_layout.addWidget(title_label)
        
        # Brand section
        self.create_brand_section(main_layout)
        
        # Spacer
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Test buttons
        self.create_test_buttons(main_layout)
        
        # Spacer
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        print("✅ Test main window created with improved brand images!")
    
    def create_brand_section(self, main_layout):
        """Create brand section with properly sized images"""
        brand_layout = QHBoxLayout()
        
        # Add spacer to center content
        brand_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Taisys section
        taisys_frame = QFrame()
        taisys_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #3498db;
                border-radius: 10px;
                background-color: white;
                padding: 15px;
                margin: 5px;
            }
        """)
        taisys_layout = QVBoxLayout()
        taisys_frame.setLayout(taisys_layout)
        
        # Set fixed size
        frame_width = self.branding.logo_width + 50
        frame_height = self.branding.logo_height + 100
        taisys_frame.setFixedSize(frame_width, frame_height)
        
        # Taisys image
        taisys_image = QLabel()
        taisys_pixmap = self.load_brand_image(self.branding.taisys_logo)
        if taisys_pixmap:
            taisys_image.setPixmap(taisys_pixmap)
            taisys_image.setAlignment(Qt.AlignCenter)
        else:
            taisys_image.setText("Taisys Logo")
            taisys_image.setAlignment(Qt.AlignCenter)
        
        # Taisys text
        taisys_text = QLabel("Built for Taisys")
        taisys_text.setAlignment(Qt.AlignCenter)
        taisys_text.setFont(QFont("Arial", 16, QFont.Bold))
        taisys_text.setStyleSheet("color: #3498db; margin: 10px 0px;")
        
        taisys_layout.addWidget(taisys_image)
        taisys_layout.addWidget(taisys_text)
        brand_layout.addWidget(taisys_frame)
        
        # Spacer between frames
        brand_layout.addItem(QSpacerItem(30, 20, QSizePolicy.Fixed, QSizePolicy.Minimum))
        
        # Avenya section
        avenya_frame = QFrame()
        avenya_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #e74c3c;
                border-radius: 10px;
                background-color: white;
                padding: 15px;
                margin: 5px;
            }
        """)
        avenya_layout = QVBoxLayout()
        avenya_frame.setLayout(avenya_layout)
        avenya_frame.setFixedSize(frame_width, frame_height)
        
        # Avenya image
        avenya_image = QLabel()
        avenya_pixmap = self.load_brand_image(self.branding.avenya_logo)
        if avenya_pixmap:
            avenya_image.setPixmap(avenya_pixmap)
            avenya_image.setAlignment(Qt.AlignCenter)
        else:
            avenya_image.setText("Avenya Logo")
            avenya_image.setAlignment(Qt.AlignCenter)
        
        # Avenya text
        avenya_text = QLabel("Built by Avenya")
        avenya_text.setAlignment(Qt.AlignCenter)
        avenya_text.setFont(QFont("Arial", 16, QFont.Bold))
        avenya_text.setStyleSheet("color: #e74c3c; margin: 10px 0px;")
        
        avenya_layout.addWidget(avenya_image)
        avenya_layout.addWidget(avenya_text)
        brand_layout.addWidget(avenya_frame)
        
        # Add spacer to center content
        brand_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        main_layout.addLayout(brand_layout)
    
    def create_test_buttons(self, main_layout):
        """Create test buttons"""
        buttons_layout = QHBoxLayout()
        buttons_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Test button
        test_button = QPushButton("Brand Images Loaded ✅")
        test_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 15px 32px;
                text-align: center;
                font-size: 16px;
                margin: 4px 2px;
                border-radius: 8px;
                font-weight: bold;
                min-width: 250px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        test_button.clicked.connect(self.close)
        buttons_layout.addWidget(test_button)
        
        buttons_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        main_layout.addLayout(buttons_layout)
    
    def load_brand_image(self, image_name):
        """Load and properly resize brand image"""
        try:
            # Get image path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            image_path = os.path.join(project_root, self.branding.logo_directory, image_name)
            
            print(f"Loading: {image_path}")
            
            if not os.path.exists(image_path):
                print(f"❌ Image not found: {image_path}")
                return None
            
            # Load original image
            original_pixmap = QPixmap(image_path)
            if original_pixmap.isNull():
                print(f"❌ Failed to load image: {image_name}")
                return None
            
            # Target dimensions with padding
            target_width = self.branding.logo_width
            target_height = self.branding.logo_height
            padding = 10
            canvas_width = target_width + (2 * padding)
            canvas_height = target_height + (2 * padding)
            
            # Create canvas
            result_pixmap = QPixmap(canvas_width, canvas_height)
            result_pixmap.fill(QColor(self.branding.background_color))
            
            # Scale image to fit
            scaled_pixmap = original_pixmap.scaled(
                target_width,
                target_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Draw on canvas
            painter = QPainter(result_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            
            # Center the image
            x = padding + (target_width - scaled_pixmap.width()) // 2
            y = padding + (target_height - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
            
            # Add border
            pen = QPen(QColor("#e0e0e0"))
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawRect(0, 0, canvas_width - 1, canvas_height - 1)
            
            painter.end()
            
            print(f"✅ Processed {image_name}: {original_pixmap.width()}x{original_pixmap.height()} → {canvas_width}x{canvas_height}")
            return result_pixmap
            
        except Exception as e:
            print(f"❌ Error loading {image_name}: {e}")
            return None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TestMainWindow()
    window.show()
    
    print("\n🎨 Main Window Test with Brand Images")
    print("Brand images should be properly resized and fitted:")
    print("- Taisys: 1600x900 → fit in 300x200 area")
    print("- Avenya: 1617x1590 → fit in 300x200 area")
    print("- Both with 10px padding and subtle borders")
    print("\nClose the window when testing is complete.")
    
    sys.exit(app.exec_())