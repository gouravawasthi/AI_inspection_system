#!/usr/bin/env python3

"""
Debug script to test the exact barcode validation logic used by the GUI
for barcode A123 to see why it's marked as invalid.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.api.api_manager import APIManager
import requests

def test_api_responses():
    """Test the raw API responses first"""
    print("=== Testing Raw API Responses ===")
    
    try:
        # Test CHIPINSPECTION API
        response1 = requests.get("http://127.0.0.1:5001/api/CHIPINSPECTION?barcode=A123")
        print(f"CHIPINSPECTION API:")
        print(f"  Status: {response1.status_code}")
        print(f"  Response: {response1.json()}")
        print()
        
        # Test INLINEINSPECTIONBOTTOM API
        response2 = requests.get("http://127.0.0.1:5001/api/INLINEINSPECTIONBOTTOM?barcode=A123")
        print(f"INLINEINSPECTIONBOTTOM API:")
        print(f"  Status: {response2.status_code}")
        print(f"  Response: {response2.json()}")
        print()
        
        return response1.json(), response2.json()
        
    except Exception as e:
        print(f"Error testing raw APIs: {e}")
        return None, None

def test_validation_logic():
    """Test the API manager validation logic"""
    print("=== Testing API Manager Validation Logic ===")
    
    # Create API manager with CHIP_TO_INLINE_BOTTOM workflow
    api_manager = APIManager(
        api1_url="http://127.0.0.1:5001/api/CHIPINSPECTION",
        api2_url="http://127.0.0.1:5001/api/INLINEINSPECTIONBOTTOM",
        placeholders=("chip inspection", "inline bottom inspection")
    )
    
    print("Testing barcode A123 with CHIP_TO_INLINE_BOTTOM workflow:")
    result = api_manager.process_barcode("A123")
    
    print(f"Validation Result:")
    print(f"  Status: {result['status']}")
    print(f"  Message: {result['message']}")
    print(f"  Action Required: {result['action_required']}")
    print(f"  Data: {result['data']}")
    print()
    
    return result

def test_evaluate_manual_result():
    """Test the _evaluate_manual_result method with real API responses"""
    print("=== Testing _evaluate_manual_result Method ===")
    
    api_manager = APIManager(
        api1_url="http://127.0.0.1:5001/api/CHIPINSPECTION",
        api2_url="http://127.0.0.1:5001/api/INLINEINSPECTIONBOTTOM",
        placeholders=("chip inspection", "inline bottom inspection")
    )
    
    # Get real API responses
    api1_response, api2_response = test_api_responses()
    
    if api1_response:
        result1 = api_manager._evaluate_manual_result(api1_response)
        print(f"CHIPINSPECTION evaluation result: {result1}")
        
        # Show what fields are being checked
        if "data" in api1_response and api1_response["data"]:
            record = api1_response["data"][0]
            print(f"  Record fields: {list(record.keys())}")
            print(f"  PASS_FAIL value: {record.get('PASS_FAIL', 'NOT_FOUND')}")
            print(f"  ManualResult value: {record.get('ManualResult', 'NOT_FOUND')}")
    
    if api2_response:
        result2 = api_manager._evaluate_manual_result(api2_response)
        print(f"INLINEINSPECTIONBOTTOM evaluation result: {result2}")
        
        # Show what fields are being checked
        if "data" in api2_response and api2_response["data"]:
            record = api2_response["data"][0]
            print(f"  Record fields: {list(record.keys())}")
            print(f"  PASS_FAIL value: {record.get('PASS_FAIL', 'NOT_FOUND')}")
            print(f"  ManualResult value: {record.get('ManualResult', 'NOT_FOUND')}")

if __name__ == "__main__":
    print("🔍 Debugging Barcode A123 Validation\n")
    
    # Step 1: Test raw API responses
    api1_resp, api2_resp = test_api_responses()
    
    # Step 2: Test the evaluation logic
    test_evaluate_manual_result()
    
    # Step 3: Test full validation workflow
    validation_result = test_validation_logic()
    
    print("=== Summary ===")
    print(f"Final validation status: {validation_result['status']}")
    if validation_result['status'] == 'error':
        print(f"❌ Barcode A123 marked as INVALID")
        print(f"Reason: {validation_result['message']}")
    else:
        print(f"✅ Barcode A123 marked as VALID")