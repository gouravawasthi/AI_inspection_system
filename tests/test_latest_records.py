#!/usr/bin/env python3
"""
Test script for latest record functionality
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

def test_latest_records():
    """Test the latest record functionality"""
    print("=" * 60)
    print("TESTING LATEST RECORD FUNCTIONALITY")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:5001/api"
    
    # Test data with different timestamps
    test_records = [
        {
            "Barcode": "TEST001",
            "DT": "2025-11-07 10:00:00",
            "Process_id": "P001",
            "Station_ID": "S001",
            "PASS_FAIL": "PASS"
        },
        {
            "Barcode": "TEST001", 
            "DT": "2025-11-07 12:00:00", # Later time - should be latest
            "Process_id": "P001",
            "Station_ID": "S001", 
            "PASS_FAIL": "FAIL"
        },
        {
            "Barcode": "TEST002",
            "DT": "2025-11-07 11:00:00",
            "Process_id": "P002",
            "Station_ID": "S002",
            "PASS_FAIL": "PASS"
        }
    ]
    
    table = "CHIPINSPECTION"
    
    print(f"1. Inserting test records into {table}...")
    for i, record in enumerate(test_records):
        try:
            response = requests.post(f"{base_url}/{table}", json=record, timeout=5)
            print(f"   Record {i+1}: Status {response.status_code} - {record['Barcode']} at {record['DT']}")
        except Exception as e:
            print(f"   Record {i+1}: Error - {e}")
    
    print("\n2. Testing latest record queries...")
    
    # Test 1: Get single latest record from entire table
    try:
        response = requests.get(f"{base_url}/{table}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   Latest record from table: {data['count']} record(s)")
            if data['data']:
                latest = data['data'][0]
                print(f"   -> Barcode: {latest.get('Barcode')}, DT: {latest.get('DT')}, Result: {latest.get('PASS_FAIL')}")
        else:
            print(f"   Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Get latest record for specific barcode
    test_barcode = "TEST001"
    try:
        response = requests.get(f"{base_url}/{table}?barcode={test_barcode}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   Latest record for {test_barcode}: {data['count']} record(s)")
            if data['data']:
                latest = data['data'][0]
                print(f"   -> DT: {latest.get('DT')}, Result: {latest.get('PASS_FAIL')} (should be FAIL from 12:00)")
        else:
            print(f"   Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Get latest record for each barcode  
    try:
        response = requests.get(f"{base_url}/{table}?all_latest=true", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   Latest record for each barcode: {data['count']} record(s)")
            for record in data['data']:
                print(f"   -> Barcode: {record.get('Barcode')}, DT: {record.get('DT')}, Result: {record.get('PASS_FAIL')}")
        else:
            print(f"   Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n3. Testing API Manager with latest records...")
    from api.api_manager import APIManager
    
    # Test API manager with our endpoints
    api_manager = APIManager(
        api1_url=f"{base_url}/{table}",
        api2_url=f"{base_url}/EOLTINSPECTION",
        placeholders=("chip", "eolt")
    )
    
    # Test processing a barcode that exists
    result = api_manager.process_barcode("TEST001")
    print(f"   API Manager result for TEST001: {result['status']} - {result['message']}")
    
    # Test processing a barcode that doesn't exist
    result = api_manager.process_barcode("NONEXISTENT")
    print(f"   API Manager result for NONEXISTENT: {result['status']} - {result['message']}")

def test_server_connection():
    """Test basic server connection"""
    try:
        response = requests.get("http://127.0.0.1:5000/api/CHIPINSPECTION", timeout=2)
        return response.status_code == 200
    except:
        return False

def main():
    """Main test function"""
    print("Testing Latest Record API Functionality")
    print("Server should be running on http://127.0.0.1:5000")
    print()
    
    # Check server connection
    if not test_server_connection():
        print("❌ Server not responding. Please start the server first:")
        print("   python main.py")
        return
    
    print("✅ Server is responding")
    time.sleep(1)
    
    # Run tests
    test_latest_records()
    
    print("\n" + "=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()