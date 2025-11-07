#!/usr/bin/env python3
"""
Debug ManualResult evaluation
"""
import sys
import os

# Add project root directory to Python path  
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from src.api import APIManager

def debug_manual_result():
    print("=== Debug ManualResult Evaluation ===\n")
    
    # Create API manager
    api_manager = APIManager.create_workflow('CHIP_TO_EOLT')
    
    # Test data from our API calls
    api1_response = {
        'count': 1, 
        'data': [{
            'Barcode': 'QUICK_TEST_001', 
            'DT': '2025-11-07 21:15:00', 
            'PASS_FAIL': 1,  # This should evaluate to True
            'Process_id': 'P001', 
            'Station_ID': 'S001'
        }], 
        'latest_only': True, 
        'table': 'CHIPINSPECTION'
    }
    
    api2_response = {
        'message': 'No record found in EOLTINSPECTION for Barcode: QUICK_TEST_001'
    }
    
    print("1. Testing _evaluate_manual_result:")
    
    result1 = api_manager._evaluate_manual_result(api1_response)
    print(f"   API1 result (CHIP with PASS_FAIL=1): {result1}")
    
    result2 = api_manager._evaluate_manual_result(api2_response)
    print(f"   API2 result (404 message): {result2}")
    
    print("\n2. Testing _get_record_data:")
    
    record1 = api_manager._get_record_data(api1_response)
    print(f"   API1 record: {record1}")
    
    record2 = api_manager._get_record_data(api2_response)
    print(f"   API2 record: {record2}")
    
    # Test with INLINE TOP data that has ManualResult
    api3_response = {
        'count': 1,
        'data': [{
            'Barcode': 'QUICK_TEST_002',
            'DT': '2025-11-07 21:15:00',
            'ManualResult': 1,  # This should evaluate to True
            'Process_id': 'P001',
            'Station_ID': 'S001'
        }],
        'latest_only': True,
        'table': 'INLINEINSPECTIONTOP'
    }
    
    result3 = api_manager._evaluate_manual_result(api3_response)
    print(f"   API3 result (INLINE with ManualResult=1): {result3}")

if __name__ == "__main__":
    debug_manual_result()