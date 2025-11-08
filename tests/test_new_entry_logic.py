#!/usr/bin/env python3
"""
Test the updated API manager logic for new entry scenario
"""
import sys
import os

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from src.api import APIManager

def test_new_entry_logic():
    """Test the updated logic for new entry scenario"""
    print("=== Testing Updated API Manager Logic ===\n")
    
    # Create API manager for CHIP_TO_EOLT workflow
    api_manager = APIManager.create_workflow('CHIP_TO_EOLT')
    print(f"Created workflow: {api_manager.placeholders}")
    
    # Test barcode that exists in CHIP but not in EOLT
    barcode = "QUICK_TEST_001"
    print(f"\nTesting barcode: {barcode}")
    print("Expected: exists in CHIP, does NOT exist in EOLT")
    
    result = api_manager.process_barcode(barcode)
    
    print(f"\n📊 Result:")
    print(f"   Status: {result['status']}")
    print(f"   Message: {result['message']}")
    print(f"   Action Required: {result['action_required']}")
    print(f"   Buttons: {result['buttons']}")
    
    # Test different workflow
    print("\n" + "="*50)
    api_manager2 = APIManager.create_workflow('INLINE_TOP_TO_EOLT') 
    print(f"Created workflow: {api_manager2.placeholders}")
    
    # Test barcode that doesn't exist in INLINE_TOP
    barcode2 = "NONEXISTENT_001" 
    print(f"\nTesting barcode: {barcode2}")
    print("Expected: does NOT exist in either table")
    
    result2 = api_manager2.process_barcode(barcode2)
    
    print(f"\n📊 Result:")
    print(f"   Status: {result2['status']}")
    print(f"   Message: {result2['message']}")
    print(f"   Action Required: {result2['action_required']}")

if __name__ == "__main__":
    test_new_entry_logic()