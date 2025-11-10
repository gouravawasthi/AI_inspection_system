#!/usr/bin/env python3
"""Test brand image resizing in the main window."""

import sys
import os
sys.path.append('/home/taisys/Desktop/AI_inspection_system')

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QFont

class BrandImageTest(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Brand Image Resize Test')
        self.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Brand Image Resize Test")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; margin: 20px;")
        layout.addWidget(title)
        
        # Test the brand loading function
        brand_layout = QHBoxLayout()
        
        # Test Taisys image
        taisys_frame = self.create_brand_frame("Taisys.jpeg", "Taisys", "#3498db")
        brand_layout.addWidget(taisys_frame)
        
        # Test Avenya image
        avenya_frame = self.create_brand_frame("Avenya.jpg", "Avenya", "#e74c3c")
        brand_layout.addWidget(avenya_frame)
        
        layout.addLayout(brand_layout)
        
        # Add info
        info_label = QLabel("Images should be properly scaled to 300x200 with padding and borders")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #666; margin: 20px;")
        layout.addWidget(info_label)
        
        self.setLayout(layout)
    
    def create_brand_frame(self, image_name, brand_name, color):
        """Create a brand frame with resized image"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {color};
                border-radius: 10px;
                background-color: white;
                padding: 15px;
                margin: 10px;
            }}
        """)
        
        layout = QVBoxLayout()
        frame.setLayout(layout)
        
        # Set fixed size
        frame.setFixedSize(350, 300)  # 300 + 50 for padding
        
        # Load and display image
        image_label = QLabel()
        pixmap = self.load_brand_image(image_name)
        
        if pixmap:
            image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignCenter)
            print(f"✅ Loaded {image_name}: {pixmap.width()}x{pixmap.height()}")
        else:
            image_label.setText(f"{brand_name} Logo\nNot Found")
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setStyleSheet(f"border: 2px dashed {color}; background-color: #f8f9fa; color: {color}; font-size: 16px; font-weight: bold; min-height: 220px;")
            print(f"❌ Failed to load {image_name}")
        
        # Brand text
        text_label = QLabel(f"{brand_name} Brand")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setFont(QFont("Arial", 14, QFont.Bold))
        text_label.setStyleSheet(f"color: {color}; margin: 5px;")
        
        layout.addWidget(image_label)
        layout.addWidget(text_label)
        
        return frame
    
    def load_brand_image(self, image_name):
        """Load brand image and return properly scaled pixmap"""
        try:
            # Configuration
            logo_width = 300
            logo_height = 200
            padding = 10
            canvas_width = logo_width + (2 * padding)
            canvas_height = logo_height + (2 * padding)
            
            # Get image path
            brand_dir = "/home/taisys/Desktop/AI_inspection_system/brand_images"
            image_path = os.path.join(brand_dir, image_name)
            
            print(f"Loading image: {image_path}")
            
            if not os.path.exists(image_path):
                print(f"❌ Image not found: {image_path}")
                return None
            
            # Load original image
            original_pixmap = QPixmap(image_path)
            if original_pixmap.isNull():
                print(f"❌ Failed to load image: {image_name}")
                return None
            
            print(f"Original image size: {original_pixmap.width()}x{original_pixmap.height()}")
            
            # Create canvas
            result_pixmap = QPixmap(canvas_width, canvas_height)
            result_pixmap.fill(QColor("#ffffff"))
            
            # Scale image to fit
            scaled_pixmap = original_pixmap.scaled(
                logo_width, 
                logo_height, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            print(f"Scaled image size: {scaled_pixmap.width()}x{scaled_pixmap.height()}")
            
            # Draw on canvas
            painter = QPainter(result_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            
            # Center the image
            x = padding + (logo_width - scaled_pixmap.width()) // 2
            y = padding + (logo_height - scaled_pixmap.height()) // 2
            
            painter.drawPixmap(x, y, scaled_pixmap)
            
            # Add border
            border_color = QColor("#e0e0e0")
            pen = QPen(border_color)
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawRect(0, 0, canvas_width - 1, canvas_height - 1)
            
            painter.end()
            
            print(f"✅ Final canvas size: {canvas_width}x{canvas_height}")
            
            return result_pixmap
            
        except Exception as e:
            print(f"❌ Error loading image {image_name}: {e}")
            return None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BrandImageTest()
    window.show()
    
    print("\nBrand Image Test Window Opened")
    print("Check that images are properly scaled and fitted")
    print("Expected: 300x200 logo area with 10px padding = 320x220 total")
    
    sys.exit(app.exec_())