#!/usr/bin/env python3
"""
Test the redesigned inspection window layout
"""

import sys
import os

# Add the UI directory to the path
sys.path.insert(0, '/home/taisys/Desktop/AI_inspection_system/src/ui')
sys.path.insert(0, '/home/taisys/Desktop/AI_inspection_system/src')

try:
    from PyQt5.QtWidgets import QApplication
    from base_inspection_window import BaseInspectionWindow
    
    class TestInspectionWindow(BaseInspectionWindow):
        """Test implementation of base inspection window"""
        
        def __init__(self):
            super().__init__(None, "TEST")
        
        def get_inspection_steps(self):
            """Return test inspection steps"""
            return ["Step 1", "Step 2", "Step 3", "Step 4", "Step 5"]
        
        def get_api_endpoints(self):
            """Return test API endpoints"""
            return ["TEST_ENDPOINT_1", "TEST_ENDPOINT_2"]
        
        def validate_step_data(self, step_index, data):
            """Validate step data"""
            return True
        
        def collect_step_data(self, step_index):
            """Collect step data"""
            return {"step": step_index, "data": "test"}
        
        def init_api_manager(self):
            """Initialize API manager - test implementation"""
            pass
    
    def main():
        """Run the layout test"""
        print("🔍 Testing Redesigned Inspection Window Layout")
        print("=" * 50)
        print("Changes made:")
        print("• Removed API status and camera settings from control panel")
        print("• Moved them to the API data section on the right")
        print("• Increased height of inspection controls area")
        print("• Made buttons larger and more visible")
        print("• Added 5% bottom margin for better display")
        print("=" * 50)
        
        app = QApplication(sys.argv)
        
        # Create and show test window
        window = TestInspectionWindow()
        window.show()
        
        print("📱 Test inspection window displayed")
        print("💡 Check if:")
        print("   - Control panel has more space for buttons")
        print("   - Inspection control buttons are clearly visible")
        print("   - Camera settings are in the right panel")
        print("   - API status is in the right panel")
        print("   - Layout looks balanced and functional")
        print("💡 Press ESC or close window to exit")
        
        # Run the application
        try:
            sys.exit(app.exec_())
        except KeyboardInterrupt:
            print("\n👋 Test interrupted by user")
            app.quit()

    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure PyQt5 is installed and paths are correct")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)