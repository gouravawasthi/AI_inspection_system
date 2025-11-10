#!/usr/bin/env python3
"""
Comprehensive test for complete window focus management system
Tests the full workflow: Main Window → Inspection Windows → Back to Main
"""

import os
import sys
import time

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest

# Mock the inspection windows first
class MockEOLTWindow(QWidget):
    window_closed = MagicMock()
    
    def __init__(self):
        super().__init__()
        self.window_closed = MagicMock()
    
    def close(self):
        self.window_closed.emit()
        super().close()

class MockINLINEWindow(QWidget):
    window_closed = MagicMock()
    
    def __init__(self):
        super().__init__()
        self.window_closed = MagicMock()
    
    def close(self):
        self.window_closed.emit()
        super().close()

# Patch the inspection window imports
sys.modules['ui.eolt_inspection_window'] = MagicMock()
sys.modules['ui.inline_inspection_window'] = MagicMock()

# Import with proper mocking
try:
    from ui.mainwindow import MainWindow
    from ui.eolt_inspection_window import EOLTInspectionWindow
    from ui.inline_inspection_window import INLINEInspectionWindow
except ImportError:
    # Create mock classes if imports fail
    class MainWindow:
        pass
    class EOLTInspectionWindow:
        pass  
    class INLINEInspectionWindow:
        pass

