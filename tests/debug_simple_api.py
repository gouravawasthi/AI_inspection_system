#!/usr/bin/env python3
"""
Simple debug script to test API manager behavior with A123
"""

import sys
import os
import requests

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_direct_api_calls():
    """Test direct API calls to understand the issue"""
    print("🧪 Testing Direct API Calls with A123...")
    
    api_base = "http://127.0.0.1:5001/api"
    barcode = "A123"
    
    # Test CHIPINSPECTION API
    print(f"\n📡 Testing {api_base}/CHIPINSPECTION?barcode={barcode}")
    try:
        response = requests.get(f"{api_base}/CHIPINSPECTION?barcode={barcode}")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json() if response.headers.get('content-type') == 'application/json' else response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test INLINEINSPECTIONBOTTOM API
    print(f"\n📡 Testing {api_base}/INLINEINSPECTIONBOTTOM?barcode={barcode}")
    try:
        response = requests.get(f"{api_base}/INLINEINSPECTIONBOTTOM?barcode={barcode}")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json() if response.headers.get('content-type') == 'application/json' else response.text}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == '__main__':
    test_direct_api_calls()