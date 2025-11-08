#!/usr/bin/env python3
"""
Test GUI integration with main system
"""

import sys
import os

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
src_dir = os.path.join(project_dir, 'src')
sys.path.insert(0, src_dir)
sys.path.insert(0, project_dir)

def test_gui_import():
    """Test if GUI components can be imported"""
    try:
        from src.ui.mainwindow import MainWindow
        print("✅ MainWindow imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import MainWindow: {e}")
        return False

def test_pyqt5_available():
    """Test if PyQt5 is available"""
    try:
        from PyQt5.QtWidgets import QApplication, QMainWindow
        from PyQt5.QtCore import Qt, pyqtSignal
        from PyQt5.QtGui import QPixmap, QFont
        print("✅ PyQt5 components imported successfully")
        return True
    except ImportError as e:
        print(f"❌ PyQt5 not available: {e}")
        return False

def test_main_system_integration():
    """Test if main system can work with GUI"""
    try:
        from main_structured import AIInspectionSystem, PYQT5_AVAILABLE
        print(f"✅ Main system imported, PyQt5 available: {PYQT5_AVAILABLE}")
        
        # Test creating system instance
        system = AIInspectionSystem()
        print("✅ AIInspectionSystem created successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Failed to import main system: {e}")
        return False

def main():
    print("🔍 Testing GUI Integration...")
    print("="*50)
    
    # Test PyQt5 availability
    pyqt5_ok = test_pyqt5_available()
    print()
    
    # Test GUI import
    gui_ok = test_gui_import()
    print()
    
    # Test main system integration
    system_ok = test_main_system_integration()
    print()
    
    print("="*50)
    if pyqt5_ok and gui_ok and system_ok:
        print("🎉 All GUI integration tests passed!")
        print("💡 You can now run the system with: python main_structured.py")
        return 0
    else:
        print("❌ Some tests failed. Check PyQt5 installation.")
        print("💡 To install PyQt5: pip install PyQt5")
        return 1

if __name__ == "__main__":
    sys.exit(main())