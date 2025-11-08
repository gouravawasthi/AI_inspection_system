#!/usr/bin/env python3
"""
Test the updated configuration with logo paths
"""

import sys
import os

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
src_dir = os.path.join(project_dir, 'src')
sys.path.insert(0, src_dir)
sys.path.insert(0, project_dir)

def test_config_loading():
    """Test if the configuration loads with branding settings"""
    print("🔧 Testing configuration loading...")
    try:
        from src.config import config_manager
        
        # Load config
        config = config_manager.load_config()
        
        print("✅ Configuration loaded successfully")
        print(f"   📁 Logo directory: {config.gui.branding.logo_directory}")
        print(f"   🏢 Taisys logo: {config.gui.branding.taisys_logo}")
        print(f"   🏭 Avenya logo: {config.gui.branding.avenya_logo}")
        print(f"   📐 Logo dimensions: {config.gui.branding.logo_width}x{config.gui.branding.logo_height}")
        print(f"   👁️  Show logos: {config.gui.branding.show_logos}")
        
        return config
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return None

def test_logo_paths_with_config(config):
    """Test logo paths using configuration"""
    print("\n🖼️  Testing logo paths with config...")
    
    if not config:
        print("❌ No config available")
        return False
    
    # Get project root and logo directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    logo_dir = os.path.join(project_root, config.gui.branding.logo_directory)
    
    print(f"   📁 Project root: {project_root}")
    print(f"   📁 Logo directory: {logo_dir}")
    
    # Test each logo file
    logos = [
        config.gui.branding.taisys_logo,
        config.gui.branding.avenya_logo
    ]
    
    all_found = True
    for logo_file in logos:
        logo_path = os.path.join(logo_dir, logo_file)
        if os.path.exists(logo_path):
            file_size = os.path.getsize(logo_path)
            print(f"   ✅ {logo_file} - Found ({file_size} bytes)")
        else:
            print(f"   ❌ {logo_file} - Not found at {logo_path}")
            all_found = False
    
    return all_found

def test_gui_with_config():
    """Test GUI initialization with config"""
    print("\n🖥️  Testing GUI with configuration...")
    try:
        # Check if PyQt5 is available
        from PyQt5.QtWidgets import QApplication
        print("   ✅ PyQt5 available")
        
        # Try importing MainWindow (this will test config loading)
        from src.ui.mainwindow import MainWindow
        print("   ✅ MainWindow imported successfully with config")
        
        return True
    except ImportError as e:
        print(f"   ❌ PyQt5 not available: {e}")
        return False
    except Exception as e:
        print(f"   ❌ GUI initialization error: {e}")
        return False

def main():
    print("🔧 CONFIGURATION AND LOGO PATH TESTING")
    print("="*60)
    
    # Test configuration loading
    config = test_config_loading()
    
    # Test logo paths with config
    logos_ok = test_logo_paths_with_config(config)
    
    # Test GUI with config
    gui_ok = test_gui_with_config()
    
    print("\n" + "="*60)
    if config and logos_ok and gui_ok:
        print("🎉 All tests passed!")
        print("💡 Configuration-based logo loading is ready")
        print("💡 Run GUI with: /Users/gourav/opt/anaconda3/bin/python src/ui/mainwindow.py")
        return 0
    else:
        print("❌ Some tests failed")
        if not config:
            print("   • Configuration loading failed")
        if not logos_ok:
            print("   • Logo files not found")
        if not gui_ok:
            print("   • GUI initialization failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())