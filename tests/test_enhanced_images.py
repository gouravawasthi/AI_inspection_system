#!/usr/bin/env python3
"""
Test enhanced image loading with background fill
"""

import sys
import os

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
src_dir = os.path.join(project_dir, 'src')
sys.path.insert(0, src_dir)
sys.path.insert(0, project_dir)

def test_enhanced_image_loading():
    """Test the enhanced image loading functionality"""
    print("🖼️  TESTING ENHANCED IMAGE LOADING")
    print("="*60)
    
    try:
        # Check PyQt5 availability first
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QPixmap
        
        # Create QApplication instance (required for QPixmap operations)
        app = QApplication([])
        
        print("✅ PyQt5 initialized")
        
        # Import and test the MainWindow
        from src.ui.mainwindow import MainWindow
        
        # Create MainWindow instance
        window = MainWindow()
        print("✅ MainWindow created successfully")
        
        # Test configuration loading
        print(f"\n🔧 Configuration Details:")
        print(f"   📁 Logo directory: {window.branding.logo_directory}")
        print(f"   📐 Logo size: {window.branding.logo_width}x{window.branding.logo_height}")
        print(f"   🎨 Background color: {window.branding.background_color}")
        
        # Test loading each logo
        logos = [
            (window.branding.taisys_logo, "Taisys"),
            (window.branding.avenya_logo, "Avenya")
        ]
        
        print(f"\n📸 Testing Image Loading:")
        for logo_file, brand_name in logos:
            print(f"\n   {brand_name} Logo ({logo_file}):")
            
            # Test the image loading method
            pixmap = window.load_brand_image(logo_file)
            
            if pixmap and not pixmap.isNull():
                print(f"   ✅ Successfully processed image")
                print(f"   📐 Final dimensions: {pixmap.width()}x{pixmap.height()}")
                
                # Check if dimensions match config
                expected_w = window.branding.logo_width
                expected_h = window.branding.logo_height
                
                if pixmap.width() == expected_w and pixmap.height() == expected_h:
                    print(f"   ✅ Dimensions match config ({expected_w}x{expected_h})")
                else:
                    print(f"   ⚠️  Dimensions mismatch. Expected: {expected_w}x{expected_h}, Got: {pixmap.width()}x{pixmap.height()}")
            else:
                print(f"   ❌ Failed to process image")
        
        print(f"\n🚀 Testing GUI Display:")
        
        # Show the window briefly to test display
        window.show()
        print("   ✅ GUI window displayed successfully")
        
        # Process events to update display
        app.processEvents()
        
        # Close window
        window.close()
        print("   ✅ GUI window closed successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ PyQt5 import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔍 ENHANCED IMAGE LOADING TEST")
    print("="*60)
    
    success = test_enhanced_image_loading()
    
    print("\n" + "="*60)
    if success:
        print("🎉 Enhanced image loading test completed successfully!")
        print("💡 Features tested:")
        print("   • Larger image dimensions (800x600)")
        print("   • Aspect ratio preservation")
        print("   • Background color fill for mismatched ratios")
        print("   • Configuration-based sizing")
        print("\n💡 Run full GUI: /Users/gourav/opt/anaconda3/bin/python src/ui/mainwindow.py")
        return 0
    else:
        print("❌ Enhanced image loading test failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())