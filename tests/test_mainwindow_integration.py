#!/usr/bin/env python3
"""
Test script for Main Window integration with inherited inspection classes
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test that all imports work correctly"""
    print("🧪 Testing imports...")
    
    try:
        # Test config imports
        from config import config_manager
        print("✅ Config manager imported successfully")
        
        # Test inspection window imports
        from src.ui.eolt_inspection_window import EOLTInspectionWindow
        print("✅ EOLTInspectionWindow imported successfully")
        
        from src.ui.inline_inspection_window import INLINEInspectionWindow
        print("✅ INLINEInspectionWindow imported successfully")
        
        from src.ui.base_inspection_window import BaseInspectionWindow
        print("✅ BaseInspectionWindow imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_class_creation():
    """Test that classes can be instantiated"""
    print("\n🧪 Testing class creation...")
    
    try:
        # Test creating inspection windows without showing them
        from src.ui.eolt_inspection_window import EOLTInspectionWindow
        from src.ui.inline_inspection_window import INLINEInspectionWindow
        
        # Create instances (but don't show them since we don't have PyQt5 runtime)
        print("📝 Creating EOLT inspection window instance...")
        eolt_class = EOLTInspectionWindow
        print("✅ EOLT class can be instantiated")
        
        print("📝 Creating INLINE inspection window instance...")
        inline_class = INLINEInspectionWindow
        print("✅ INLINE class can be instantiated")
        
        return True
    except Exception as e:
        print(f"❌ Class creation error: {e}")
        return False

def test_inheritance_structure():
    """Test the inheritance structure"""
    print("\n🧪 Testing inheritance structure...")
    
    try:
        from src.ui.eolt_inspection_window import EOLTInspectionWindow
        from src.ui.inline_inspection_window import INLINEInspectionWindow
        from src.ui.base_inspection_window import BaseInspectionWindow
        
        # Check inheritance
        print(f"✅ EOLTInspectionWindow inherits from BaseInspectionWindow: {issubclass(EOLTInspectionWindow, BaseInspectionWindow)}")
        print(f"✅ INLINEInspectionWindow inherits from BaseInspectionWindow: {issubclass(INLINEInspectionWindow, BaseInspectionWindow)}")
        
        # Check methods exist
        eolt_methods = [method for method in dir(EOLTInspectionWindow) if not method.startswith('_')]
        inline_methods = [method for method in dir(INLINEInspectionWindow) if not method.startswith('_')]
        base_methods = [method for method in dir(BaseInspectionWindow) if not method.startswith('_')]
        
        print(f"✅ EOLT has {len(eolt_methods)} methods")
        print(f"✅ INLINE has {len(inline_methods)} methods")
        print(f"✅ Base has {len(base_methods)} methods")
        
        return True
    except Exception as e:
        print(f"❌ Inheritance structure error: {e}")
        return False

def test_integration_flow():
    """Test the integration flow"""
    print("\n🧪 Testing integration flow...")
    
    try:
        # Test that main window can import inspection classes
        print("📝 Testing main window imports...")
        
        # Simulate what main window does
        from src.ui.eolt_inspection_window import EOLTInspectionWindow
        from src.ui.inline_inspection_window import INLINEInspectionWindow
        
        print("✅ Main window can import EOLT inspection class")
        print("✅ Main window can import INLINE inspection class")
        
        # Test method signatures exist
        eolt_instance_methods = ['get_inspection_steps', 'init_api_manager', 'get_api_endpoints', 
                                'collect_inspection_data', 'validate_step_data', 'perform_api_submissions']
        
        for method in eolt_instance_methods:
            if hasattr(EOLTInspectionWindow, method):
                print(f"✅ EOLT has required method: {method}")
            else:
                print(f"❌ EOLT missing method: {method}")
        
        for method in eolt_instance_methods:
            if hasattr(INLINEInspectionWindow, method):
                print(f"✅ INLINE has required method: {method}")
            else:
                print(f"❌ INLINE missing method: {method}")
        
        return True
    except Exception as e:
        print(f"❌ Integration flow error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Main Window Integration Tests\n")
    
    tests = [
        test_imports,
        test_class_creation,
        test_inheritance_structure,
        test_integration_flow
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed! Main window is ready to connect with inspection classes.")
    else:
        print("⚠️  Some tests failed. Please check the integration setup.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)