class TestCompleteWindowFocus(unittest.TestCase):
    """Test the complete window focus management system"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        if not QApplication.instance():
            cls.app = QApplication(['test'])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up test fixtures"""
        print("\n🧪 Setting up window focus test...")
        
        # Mock the inspection windows
        with patch('ui.mainwindow.EOLTInspectionWindow', MockEOLTWindow):
            with patch('ui.mainwindow.INLINEInspectionWindow', MockINLINEWindow):
                self.main_window = MainWindow()
        
        # Override the inspection window classes in the main window
        import ui.mainwindow
        ui.mainwindow.EOLTInspectionWindow = MockEOLTWindow
        ui.mainwindow.INLINEInspectionWindow = MockINLINEWindow
        
        print("✅ Test setup complete")
    
    def tearDown(self):
        """Clean up test fixtures"""
        if hasattr(self, 'main_window'):
            self.main_window.close()
            if self.main_window.eolt_window:
                self.main_window.eolt_window.close()
            if self.main_window.inline_window:
                self.main_window.inline_window.close()
    
    def test_main_window_initialization(self):
        """Test main window initializes with proper focus methods"""
        print("\n🔍 Testing main window initialization...")
        
        # Check that focus management methods exist
        self.assertTrue(hasattr(self.main_window, 'ensure_window_foreground'))
        self.assertTrue(hasattr(self.main_window, 'force_main_window_focus'))
        self.assertTrue(hasattr(self.main_window, 'restore_main_window'))
        self.assertTrue(hasattr(self.main_window, 'remove_stay_on_top'))
        
        print("✅ Main window has all required focus management methods")
    
    def test_eolt_inspection_window_focus(self):
        """Test EOLT inspection window focus management"""
        print("\n🔍 Testing EOLT inspection window focus...")
        
        # Show main window
        self.main_window.show()
        self.assertTrue(self.main_window.isVisible())
        
        # Click EOLT inspection button
        self.main_window.on_eolt_clicked()
        
        # Process events to handle window operations
        QTest.qWait(100)
        
        # Check that main window is hidden
        self.assertFalse(self.main_window.isVisible())
        
        # Check that EOLT window was created
        self.assertIsNotNone(self.main_window.eolt_window)
        self.assertTrue(self.main_window.eolt_window.isVisible())
        
        print("✅ EOLT inspection window focus management works")
    
    def test_inline_inspection_window_focus(self):
        """Test Inline inspection window focus management"""
        print("\n🔍 Testing Inline inspection window focus...")
        
        # Show main window
        self.main_window.show()
        self.assertTrue(self.main_window.isVisible())
        
        # Click Inline inspection button
        self.main_window.on_inline_clicked()
        
        # Process events to handle window operations
        QTest.qWait(100)
        
        # Check that main window is hidden
        self.assertFalse(self.main_window.isVisible())
        
        # Check that Inline window was created
        self.assertIsNotNone(self.main_window.inline_window)
        self.assertTrue(self.main_window.inline_window.isVisible())
        
        print("✅ Inline inspection window focus management works")
    
    def test_restore_main_window_focus(self):
        """Test restoring main window focus from inspection windows"""
        print("\n🔍 Testing main window restoration...")
        
        # Show main window
        self.main_window.show()
        
        # Open EOLT window
        self.main_window.on_eolt_clicked()
        QTest.qWait(100)
        
        # Main window should be hidden
        self.assertFalse(self.main_window.isVisible())
        
        # Simulate closing inspection window (restore main window)
        self.main_window.restore_main_window()
        QTest.qWait(100)
        
        # Main window should be visible again
        self.assertTrue(self.main_window.isVisible())
        
        print("✅ Main window restoration works")
    
    def test_wayland_compatible_focus_methods(self):
        """Test Wayland-compatible focus management methods"""
        print("\n🔍 Testing Wayland-compatible focus methods...")
        
        # Create a test widget
        test_widget = QWidget()
        test_widget.show()
        
        # Test ensure_window_foreground method
        try:
            self.main_window.ensure_window_foreground(test_widget)
            print("✅ ensure_window_foreground method works")
        except Exception as e:
            self.fail(f"ensure_window_foreground failed: {e}")
        
        # Test force_main_window_focus method
        try:
            self.main_window.force_main_window_focus()
            print("✅ force_main_window_focus method works")
        except Exception as e:
            self.fail(f"force_main_window_focus failed: {e}")
        
        # Test remove_stay_on_top method
        try:
            # Add stay-on-top flag first
            test_widget.setWindowFlags(test_widget.windowFlags() | Qt.WindowStaysOnTopHint)
            test_widget.show()
            
            # Remove it
            self.main_window.remove_stay_on_top(test_widget)
            print("✅ remove_stay_on_top method works")
        except Exception as e:
            self.fail(f"remove_stay_on_top failed: {e}")
        
        test_widget.close()
    
    def test_window_switching_workflow(self):
        """Test complete window switching workflow"""
        print("\n🔍 Testing complete window switching workflow...")
        
        # Start with main window visible
        self.main_window.show()
        self.assertTrue(self.main_window.isVisible())
        print("📱 Main window is visible")
        
        # 1. Switch to EOLT inspection
        self.main_window.on_eolt_clicked()
        QTest.qWait(100)
        self.assertFalse(self.main_window.isVisible())
        self.assertIsNotNone(self.main_window.eolt_window)
        print("🔬 Switched to EOLT inspection window")
        
        # 2. Switch to Inline inspection (should close EOLT)
        self.main_window.on_inline_clicked()
        QTest.qWait(100)
        self.assertFalse(self.main_window.isVisible())
        self.assertIsNotNone(self.main_window.inline_window)
        print("🔬 Switched to Inline inspection window")
        
        # 3. Return to main window
        self.main_window.restore_main_window()
        QTest.qWait(100)
        self.assertTrue(self.main_window.isVisible())
        print("📱 Returned to main window")
        
        print("✅ Complete window switching workflow works")
    
    def test_stay_on_top_timer_functionality(self):
        """Test the stay-on-top timer functionality"""
        print("\n🔍 Testing stay-on-top timer functionality...")
        
        # Create a test widget
        test_widget = QWidget()
        test_widget.show()
        
        # Add stay-on-top flag
        test_widget.setWindowFlags(test_widget.windowFlags() | Qt.WindowStaysOnTopHint)
        test_widget.show()
        
        # Check that stay-on-top flag is set
        self.assertTrue(test_widget.windowFlags() & Qt.WindowStaysOnTopHint)
        
        # Use the remove_stay_on_top method
        self.main_window.remove_stay_on_top(test_widget)
        
        # Check that stay-on-top flag is removed
        self.assertFalse(test_widget.windowFlags() & Qt.WindowStaysOnTopHint)
        
        test_widget.close()
        print("✅ Stay-on-top timer functionality works")

def main():
    """Run the complete window focus tests"""
    print("🧪 Starting Comprehensive Window Focus Management Tests...")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCompleteWindowFocus)
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Run tests
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("🎉 All window focus management tests passed!")
    else:
        print("❌ Some tests failed.")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)