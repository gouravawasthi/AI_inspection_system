#!/usr/bin/env python3
"""
Test the wider camera area layout
"""

import sys
import os

# Add the UI directory to the path
sys.path.insert(0, '/home/taisys/Desktop/AI_inspection_system/src/ui')
sys.path.insert(0, '/home/taisys/Desktop/AI_inspection_system/src')

try:
    from PyQt5.QtWidgets import QApplication
    from base_inspection_window import BaseInspectionWindow
    
    class WiderCameraTestWindow(BaseInspectionWindow):
        """Test implementation for wider camera layout"""
        
        def __init__(self):
            super().__init__(None, "WIDE")
        
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
        """Run the wider camera layout test"""
        print("🔍 Testing Wider Camera Area Layout")
        print("=" * 50)
        print("Changes made:")
        print("• Control panel width: 400px → 320px (20% reduction)")
        print("• Inspection panel width: 400px → 320px (20% reduction)")
        print("• Camera area width: gained 160px total")
        print("• Camera display: 800px → 960px width")
        print("• Optimized side panel content for reduced space")
        print("• Maintained 5% bottom margin")
        print("=" * 50)
        
        app = QApplication(sys.argv)
        
        # Create and show test window
        window = WiderCameraTestWindow()
        window.show()
        
        print("📱 Wider camera test window displayed")
        print("💡 Check if:")
        print("   - Camera area looks significantly wider")
        print("   - Side panels are narrower but still functional")
        print("   - Buttons are still clearly visible and usable")
        print("   - Overall layout is balanced")
        print("   - Text and controls fit properly in reduced space")
        print("💡 Press ESC or close window to exit")
        
        # Layout info
        print(f"\n📏 Layout dimensions:")
        print(f"   Control Panel: 320px wide")
        print(f"   Camera Area: ~{1440-320-320-40}px wide (estimated)")
        print(f"   Inspection Panel: 320px wide")
        print(f"   Total Screen: 1440px wide")
        
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