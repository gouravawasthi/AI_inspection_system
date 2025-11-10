"""
Main application window for AI VDI System
"""

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QLabel, QFrame, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont

# Add parent directory to path for config imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config_manager

# Try to import inspection windows - handle both direct and package import
try:
    from .eolt_inspection_window import EOLTInspectionWindow
    from .inline_inspection_window import INLINEInspectionWindow
except ImportError:
    # Fallback for direct execution
    try:
        from eolt_inspection_window import EOLTInspectionWindow
        from inline_inspection_window import INLINEInspectionWindow
    except ImportError:
        # Mock classes for testing
        class EOLTInspectionWindow:
            def __init__(self): pass
            def show(self): pass
            def close(self): pass
        
        class INLINEInspectionWindow:
            def __init__(self): pass
            def show(self): pass
            def close(self): pass


class MainWindow(QMainWindow):
    """Main application window for the AI VDI System"""
    
    # Define signals
    eolt_inspection_requested = pyqtSignal()
    inline_inspection_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.inspection_window = None
        self.eolt_window = None
        self.inline_window = None
        
        # Load configuration
        try:
            self.config = config_manager.load_config()
            self.branding = self.config.gui.branding
        except Exception as e:
            print(f"Warning: Could not load config, using defaults: {e}")
            # Create default branding config
            from config import BrandingConfig
            self.branding = BrandingConfig()
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("AI Inspection System")
        
        # Import screen utilities for better display handling
        try:
            from .screen_utils import apply_fullscreen_to_window, force_fullscreen_refresh
        except ImportError:
            from screen_utils import apply_fullscreen_to_window, force_fullscreen_refresh
        
        # Apply fullscreen with 5% bottom margin for better UI spacing
        apply_fullscreen_to_window(self, bottom_margin_percent=5)
        
        # For Raspberry Pi, schedule a delayed refresh to fix any display issues
        try:
            from PyQt5.QtCore import QTimer
            self.refresh_timer = QTimer()
            self.refresh_timer.singleShot(500, lambda: force_fullscreen_refresh(self, bottom_margin_percent=5))
        except Exception as e:
            print(f"Could not setup refresh timer: {e}")
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
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
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton#eoltButton {
                background-color: #2196F3;
            }
            QPushButton#eoltButton:hover {
                background-color: #1976D2;
            }
            QPushButton#inlineButton {
                background-color: #FF9800;
            }
            QPushButton#inlineButton:hover {
                background-color: #F57C00;
            }
            QPushButton#quitButton {
                background-color: #f44336;
            }
            QPushButton#quitButton:hover {
                background-color: #da190b;
            }
            QLabel {
                color: #333;
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Add title
        title_label = QLabel("AI Inspection System")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 36, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50; margin: 30px;")
        main_layout.addWidget(title_label)
        
        # Create brand images section
        self.create_brand_section(main_layout)
        
        # Add spacer
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Create control buttons section
        self.create_buttons_section(main_layout)
        
        # Add spacer
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
    
    def create_brand_section(self, main_layout):
        """Create the brand images and text section"""
        # Create horizontal layout for brand section
        brand_layout = QHBoxLayout()
        
        # Add spacer to center the content
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
        
        # Set fixed size for consistent appearance
        frame_width = self.branding.logo_width + 50  # Add extra space for padding
        frame_height = self.branding.logo_height + 100  # Add space for text
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
            taisys_image.setStyleSheet(f"border: 2px dashed #3498db; min-height: {self.branding.logo_height}px; min-width: {self.branding.logo_width}px; background-color: #f8f9fa; color: #3498db; font-size: 18px; font-weight: bold;")
        
        # Taisys text
        taisys_text = QLabel("Built for Taisys")
        taisys_text.setAlignment(Qt.AlignCenter)
        taisys_text.setFont(QFont("Arial", 16, QFont.Bold))
        taisys_text.setStyleSheet("color: #3498db; margin: 10px 0px;")
        
        taisys_layout.addWidget(taisys_image)
        taisys_layout.addWidget(taisys_text)
        
        brand_layout.addWidget(taisys_frame)
        
        # Add spacer between images
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
        
        # Set fixed size for consistent appearance
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
            avenya_image.setStyleSheet(f"border: 2px dashed #e74c3c; min-height: {self.branding.logo_height}px; min-width: {self.branding.logo_width}px; background-color: #f8f9fa; color: #e74c3c; font-size: 18px; font-weight: bold;")
        
        # Avenya text
        avenya_text = QLabel("Built by Avenya")
        avenya_text.setAlignment(Qt.AlignCenter)
        avenya_text.setFont(QFont("Arial", 16, QFont.Bold))
        avenya_text.setStyleSheet("color: #e74c3c; margin: 10px 0px;")
        
        avenya_layout.addWidget(avenya_image)
        avenya_layout.addWidget(avenya_text)
        
        brand_layout.addWidget(avenya_frame)
        
        # Add spacer to center the content
        brand_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        main_layout.addLayout(brand_layout)
    
    def create_buttons_section(self, main_layout):
        """Create the control buttons section"""
        # Create horizontal layout for buttons
        buttons_layout = QHBoxLayout()
        
        # Add spacer to center buttons
        buttons_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Inspect EOLT button
        self.eolt_button = QPushButton("Inspect EOLT")
        self.eolt_button.setObjectName("eoltButton")
        self.eolt_button.setMinimumSize(200, 80)
        self.eolt_button.setFont(QFont("Arial", 16, QFont.Bold))
        self.eolt_button.clicked.connect(self.on_eolt_clicked)
        buttons_layout.addWidget(self.eolt_button)
        
        # Add spacer between buttons
        buttons_layout.addItem(QSpacerItem(30, 20, QSizePolicy.Fixed, QSizePolicy.Minimum))
        
        # Inspect INLINE button
        self.inline_button = QPushButton("Inspect INLINE")
        self.inline_button.setObjectName("inlineButton")
        self.inline_button.setMinimumSize(200, 80)
        self.inline_button.setFont(QFont("Arial", 16, QFont.Bold))
        self.inline_button.clicked.connect(self.on_inline_clicked)
        buttons_layout.addWidget(self.inline_button)
        
        # Add spacer between buttons
        buttons_layout.addItem(QSpacerItem(30, 20, QSizePolicy.Fixed, QSizePolicy.Minimum))
        
        # Quit button
        self.quit_button = QPushButton("QUIT")
        self.quit_button.setObjectName("quitButton")
        self.quit_button.setMinimumSize(200, 80)
        self.quit_button.setFont(QFont("Arial", 16, QFont.Bold))
        self.quit_button.clicked.connect(self.on_quit_clicked)
        buttons_layout.addWidget(self.quit_button)
        
        # Add spacer to center buttons
        buttons_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        main_layout.addLayout(buttons_layout)
    
    def load_brand_image(self, image_name):
        """Load brand image and return properly scaled pixmap with background fill"""
        try:
            # Get the path using config
            current_dir = os.path.dirname(os.path.abspath(__file__))  # src/ui/
            src_dir = os.path.dirname(current_dir)  # src/
            project_root = os.path.dirname(src_dir)  # project root
            image_path = os.path.join(project_root, self.branding.logo_directory, image_name)
            
            print(f"Looking for image at: {image_path}")  # Debug print
            
            if os.path.exists(image_path):
                from PyQt5.QtGui import QPainter, QColor, QPen
                from PyQt5.QtCore import QSize
                
                # Load original image
                original_pixmap = QPixmap(image_path)
                if original_pixmap.isNull():
                    print(f"❌ Failed to load image: {image_name}")
                    return None
                
                # Get target dimensions from config
                target_width = self.branding.logo_width
                target_height = self.branding.logo_height
                
                # Add padding for better visual appearance
                padding = 10
                canvas_width = target_width + (2 * padding)
                canvas_height = target_height + (2 * padding)
                
                # Get background color from config (default to white)
                bg_color = getattr(self.branding, 'background_color', '#ffffff')
                
                # Create a new pixmap with canvas dimensions
                result_pixmap = QPixmap(canvas_width, canvas_height)
                result_pixmap.fill(QColor(bg_color))
                
                # Scale original image to fit within target dimensions while preserving aspect ratio
                scaled_pixmap = original_pixmap.scaled(
                    target_width, 
                    target_height, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                
                # Create painter for drawing
                painter = QPainter(result_pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setRenderHint(QPainter.SmoothPixmapTransform)
                
                # Calculate position to center the image within padding
                x = padding + (target_width - scaled_pixmap.width()) // 2
                y = padding + (target_height - scaled_pixmap.height()) // 2
                
                # Draw the scaled image centered on the canvas
                painter.drawPixmap(x, y, scaled_pixmap)
                
                # Add a subtle border for better definition
                border_color = QColor("#e0e0e0")
                pen = QPen(border_color)
                pen.setWidth(1)
                painter.setPen(pen)
                painter.drawRect(0, 0, canvas_width - 1, canvas_height - 1)
                
                painter.end()
                
                print(f"✅ Successfully loaded and processed image: {image_name}")
                print(f"   Original size: {original_pixmap.width()}x{original_pixmap.height()}")
                print(f"   Scaled to fit: {scaled_pixmap.width()}x{scaled_pixmap.height()}")
                print(f"   Final canvas: {canvas_width}x{canvas_height} with {padding}px padding")
                
                return result_pixmap
            else:
                print(f"❌ Image not found: {image_path}")
                return None
        except Exception as e:
            print(f"❌ Error loading image {image_name}: {e}")
            return None
    
    def on_eolt_clicked(self):
        """Handle Inspect EOLT button click"""
        print("🔍 EOLT Inspection requested")
        self.eolt_inspection_requested.emit()
        
        # Close any existing inspection windows
        if self.inline_window:
            self.inline_window.close()
            self.inline_window = None
            
        # Create and show EOLT inspection window
        try:
            self.eolt_window = EOLTInspectionWindow()
            
            # Connect window closed signal to restore main window
            self.eolt_window.window_closed.connect(self.restore_main_window)
            
            # Minimize main window and show inspection window
            self.showMinimized()
            self.eolt_window.show()
            
            print("✅ EOLT Inspection window opened, main window minimized")
            self.show_inspection_status("EOLT Inspection Window Opened")
        except Exception as e:
            print(f"❌ Error opening EOLT inspection window: {e}")
            self.show_inspection_status(f"Error: {e}")
    
    def on_inline_clicked(self):
        """Handle Inspect INLINE button click"""
        print("🔍 INLINE Inspection requested")
        self.inline_inspection_requested.emit()
        
        # Close any existing inspection windows
        if self.eolt_window:
            self.eolt_window.close()
            self.eolt_window = None
            
        # Create and show INLINE inspection window
        try:
            self.inline_window = INLINEInspectionWindow()
            
            # Connect window closed signal to restore main window
            self.inline_window.window_closed.connect(self.restore_main_window)
            
            # Minimize main window and show inspection window
            self.showMinimized()
            self.inline_window.show()
            
            print("✅ INLINE Inspection window opened, main window minimized")
            self.show_inspection_status("INLINE Inspection Window Opened")
        except Exception as e:
            print(f"❌ Error opening INLINE inspection window: {e}")
            self.show_inspection_status(f"Error: {e}")
    
    def on_quit_clicked(self):
        """Handle quit button click - safely close everything"""
        print("🚪 Quit requested - shutting down safely...")
        self.quit_requested.emit()
        
        # Perform safe shutdown
        self.safe_shutdown()
    
    def restore_main_window(self):
        """Restore main window when inspection window is closed"""
        print("🔄 Restoring main window...")
        
        # Clear inspection window references
        if self.eolt_window:
            self.eolt_window = None
        if self.inline_window:
            self.inline_window = None
            
        # Restore main window
        self.showNormal()  # Restore from minimized state
        self.activateWindow()  # Bring to front
        self.raise_()  # Ensure it's on top
        
        print("✅ Main window restored")
        self.show_inspection_status("Returned to Main Menu")
    
    def show_inspection_status(self, message):
        """Show inspection status message"""
        # Update the window title temporarily to show status
        original_title = self.windowTitle()
        self.setWindowTitle(f"{original_title} - {message}")
        
        # You can add more sophisticated status display here
        print(f"📊 Status: {message}")
    
    def safe_shutdown(self):
        """Perform safe shutdown of the application"""
        try:
            print("🔄 Performing safe shutdown...")
            
            # Close any open inspection windows
            if self.inspection_window:
                self.inspection_window.close()
                self.inspection_window = None
                
            if self.eolt_window:
                self.eolt_window.close()
                self.eolt_window = None
                
            if self.inline_window:
                self.inline_window.close()
                self.inline_window = None
            
            # TODO: Add cleanup logic here:
            # - Stop any running inspections
            # - Close camera connections
            # - Save any pending data
            # - Stop server if needed
            # - Clean up resources
            
            print("✅ Safe shutdown completed")
            
            # Close the application
            self.close()
            QApplication.quit()
            
        except Exception as e:
            print(f"❌ Error during shutdown: {e}")
            # Force close if safe shutdown fails
            QApplication.quit()
    
    def closeEvent(self, event):
        """Handle application close event"""
        print("🚪 Application closing...")
        self.safe_shutdown()
        event.accept()


def main():
    """Main function to run the application"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()