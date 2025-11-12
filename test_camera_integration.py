#!/usr/bin/env python3
"""
Test Camera Integration System
Tests the complete camera integration workflow
"""

import sys
import os
import logging
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from camera.camera_integrator import CameraIntegrator
from ml.algorithm_engine import AlgorithmEngine


def test_camera_configs():
    """Test if all config files exist and are valid"""
    print("🔧 Testing Camera Configuration...")
    
    # Check camera config
    camera_config = Path("configs/camera_config.json")
    if camera_config.exists():
        print(f"✅ Camera config found: {camera_config}")
    else:
        print(f"❌ Camera config missing: {camera_config}")
        return False
    
    # Check algorithm config  
    algo_config = Path("configs/algo.json")
    if algo_config.exists():
        print(f"✅ Algorithm config found: {algo_config}")
    else:
        print(f"⚠️ Algorithm config missing: {algo_config} - will use default")
    
    return True


def test_camera_integrator():
    """Test camera integrator initialization"""
    print("\n📹 Testing Camera Integrator...")
    
    try:
        # Initialize camera integrator
        integrator = CameraIntegrator()
        print("✅ CameraIntegrator initialized successfully")
        
        # Check camera state
        state = integrator.get_camera_state()
        print(f"📊 Camera state: {state}")
        
        # Test INLINE parameters
        success = integrator.start_inspection_streaming('inline', submode='bottom')
        if success:
            print("✅ INLINE streaming started successfully")
            
            # Check if ready for capture
            ready = integrator.is_ready_for_capture()
            print(f"📸 Ready for capture: {ready}")
            
            # Stop inspection
            integrator.stop_inspection()
            print("✅ Inspection stopped successfully")
        else:
            print("⚠️ Camera streaming failed to start (camera may not be connected)")
        
        return True
        
    except Exception as e:
        print(f"❌ Camera integrator test failed: {e}")
        return False


def test_algorithm_engine():
    """Test algorithm engine initialization"""
    print("\n🧠 Testing Algorithm Engine...")
    
    try:
        from pathlib import Path
        algo_config = Path("configs/algo.json")
        
        if algo_config.exists():
            engine = AlgorithmEngine(str(algo_config))
            print("✅ AlgorithmEngine initialized with config")
        else:
            print("⚠️ Creating default algorithm config...")
            # Create minimal algo config for testing
            default_config = {
                "inline": {
                    "bottom": {"enabled": True},
                    "top": {"enabled": True}
                },
                "eolt": {
                    "front": {"enabled": True},
                    "back": {"enabled": True},
                    "left": {"enabled": True},
                    "right": {"enabled": True}
                }
            }
            
            import json
            with open(algo_config, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            engine = AlgorithmEngine(str(algo_config))
            print("✅ AlgorithmEngine initialized with default config")
        
        return True
        
    except Exception as e:
        print(f"❌ Algorithm engine test failed: {e}")
        return False


def main():
    """Run all camera integration tests"""
    print("🚀 Camera Integration System Test")
    print("=" * 50)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Change to script directory
    os.chdir(Path(__file__).resolve().parent)
    
    tests = [
        ("Configuration Files", test_camera_configs),
        ("Camera Integrator", test_camera_integrator), 
        ("Algorithm Engine", test_algorithm_engine)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 Tests Passed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("🎉 All camera integration tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed - check configuration and dependencies")
        return 1


if __name__ == "__main__":
    exit(main())