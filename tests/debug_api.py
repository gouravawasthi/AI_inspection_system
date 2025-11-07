#!/usr/bin/env python3
"""
Debug API Manager calls
"""
import sys
import os
import requests

# Add project root directory to Python path  
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

def debug_api_calls():
    print("=== Debug API Manager Calls ===\n")
    
    # Test direct API calls
    base_url = "http://127.0.0.1:5001/api"
    barcode = "QUICK_TEST_001"
    
    print("1. Direct API calls:")
    try:
        url = f"{base_url}/CHIPINSPECTION?barcode={barcode}"
        print(f"   Calling: {url}")
        response = requests.get(url, timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        url2 = f"{base_url}/EOLTINSPECTION?barcode={barcode}"
        print(f"   Calling: {url2}")
        response2 = requests.get(url2, timeout=5)
        print(f"   Status: {response2.status_code}")
        if response2.status_code == 404:
            print(f"   Response: {response2.json()}")
        else:
            print(f"   Response: {response2.text}")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n2. Testing API Manager _call_api method:")
    from src.api import APIManager
    
    api_manager = APIManager.create_workflow('CHIP_TO_EOLT')
    
    # Test the internal _call_api method
    url1 = f"{base_url}/CHIPINSPECTION?barcode={barcode}"
    url2 = f"{base_url}/EOLTINSPECTION?barcode={barcode}"
    
    ok1, result1 = api_manager._call_api("get", url1)
    print(f"   _call_api result 1: ok={ok1}, result={result1}")
    
    ok2, result2 = api_manager._call_api("get", url2)
    print(f"   _call_api result 2: ok={ok2}, result={result2}")
    
    print("\n3. Testing process_barcode:")
    result = api_manager.process_barcode(barcode)
    print(f"   Final result: {result}")

if __name__ == "__main__":
    debug_api_calls()