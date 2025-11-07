#!/usr/bin/env python3
"""
Quick test for ManualResult logic with 1/0 values
"""
import sys
import os
import requests
import time

# Add project root directory to Python path  
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from src.api import APIManager

def quick_test():
    base_url = "http://127.0.0.1:5001/api"
    
    print("=== Quick ManualResult Test (1/0 values) ===\n")
    
    # Test with existing barcode I123 first
    print("1. Testing existing barcode I123...")
    
    try:
        # Check what's in INLINEINSPECTIONTOP for I123
        response = requests.get(f"{base_url}/INLINEINSPECTIONTOP?barcode=I123", timeout=5)
        print(f"   GET I123 from INLINE TOP: Status {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data}")
        else:
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   GET error: {e}")
    
    # Insert test data with 1/0 values
    print("\n2. Inserting new test records...")
    
    # CHIP record with PASS_FAIL=1 (Pass)
    chip_pass = {
        "Barcode": "QUICK_TEST_001",
        "DT": "2025-11-07 21:15:00",
        "Process_id": "P001",
        "Station_ID": "S001",
        "PASS_FAIL": 1  # Using 1 for Pass
    }
    
    # INLINE TOP record with ManualResult=1 (Pass)
    inline_pass = {
        "Barcode": "QUICK_TEST_002", 
        "DT": "2025-11-07 21:15:00",
        "Process_id": "P001",
        "Station_ID": "S001",
        "Screw": 1,
        "Plate": 1,
        "Result": 1,
        "ManualScrew": 1,
        "ManualPlate": 1,
        "ManualResult": 1  # Using 1 for Pass
    }
    
    try:
        # Insert CHIP record
        response = requests.post(f"{base_url}/CHIPINSPECTION", json=chip_pass, timeout=5)
        print(f"   CHIP record (PASS_FAIL=1): Status {response.status_code}")
        
        # Insert INLINE record  
        response = requests.post(f"{base_url}/INLINEINSPECTIONTOP", json=inline_pass, timeout=5)
        print(f"   INLINE record (ManualResult=1): Status {response.status_code}")
        
    except Exception as e:
        print(f"   Insert error: {e}")
        return
    
    print("\n3. Testing API Manager workflows...")
    
    # Test with the existing barcode I123
    print("   Testing existing barcode I123 with INLINE_TOP_TO_EOLT:")
    try:
        api_manager = APIManager.create_workflow('INLINE_TOP_TO_EOLT')
        result = api_manager.process_barcode("I123")
        print(f"   → Status: {result['status']}")
        print(f"   → Message: {result['message']}")
    except Exception as e:
        print(f"   → Error: {e}")
    
    # Test CHIP_TO_EOLT workflow with our new record
    print("\n   Testing CHIP_TO_EOLT workflow:")
    try:
        api_manager2 = APIManager.create_workflow('CHIP_TO_EOLT')
        result2 = api_manager2.process_barcode("QUICK_TEST_001")
        print(f"   → Status: {result2['status']}")
        print(f"   → Message: {result2['message']}")
    except Exception as e:
        print(f"   → Error: {e}")
    
    # Test INLINE_TOP_TO_EOLT workflow with our new record
    print("\n   Testing INLINE_TOP_TO_EOLT workflow:")
    try:
        result3 = api_manager.process_barcode("QUICK_TEST_002")
        print(f"   → Status: {result3['status']}")
        print(f"   → Message: {result3['message']}")
    except Exception as e:
        print(f"   → Error: {e}")
    
    # Test with non-existent barcode
    print("\n   Testing non-existent barcode:")
    try:
        result3 = api_manager.process_barcode("NONEXISTENT_123")
        print(f"   → Status: {result3['status']}")
        print(f"   → Message: {result3['message']}")
    except Exception as e:
        print(f"   → Error: {e}")
    
    print("\n✅ Quick test complete!")

if __name__ == "__main__":
    quick_test()