#!/usr/bin/env python3
"""
Test script for ManualResult-based API Manager logic
"""

import sys
import os
import requests
import time
from datetime import datetime

# Add project root directory to Python path  
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from src.api import APIManager

def test_manual_result_logic():
    """Test the ManualResult-based logic"""
    print("=" * 60)
    print("TESTING MANUALRESULT-BASED API MANAGER LOGIC")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:5001/api"
    
    # Insert test records with different ManualResult values
    print("1. Setting up test data...")
    
    # Test record 1: CHIP_INSPECTION with PASS_FAIL=1 (Pass)
    chip_pass = {
        "Barcode": "TEST_PASS_001",
        "DT": "2025-11-07 21:00:00",
        "Process_id": "P001",
        "Station_ID": "S001",
        "PASS_FAIL": 1
    }
    
    # Test record 2: CHIP_INSPECTION with PASS_FAIL=0 (Fail)  
    chip_fail = {
        "Barcode": "TEST_FAIL_001",
        "DT": "2025-11-07 21:00:00",
        "Process_id": "P001", 
        "Station_ID": "S001",
        "PASS_FAIL": 0
    }
    
    # Insert into CHIP table (note: no ManualResult in CHIP table, so it will be None/0)
    for i, record in enumerate([chip_pass, chip_fail]):
        try:
            response = requests.post(f"{base_url}/CHIPINSPECTION", json=record, timeout=5)
            print(f"   CHIP record {i+1}: Status {response.status_code} - {record['Barcode']}")
        except Exception as e:
            print(f"   CHIP record {i+1}: Error - {e}")
    
    # Test record 3: INLINE TOP with ManualResult=1
    inline_pass = {
        "Barcode": "TEST_INLINE_PASS",
        "DT": "2025-11-07 21:00:00",
        "Process_id": "P001",
        "Station_ID": "S001", 
        "Screw": 1,
        "Plate": 1,
        "Result": 1,
        "ManualScrew": 1,
        "ManualPlate": 1,
        "ManualResult": 1  # This is the key field
    }
    
    # Test record 4: INLINE TOP with ManualResult=0
    inline_fail = {
        "Barcode": "TEST_INLINE_FAIL", 
        "DT": "2025-11-07 21:00:00",
        "Process_id": "P001",
        "Station_ID": "S001",
        "Screw": 0,
        "Plate": 1, 
        "Result": 0,
        "ManualScrew": 0,
        "ManualPlate": 1,
        "ManualResult": 0  # Failed
    }
    
    # Insert into INLINE TOP table
    for i, record in enumerate([inline_pass, inline_fail]):
        try:
            response = requests.post(f"{base_url}/INLINEINSPECTIONTOP", json=record, timeout=5)
            print(f"   INLINE TOP record {i+1}: Status {response.status_code} - {record['Barcode']}")
        except Exception as e:
            print(f"   INLINE TOP record {i+1}: Error - {e}")

    print("\n2. Testing API Manager with different workflows...")
    
    # Test Case 1: INLINE_TOP_TO_EOLT workflow
    print("\n   Test Case 1: INLINE_TOP_TO_EOLT workflow")
    api_manager = APIManager.create_workflow('INLINE_TOP_TO_EOLT')
    
    # Test with passing barcode
    print(f"   Testing barcode with ManualResult=1 (should pass):")
    result = api_manager.process_barcode("TEST_INLINE_PASS")
    print(f"   Result: {result['status']} - {result['message']}")
    
    # Test with failing barcode
    print(f"   Testing barcode with ManualResult=0 (should fail):")
    result = api_manager.process_barcode("TEST_INLINE_FAIL") 
    print(f"   Result: {result['status']} - {result['message']}")
    
    # Test with non-existent barcode
    print(f"   Testing non-existent barcode:")
    result = api_manager.process_barcode("NONEXISTENT_CODE")
    print(f"   Result: {result['status']} - {result['message']}")
    
    # Test Case 2: Custom endpoint configuration
    print("\n   Test Case 2: Custom endpoint configuration")
    api_manager2 = APIManager.create_from_config(
        'INLINE_INSPECTION_TOP',
        'EOLT_INSPECTION', 
        ('inline top inspection', 'EOLT testing')
    )
    
    print(f"   Testing with custom config:")
    result = api_manager2.process_barcode("TEST_INLINE_PASS")
    print(f"   Result: {result['status']} - {result['message']}")

def test_server_connection():
    """Test basic server connection"""
    try:
        response = requests.get("http://127.0.0.1:5001/api/CHIPINSPECTION", timeout=2)
        return response.status_code in [200, 404]  # 404 is OK for empty table
    except:
        return False

def main():
    """Main test function"""
    print("Testing ManualResult-based API Manager Logic")
    print("Server should be running on http://127.0.0.1:5001")
    print()
    
    # Check server connection
    if not test_server_connection():
        print("❌ Server not responding. Please start the server first:")
        print("   python main.py")
        return
    
    print("✅ Server is responding")
    time.sleep(1)
    
    # Run tests
    test_manual_result_logic()
    
    print("\n" + "=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()