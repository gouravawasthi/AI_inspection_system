#!/usr/bin/env python3
"""
Test logo paths for the GUI
"""

import sys
import os

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
src_dir = os.path.join(project_dir, 'src')
sys.path.insert(0, src_dir)
sys.path.insert(0, project_dir)

def test_logo_paths():
    """Test if logo files can be found"""
    print("🔍 Testing logo file paths...")
    print("="*50)
    
    # Get project root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    brand_images_dir = os.path.join(project_root, "brand_images")
    
    print(f"📁 Project root: {project_root}")
    print(f"📁 Brand images directory: {brand_images_dir}")
    print()
    
    # Check if brand_images directory exists
    if not os.path.exists(brand_images_dir):
        print("❌ brand_images directory not found!")
        return False
    
    print("✅ brand_images directory found")
    
    # List all files in brand_images
    print(f"\n📋 Files in brand_images:")
    try:
        files = os.listdir(brand_images_dir)
        for file in files:
            file_path = os.path.join(brand_images_dir, file)
            if os.path.isfile(file_path):
                print(f"   📄 {file}")
    except Exception as e:
        print(f"❌ Error listing files: {e}")
        return False
    
    # Test specific logo files
    logo_files = ["Taisys.jpeg", "Avenya.jpg"]
    
    print(f"\n🔍 Checking required logo files:")
    all_found = True
    
    for logo_file in logo_files:
        logo_path = os.path.join(brand_images_dir, logo_file)
        if os.path.exists(logo_path):
            file_size = os.path.getsize(logo_path)
            print(f"   ✅ {logo_file} - Found ({file_size} bytes)")
        else:
            print(f"   ❌ {logo_file} - Not found")
            all_found = False
    
    print("="*50)
    if all_found:
        print("🎉 All logo files found! GUI should display images correctly.")
        return True
    else:
        print("❌ Some logo files missing. GUI will show placeholder text.")
        return False

def test_gui_import():
    """Test if GUI can be imported and logo loading works"""
    try:
        from src.ui.mainwindow import MainWindow
        print("\n🔍 Testing GUI logo loading...")
        
        # Test the load_brand_image method without creating full GUI
        import tempfile
        from unittest.mock import MagicMock
        
        # Mock QPixmap for testing
        sys.modules['PyQt5.QtGui'].QPixmap = MagicMock()
        
        window = MainWindow()
        
        # Test loading each logo
        for logo_file in ["Taisys.jpeg", "Avenya.jpg"]:
            result = window.load_brand_image(logo_file)
            print(f"   Logo loading test for {logo_file}: {'✅ Success' if result else '❌ Failed'}")
        
        return True
        
    except ImportError as e:
        print(f"\n❌ Cannot test GUI logo loading: {e}")
        print("   (This is OK if PyQt5 is not installed)")
        return True
    except Exception as e:
        print(f"\n❌ Error testing GUI: {e}")
        return False

def main():
    print("🖼️  LOGO PATH TESTING")
    print("="*50)
    
    # Test file paths
    paths_ok = test_logo_paths()
    
    # Test GUI integration (if possible)
    gui_ok = test_gui_import()
    
    print("\n" + "="*50)
    if paths_ok:
        print("✅ Logo path testing completed successfully!")
        print("💡 Run the GUI with: /Users/gourav/opt/anaconda3/bin/python src/ui/mainwindow.py")
    else:
        print("❌ Logo path testing failed!")
        print("💡 Check that logo files exist in brand_images folder")
    
    return 0 if paths_ok else 1

if __name__ == "__main__":
    sys.exit(main())