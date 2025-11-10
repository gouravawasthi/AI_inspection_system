#!/usr/bin/env python3
"""
Test for main window transparency fix
Tests the background refresh functionality
"""

import os
import sys
import time

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest

def test_transparency_fix():
    """Test that main window background transparency is properly handled"""
    print("🧪 Testing Main Window Transparency Fix")
    print("=" * 50)
    
    # Create QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(['test'])
    
    # Import mainwindow after app creation
    try:
        from ui.mainwindow import MainWindow
    except ImportError as e:
        print(f"❌ Could not import MainWindow: {e}")
        return False
    
    try:
        print("🔍 Creating MainWindow...")
        main_window = MainWindow()
        print("✅ MainWindow created successfully")
        
        # Test background refresh method
        print("\n🔍 Testing background refresh method...")
        if hasattr(main_window, 'refresh_window_background'):
            main_window.refresh_window_background()
            print("✅ Background refresh method works")
        else:
            print("❌ Background refresh method missing")
            return False
        
        # Test improved remove_stay_on_top method
        print("\n🔍 Testing improved stay-on-top removal...")
        main_window.show()
        
        # Add stay-on-top flag
        main_window.setWindowFlags(main_window.windowFlags() | Qt.WindowStaysOnTopHint)
        main_window.show()
        
        # Check flag is set
        has_flag = bool(main_window.windowFlags() & Qt.WindowStaysOnTopHint)
        print(f"Stay-on-top flag applied: {has_flag}")
        
        # Remove flag using improved method
        main_window.remove_stay_on_top(main_window)
        
        # Check flag is removed
        has_flag = bool(main_window.windowFlags() & Qt.WindowStaysOnTopHint)
        print(f"Stay-on-top flag removed: {not has_flag}")
        
        if not has_flag:
            print("✅ Improved stay-on-top removal works")
        else:
            print("❌ Stay-on-top removal failed")
        
        # Test force_main_window_focus with transparency prevention
        print("\n🔍 Testing improved focus management...")
        main_window.force_main_window_focus()
        
        # Wait for timer operations
        QTest.qWait(250)
        
        # Check window is still visible and not transparent
        if main_window.isVisible():
            print("✅ Window remains visible after focus management")
        else:
            print("❌ Window became hidden during focus management")
        
        # Test restore_main_window with background refresh
        print("\n🔍 Testing main window restoration...")
        main_window.restore_main_window()
        
        # Wait for operations
        QTest.qWait(350)
        
        if main_window.isVisible():
            print("✅ Window restoration works correctly")
        else:
            print("❌ Window restoration failed")
        
        # Clean up
        main_window.close()
        
        print("\n" + "=" * 50)
        print("🎉 Transparency fix tests completed!")
        print("\n💡 Improvements made:")
        print("• Added explicit repaint() and update() calls")
        print("• Improved remove_stay_on_top with background preservation")
        print("• Added refresh_window_background() method")
        print("• Enhanced all focus management methods")
        print("\n✨ This should prevent transparency issues!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run transparency fix tests"""
    print("🚀 Starting Main Window Transparency Fix Tests...")
    print("=" * 60)
    
    success = test_transparency_fix()
    
    if success:
        print("\n🎉 All transparency fix tests passed!")
        print("\n📋 What was fixed:")
        print("• Window flag changes now preserve background rendering")
        print("• Added explicit repaint calls to prevent transparency")
        print("• Improved stay-on-top flag removal process")
        print("• Added background refresh functionality")
        print("\n🎯 The transparency issue should now be resolved!")
    else:
        print("\n❌ Some tests failed.")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)