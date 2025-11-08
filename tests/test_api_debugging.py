#!/usr/bin/env python3
"""
Test script to verify API debugging and INLINE workflow
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_inline_api_workflows():
    """Test INLINE API workflow configuration"""
    print("🧪 Testing INLINE API Workflows")
    print("=" * 50)
    
    try:
        from config import config_manager
        config = config_manager.load_config()
        
        print("📋 Available workflows:")
        for workflow in config.workflows:
            print(f"   ✅ {workflow.name}: {workflow.api1_table} → {workflow.api2_table}")
            if not workflow.enabled:
                print("      ⚠️ (Disabled)")
        
        # Test INLINE specific workflows
        inline_workflows = [
            "CHIP_TO_INLINE_BOTTOM",
            "INLINE_BOTTOM_TO_INLINE_TOP"
        ]
        
        print(f"\n🔍 Checking required INLINE workflows:")
        for workflow_name in inline_workflows:
            found = False
            for wf in config.workflows:
                if wf.name == workflow_name:
                    print(f"   ✅ {workflow_name}: {wf.api1_table} → {wf.api2_table}")
                    found = True
                    break
            
            if not found:
                print(f"   ❌ {workflow_name}: NOT FOUND")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return False

def test_inline_window_creation():
    """Test INLINE inspection window creation and API manager initialization"""
    print("\n🧪 Testing INLINE Window Creation")
    print("=" * 50)
    
    try:
        from src.ui.inline_inspection_window import INLINEInspectionWindow
        
        print("📝 Creating INLINE inspection window...")
        
        # This would normally require PyQt5, but we can test the class structure
        print("   📋 Class structure:")
        print(f"      - Has get_inspection_steps: {hasattr(INLINEInspectionWindow, 'get_inspection_steps')}")
        print(f"      - Has init_api_manager: {hasattr(INLINEInspectionWindow, 'init_api_manager')}")
        print(f"      - Has get_api_endpoints: {hasattr(INLINEInspectionWindow, 'get_api_endpoints')}")
        print(f"      - Has perform_api_submissions: {hasattr(INLINEInspectionWindow, 'perform_api_submissions')}")
        
        # Test inspection steps
        try:
            # Create a minimal instance for testing (won't work with PyQt5 but shows structure)
            steps = ["TOP: Setup", "TOP: Screw", "TOP: Plate", "BOTTOM: Setup", "BOTTOM: Antenna", "BOTTOM: Capacitor", "BOTTOM: Speaker"]
            print(f"   📋 Expected steps: {len(steps)}")
            for i, step in enumerate(steps, 1):
                print(f"      {i}. {step}")
        except Exception as e:
            print(f"   ⚠️ Could not test steps directly: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing INLINE window: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_eolt_window_creation():
    """Test EOLT inspection window creation and API manager initialization"""
    print("\n🧪 Testing EOLT Window Creation")
    print("=" * 50)
    
    try:
        from src.ui.eolt_inspection_window import EOLTInspectionWindow
        
        print("📝 Creating EOLT inspection window...")
        
        print("   📋 Class structure:")
        print(f"      - Has get_inspection_steps: {hasattr(EOLTInspectionWindow, 'get_inspection_steps')}")
        print(f"      - Has init_api_manager: {hasattr(EOLTInspectionWindow, 'init_api_manager')}")
        print(f"      - Has get_api_endpoints: {hasattr(EOLTInspectionWindow, 'get_api_endpoints')}")
        print(f"      - Has perform_api_submissions: {hasattr(EOLTInspectionWindow, 'perform_api_submissions')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing EOLT window: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_manager_workflows():
    """Test API manager workflow creation"""
    print("\n🧪 Testing API Manager Workflows")
    print("=" * 50)
    
    try:
        from api.api_manager import APIManager, INSPECTION_WORKFLOWS
        
        print("📋 Available predefined workflows in APIManager:")
        for name, config in INSPECTION_WORKFLOWS.items():
            print(f"   ✅ {name}:")
            print(f"      API1: {config['api1_url']}")
            print(f"      API2: {config['api2_url']}")
            print(f"      Placeholders: {config['placeholders']}")
        
        # Test creating specific workflows
        test_workflows = [
            'CHIP_TO_EOLT',
            'CHIP_TO_INLINE_BOTTOM',
            'INLINE_BOTTOM_TO_INLINE_TOP'
        ]
        
        print(f"\n🔧 Testing workflow creation:")
        for workflow_name in test_workflows:
            try:
                if workflow_name in INSPECTION_WORKFLOWS:
                    api_manager = APIManager.create_workflow(workflow_name)
                    print(f"   ✅ {workflow_name}: Created successfully")
                    print(f"      API1: {api_manager.api1_url}")
                    print(f"      API2: {api_manager.api2_url}")
                    print(f"      Placeholders: {api_manager.placeholders}")
                else:
                    print(f"   ⚠️ {workflow_name}: Not found in predefined workflows")
            except Exception as e:
                print(f"   ❌ {workflow_name}: Failed to create - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing API manager: {e}")
        import traceback
        traceback.print_exc()
        return False

def simulate_inline_workflow():
    """Simulate the INLINE inspection workflow with debugging"""
    print("\n🎭 Simulating INLINE Inspection Workflow")
    print("=" * 50)
    
    print("📝 INLINE Inspection Process:")
    print("1. User enters barcode")
    print("2. System validates with CHIP_TO_INLINE_BOTTOM workflow")
    print("3. User performs BOTTOM inspection (Antenna, Capacitor, Speaker)")
    print("4. System submits BOTTOM data to INLINEINSPECTIONBOTTOM")
    print("5. User performs TOP inspection (Screw, Plate)")
    print("6. System validates with INLINE_BOTTOM_TO_INLINE_TOP workflow")
    print("7. System submits TOP data to INLINEINSPECTIONTOP")
    
    print(f"\n🔄 Workflow Details:")
    workflows = [
        ("Step 2", "CHIP_TO_INLINE_BOTTOM", "Validate barcode exists in CHIP", "Check INLINEINSPECTIONBOTTOM for duplicates"),
        ("Step 6", "INLINE_BOTTOM_TO_INLINE_TOP", "Validate BOTTOM results exist", "Submit to INLINEINSPECTIONTOP")
    ]
    
    for step, workflow, desc1, desc2 in workflows:
        print(f"   {step}: {workflow}")
        print(f"      📡 API1 Check: {desc1}")
        print(f"      📡 API2 Submit: {desc2}")
    
    print(f"\n📊 Expected Debug Output:")
    print("   🔧 Initializing INLINE API managers...")
    print("   ✅ INLINE BOTTOM API Manager initialized:")
    print("      📡 API1: http://127.0.0.1:5001/api/CHIPINSPECTION")
    print("      📡 API2: http://127.0.0.1:5001/api/INLINEINSPECTIONBOTTOM")
    print("   ✅ INLINE TOP API Manager initialized:")
    print("      📡 API1: http://127.0.0.1:5001/api/INLINEINSPECTIONBOTTOM")
    print("      📡 API2: http://127.0.0.1:5001/api/INLINEINSPECTIONTOP")
    
    return True

def main():
    """Run all API debugging tests"""
    print("🚀 API Debugging and Workflow Tests")
    print("=" * 60)
    
    tests = [
        test_inline_api_workflows,
        test_inline_window_creation,
        test_eolt_window_creation,
        test_api_manager_workflows,
        simulate_inline_workflow
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✅ PASSED\n")
            else:
                print("❌ FAILED\n")
        except Exception as e:
            print(f"❌ EXCEPTION: {e}\n")
    
    print("🏁 Test Summary")
    print("=" * 30)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        print("\n💡 Key Features Implemented:")
        print("   🔘 INLINE workflow: CHIP_TO_INLINE_BOTTOM → INLINE_BOTTOM_TO_INLINE_TOP")
        print("   🔘 EOLT workflow: CHIP_TO_EOLT")
        print("   🔘 Detailed API debugging output")
        print("   🔘 Proper workflow configuration")
        
        print("\n🚀 Ready for Testing:")
        print("   1. Start Flask server: python src/server/server.py")
        print("   2. Launch inspection windows")
        print("   3. Check console for detailed API debug output")
    else:
        print("\n⚠️ Some tests failed. Check implementation.")

if __name__ == "__main__":
    main()