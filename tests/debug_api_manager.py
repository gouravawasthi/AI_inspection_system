#!/usr/bin/env python3
"""
Debug script to test API manager behavior with A123
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from api.api_manager import APIManager

def test_api_manager_a123():
    """Test API manager with barcode A123"""
    print("🧪 Testing API Manager with A123...")
    
    # Simulate the inline inspection API manager setup
    api1_url = "http://127.0.0.1:5001/api/CHIPINSPECTION"
    api2_url = "http://127.0.0.1:5001/api/INLINEINSPECTIONBOTTOM"
    
    api_manager = APIManager(
        api1_url=api1_url,
        api2_url=api2_url,
        placeholders=("chipinspection", "inlineinspectionbottom")
    )
    
    print(f"📡 API1 URL: {api1_url}")
    print(f"📡 API2 URL: {api2_url}")
    
    # Test the process_barcode method
    print("\n🔍 Processing barcode A123...")
    result = api_manager.process_barcode("A123")
    
    print(f"\n📊 Result: {result}")
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"Action Required: {result.get('action_required', 'N/A')}")
    
    # Test individual API calls
    print("\n🔍 Testing individual API calls...")
    
    print("📡 Testing API1 (CHIPINSPECTION)...")
    ok1, result1 = api_manager._call_api("get", f"{api1_url}?barcode=A123")
    print(f"   Success: {ok1}")
    print(f"   Result: {result1}")
    
    print("📡 Testing API2 (INLINEINSPECTIONBOTTOM)...")
    ok2, result2 = api_manager._call_api("get", f"{api2_url}?barcode=A123")
    print(f"   Success: {ok2}")
    print(f"   Result: {result2}")

if __name__ == '__main__':
    test_api_manager_a123()