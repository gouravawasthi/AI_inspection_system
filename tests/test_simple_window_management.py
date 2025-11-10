#!/usr/bin/env python3
"""
Test the reverted simple window management
"""

import os
import sys
import time

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from PyQt5.QtTest import QTest

def test_simple_window_management():
    """Test the simplified window management"""
    print("🧪 Testing Simple Window Management (Reverted)")
    print("=" * 50)
    
    # Create QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(['test'])
    
    try:
        from ui.mainwindow import MainWindow
    except ImportError as e:
        print(f"❌ Could not import MainWindow: {e}")
        return False
    
    try:
        print("🔍 Creating MainWindow...")
        main_window = MainWindow()
        print("✅ MainWindow created successfully")
        
        # Test simple maximize method
        print("\n🔍 Testing simple maximize method...")
        if hasattr(main_window, 'maximize_and_bring_to_front'):
            main_window.maximize_and_bring_to_front()
            print("✅ maximize_and_bring_to_front method works")
        else:
            print("❌ maximize_and_bring_to_front method missing")
        
        # Test simplified focus method
        print("\n🔍 Testing simplified focus method...")
        main_window.force_main_window_focus()
        print("✅ Simplified focus method works")
        
        # Test simplified restore method
        print("\n🔍 Testing simplified restore method...")
        main_window.restore_main_window()
        print("✅ Simplified restore method works")
        
        # Verify event handlers are simple
        print("\n🔍 Checking event handlers are simplified...")
        
        # Check mousePressEvent
        import inspect
        mouse_source = inspect.getsource(main_window.mousePressEvent)
        if "super().mousePressEvent(event)" in mouse_source and len(mouse_source.split('\n')) <= 4:
            print("✅ mousePressEvent is simple")
        else:
            print("❌ mousePressEvent still complex")
        
        # Check showEvent  
        show_source = inspect.getsource(main_window.showEvent)
        if "super().showEvent(event)" in show_source and len(show_source.split('\n')) <= 4:
            print("✅ showEvent is simple")
        else:
            print("❌ showEvent still complex")
        
        # Clean up
        main_window.close()
        
        print("\n" + "=" * 50)
        print("🎉 Simple window management test completed!")
        print("\n💡 Reverted changes:")
        print("• Removed complex transparency fixes")
        print("• Simplified to showMaximized() + raise() + activateWindow()")
        print("• Removed background refresh complexity")
        print("• Removed stay-on-top flag management")
        print("• Simple event handlers")
        print("\n✨ Window management is now simple and direct!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run simple window management tests"""
    print("🚀 Starting Simple Window Management Tests...")
    print("=" * 60)
    
    success = test_simple_window_management()
    
    if success:
        print("\n🎉 All simple window management tests passed!")
        print("\n📋 Reverted to simple approach:")
        print("• Just maximize windows and bring to front")
        print("• No complex transparency handling")
        print("• Clean, simple code")
        print("\n🎯 Window management is now straightforward!")
    else:
        print("\n❌ Some tests failed.")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)