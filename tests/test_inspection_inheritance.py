#!/usr/bin/env python3
"""
Test script for both EOLT and INLINE inspection windows
Demonstrates inheritance from BaseInspectionWindow
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox, QPushButton, QVBoxLayout, QWidget

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
src_dir = os.path.join(project_dir, 'src')
sys.path.insert(0, src_dir)
sys.path.insert(0, project_dir)


class InspectionTestLauncher(QWidget):
    """Simple launcher for testing both inspection types"""
    
    def __init__(self):
        super().__init__()
        self.inspection_window = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Inspection Test Launcher")
        self.setGeometry(300, 300, 400, 200)
        
        layout = QVBoxLayout()
        
        # EOLT Test Button
        eolt_btn = QPushButton("Test EOLT Inspection Window")
        eolt_btn.setMinimumHeight(50)
        eolt_btn.clicked.connect(self.launch_eolt)
        layout.addWidget(eolt_btn)
        
        # INLINE Test Button
        inline_btn = QPushButton("Test INLINE Inspection Window")
        inline_btn.setMinimumHeight(50)
        inline_btn.clicked.connect(self.launch_inline)
        layout.addWidget(inline_btn)
        
        # Info Button
        info_btn = QPushButton("Show Inheritance Info")
        info_btn.setMinimumHeight(50)
        info_btn.clicked.connect(self.show_info)
        layout.addWidget(info_btn)
        
        self.setLayout(layout)
    
    def launch_eolt(self):
        """Launch EOLT inspection window"""
        try:
            from src.ui.eolt_inspection_window import EOLTInspectionWindow
            
            if self.inspection_window:
                self.inspection_window.close()
            
            self.inspection_window = EOLTInspectionWindow(self)
            self.inspection_window.window_closed.connect(self.show)
            self.inspection_window.show()
            self.hide()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch EOLT window: {e}")
    
    def launch_inline(self):
        """Launch INLINE inspection window"""
        try:
            from src.ui.inline_inspection_window import INLINEInspectionWindow
            
            if self.inspection_window:
                self.inspection_window.close()
            
            self.inspection_window = INLINEInspectionWindow(self)
            self.inspection_window.window_closed.connect(self.show)
            self.inspection_window.show()
            self.hide()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch INLINE window: {e}")
    
    def show_info(self):
        """Show information about the inheritance structure"""
        info_text = """
🏗️ INSPECTION WINDOW INHERITANCE STRUCTURE

📋 BaseInspectionWindow (Parent Class):
   • Common UI components (control panel, camera panel, progress panel)
   • Barcode input and validation
   • API manager integration
   • Step-by-step inspection flow
   • Manual override functionality
   • Logging and data collection
   • Abstract methods for customization

🔍 EOLTInspectionWindow (Child Class):
   • Inherits from BaseInspectionWindow
   • Steps: Upper, Lower, Left, Right, Printtext, Barcodetext
   • Single API submission to EOLTINSPECTION endpoint
   • Validates 4 sides + text detection
   • ManualResult based on 1/0 values

🔍 INLINEInspectionWindow (Child Class):
   • Inherits from BaseInspectionWindow  
   • Steps: TOP (Setup, Screw, Plate) + BOTTOM (Setup, Antenna, Capacitor, Speaker)
   • TWO SEQUENTIAL API submissions:
     1. INLINEINSPECTIONTOP
     2. INLINEINSPECTIONBOTTOM
   • Both phases must pass for overall PASS

🔧 Key Differences:
   • Number of API calls: EOLT (1) vs INLINE (2)
   • Inspection components: Different for each type
   • Data validation: Component-specific logic
   • API data preparation: Tailored to each endpoint

🎯 Common Features (Inherited):
   • Barcode scanning and validation
   • Camera integration ready
   • Step-by-step progress tracking
   • Manual override with audit logging
   • Configurable API endpoints
   • Modular button activation/deactivation
        """
        
        QMessageBox.information(self, "Inheritance Structure", info_text)


def test_inheritance_features():
    """Test that inheritance is working correctly"""
    print("🧪 TESTING INHERITANCE FEATURES")
    print("="*60)
    
    try:
        # Test imports
        from src.ui.base_inspection_window import BaseInspectionWindow
        from src.ui.eolt_inspection_window import EOLTInspectionWindow
        from src.ui.inline_inspection_window import INLINEInspectionWindow
        
        print("✅ All inspection window classes imported successfully")
        
        # Test inheritance
        print(f"✅ EOLTInspectionWindow inherits from BaseInspectionWindow: {issubclass(EOLTInspectionWindow, BaseInspectionWindow)}")
        print(f"✅ INLINEInspectionWindow inherits from BaseInspectionWindow: {issubclass(INLINEInspectionWindow, BaseInspectionWindow)}")
        
        # Create QApplication for widget testing
        app = QApplication([])
        
        # Test abstract method implementation
        eolt_instance = EOLTInspectionWindow()
        inline_instance = INLINEInspectionWindow()
        
        print(f"✅ EOLT inspection steps: {len(eolt_instance.get_inspection_steps())} steps")
        print(f"   Steps: {eolt_instance.get_inspection_steps()}")
        
        print(f"✅ INLINE inspection steps: {len(inline_instance.get_inspection_steps())} steps")
        print(f"   Steps: {inline_instance.get_inspection_steps()}")
        
        print(f"✅ EOLT API endpoints: {eolt_instance.get_api_endpoints()}")
        print(f"✅ INLINE API endpoints: {inline_instance.get_api_endpoints()}")
        
        # Test key differences
        print(f"\n🔍 Key Differences:")
        print(f"   EOLT steps: {len(eolt_instance.get_inspection_steps())} (single inspection)")
        print(f"   INLINE steps: {len(inline_instance.get_inspection_steps())} (dual inspection)")
        print(f"   EOLT APIs: {len(eolt_instance.get_api_endpoints())} endpoints")
        print(f"   INLINE APIs: {len(inline_instance.get_api_endpoints())} endpoints")
        
        # Clean up instances
        eolt_instance.close()
        inline_instance.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Inheritance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("🚀 INSPECTION WINDOW INHERITANCE TEST")
    print("="*60)
    
    # Test inheritance features first
    inheritance_ok = test_inheritance_features()
    
    print("\n" + "="*60)
    
    if not inheritance_ok:
        print("❌ Inheritance tests failed!")
        return 1
    
    print("🎉 Inheritance tests passed!")
    
    # Ask if user wants to launch GUI test
    try:
        user_input = input("\n🤔 Launch GUI test launcher? (y/N): ").lower().strip()
        if user_input not in ['y', 'yes']:
            print("👋 Skipping GUI test")
            return 0
    except (KeyboardInterrupt, EOFError):
        print("\n👋 Skipping GUI test")
        return 0
    
    # Launch GUI test
    try:
        # Create new QApplication for GUI
        app = QApplication(sys.argv)
        
        launcher = InspectionTestLauncher()
        launcher.show()
        
        print("📱 GUI launcher started")
        print("\nFeatures to test:")
        print("  • EOLT: Single API submission workflow")
        print("  • INLINE: Dual API submission workflow") 
        print("  • Common: Barcode input, step progression, manual override")
        print("  • Inheritance: Shared UI components and base functionality")
        
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"❌ Failed to start GUI: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())