#!/usr/bin/env python3
"""
Test script for API manager and server integration
"""

import sys
import os
import requests
import time

# Add project root directory to Python path  
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Import API manager only, don't start another server
from src.api import APIManager

def test_server_endpoints():
    """Test basic server endpoints"""
    print("=" * 50)
    print("TESTING SERVER ENDPOINTS")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5001/api"
    
    # Test available tables
    tables = ['CHIPINSPECTION', 'INLINEINSPECTIONBOTTOM', 'INLINEINSPECTIONTOP', 'EOLTINSPECTION']
    
    for table in tables:
        try:
            response = requests.get(f"{base_url}/{table}", timeout=5)
            print(f"GET {table}: Status {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Response: {len(data) if isinstance(data, list) else 'Non-list response'} records")
            else:
                print(f"  Error: {response.text}")
        except requests.exceptions.ConnectionError:
            print(f"GET {table}: Connection failed - server not running?")
        except Exception as e:
            print(f"GET {table}: Error - {e}")
        print()

def test_api_manager():
    """Test API manager functionality"""
    print("=" * 50)
    print("TESTING API MANAGER")
    print("=" * 50)
    
    # Since we have one server running on port 5000, 
    # we'll create mock API URLs that match the server structure
    api1_url = "http://127.0.0.1:5000/api/CHIPINSPECTION"  # Previous inspection check
    api2_url = "http://127.0.0.1:5000/api/EOLTINSPECTION"   # Current inspection check
    
    api_manager = APIManager(
        api1_url=api1_url,
        api2_url=api2_url,
        placeholders=("visual", "electrical")
    )
    
    # Test barcode processing
    test_barcode = "TEST123"
    print(f"Testing barcode: {test_barcode}")
    
    result = api_manager.process_barcode(test_barcode)
    print(f"Process result: {result}")
    
    # If action required, test action execution
    if result.get("action_required"):
        print("\nTesting action execution...")
        for action in ["delete", "update", "append"]:
            action_result = api_manager.execute_action(action, test_barcode, {"test": "data"})
            print(f"Action '{action}': {action_result}")
    
    # Test pending actions
    print("\nTesting commit pending actions...")
    commit_result = api_manager.commit_pending_actions()
    print(f"Commit result: {commit_result}")

def test_direct_api_calls():
    """Test direct API calls to understand server behavior"""
    print("=" * 50)
    print("TESTING DIRECT API CALLS")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5000/api"
    
    # Test POST with barcode data
    test_data = {
        "Barcode": "TEST123",
        "DT": "2025-11-07 20:40:00",
        "Process_id": "P001",
        "Station_ID": "S001",
        "PASS_FAIL": "PASS"
    }
    
    try:
        # Test POST to CHIPINSPECTION
        response = requests.post(f"{base_url}/CHIPINSPECTION", json=test_data, timeout=5)
        print(f"POST CHIPINSPECTION: Status {response.status_code}")
        print(f"Response: {response.text}")
        
        # Test GET after POST
        response = requests.get(f"{base_url}/CHIPINSPECTION", timeout=5)
        print(f"GET CHIPINSPECTION after POST: Status {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Records found: {len(data) if isinstance(data, list) else 'Non-list response'}")
            
    except requests.exceptions.ConnectionError:
        print("Connection failed - server not running?")
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Main test function"""
    print("API Manager and Server Testing")
    print("Server should be running on http://127.0.0.1:5000")
    print()
    
    # Give server a moment to fully start
    time.sleep(2)
    
    # Run tests
    test_server_endpoints()
    test_direct_api_calls()
    test_api_manager()
    
    print("=" * 50)
    print("TESTING COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    main()