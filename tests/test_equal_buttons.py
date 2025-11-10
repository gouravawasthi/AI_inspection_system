#!/usr/bin/env python3
"""
Test the equal-sized buttons and renamed labels
"""

import sys
import os

# Add the UI directory to the path
sys.path.insert(0, '/home/taisys/Desktop/AI_inspection_system/src/ui')
sys.path.insert(0, '/home/taisys/Desktop/AI_inspection_system/src')

try:
    from PyQt5.QtWidgets import QApplication
    from base_inspection_window import BaseInspectionWindow
    
    class EqualButtonsTestWindow(BaseInspectionWindow):
        """Test implementation for equal button sizing"""
        
        def __init__(self):
            super().__init__(None, "EQUAL")
        
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
        """Run the equal buttons test"""
        print("🔍 Testing Equal-Sized Buttons and Renamed Labels")
        print("=" * 55)
        print("Changes made:")
        print("• All inspection control buttons now have equal size")
        print("• Fixed height: 40px for all buttons")
        print("• Fixed font size: 14px for consistency")
        print("• Renamed 'Start Inspection' → 'Capture'")
        print("• Renamed 'Back to Main Menu' → 'Main Menu'")
        print("• Consistent styling and spacing")
        print("=" * 55)
        
        app = QApplication(sys.argv)
        
        # Create and show test window
        window = EqualButtonsTestWindow()
        window.show()
        
        print("📱 Equal buttons test window displayed")
        print("💡 Check if:")
        print("   - All buttons have the same height (40px)")
        print("   - Button text is consistent size (14px)")
        print("   - 'Capture' button (was 'Start Inspection')")
        print("   - 'Main Menu' button (was 'Back to Main Menu')")
        print("   - Buttons are evenly spaced and aligned")
        print("   - Colors distinguish button functions clearly")
        print("💡 Press ESC or close window to exit")
        
        # Button list for reference
        print(f"\n🎯 Button Layout (top to bottom):")
        buttons = [
            "Capture (Green - was 'Start Inspection')",
            "Next Step (Blue)",
            "Repeat Step (Blue)",
            "Manual Override (Orange)",
            "--- Spacer ---",
            "Stop Inspection (Red)",
            "Main Menu (Gray - was 'Back to Main Menu')",
            "QUIT APPLICATION (Dark Red)"
        ]
        for i, button in enumerate(buttons, 1):
            print(f"   {i}. {button}")
        
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