#!/usr/bin/env python3
"""
Test API connection and barcode validation
"""

import sys
import os
import requests

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_api_server():
    """Test if the API server is running"""
    print("🔍 Testing API Server Connection...")
    
    base_url = "http://127.0.0.1:5001/api"
    endpoints = {
        'CHIPINSPECTION': f"{base_url}/CHIPINSPECTION",
        'EOLTINSPECTION': f"{base_url}/EOLTINSPECTION",
        'INLINEINSPECTIONTOP': f"{base_url}/INLINEINSPECTIONTOP", 
        'INLINEINSPECTIONBOTTOM': f"{base_url}/INLINEINSPECTIONBOTTOM"
    }
    
    test_barcode = "TEST123"
    
    for name, url in endpoints.items():
        try:
            print(f"\n📡 Testing {name}...")
            print(f"   URL: {url}")
            
            # Test GET request
            response = requests.get(f"{url}?barcode={test_barcode}", timeout=5)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ Response: {data}")
                except:
                    print(f"   📄 Response: {response.text[:100]}...")
            elif response.status_code == 404:
                try:
                    data = response.json()
                    print(f"   ⚠️ Not Found: {data}")
                except:
                    print(f"   ⚠️ Not Found: {response.text[:100]}...")
            else:
                print(f"   ❌ Error: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection failed - Server not running on {url}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
def test_api_manager():
    """Test the API manager directly"""
    print("\n🧪 Testing API Manager...")
    
    try:
        from api.api_manager import APIManager
        
        # Create API manager for CHIP_TO_EOLT workflow
        print("   📝 Creating API Manager for CHIP_TO_EOLT workflow...")
        api_manager = APIManager.create_workflow('CHIP_TO_EOLT')
        
        print(f"   📡 API1: {api_manager.api1_url}")
        print(f"   📡 API2: {api_manager.api2_url}")
        print(f"   📝 Placeholders: {api_manager.placeholders}")
        
        # Test barcode processing
        test_barcodes = ["TEST123", "ABC456", "XYZ789"]
        
        for barcode in test_barcodes:
            print(f"\n   🔍 Testing barcode: {barcode}")
            result = api_manager.process_barcode(barcode)
            
            print(f"      Status: {result['status']}")
            print(f"      Message: {result['message']}")
            if result.get('action_required'):
                print(f"      Action Required: {result['action_required']}")
            if result.get('buttons'):
                print(f"      Buttons: {result['buttons']}")
                
    except Exception as e:
        print(f"   ❌ API Manager Error: {e}")
        import traceback
        traceback.print_exc()

def test_server_status():
    """Check if Flask server is running"""
    print("\n🌐 Checking Flask Server Status...")
    
    try:
        response = requests.get("http://127.0.0.1:5001/", timeout=5)
        print(f"   ✅ Flask server is running (Status: {response.status_code})")
        return True
    except requests.exceptions.ConnectionError:
        print("   ❌ Flask server is not running")
        print("   💡 To start the server, run:")
        print("      python src/server/server.py")
        return False
    except Exception as e:
        print(f"   ❌ Error checking server: {e}")
        return False

def check_database():
    """Check if database files exist"""
    print("\n💾 Checking Database Files...")
    
    db_paths = [
        "data/db/inspection_data.db",
        "data/db/chip_data_dummy.csv",
        "data/db/eolt_dummy.csv",
        "data/db/inline_top_dummy.csv",
        "data/db/inline_bottom_dummy.csv"
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            print(f"   ✅ {db_path} ({size} bytes)")
        else:
            print(f"   ❌ {db_path} (missing)")

def provide_solution():
    """Provide solution steps"""
    print("\n💡 SOLUTION STEPS:")
    print("=" * 50)
    
    print("\n1. 🔧 Start the API Server:")
    print("   cd /Users/gourav/Desktop/Taisys/AI_inspection_system")
    print("   python src/server/server.py")
    print("   (Leave this running in a separate terminal)")
    
    print("\n2. 📦 Load Database with Sample Data:")
    print("   python load_dummydata_db.py")
    print("   (This populates the database with test records)")
    
    print("\n3. ✅ Test with Valid Barcode:")
    print("   Use a barcode that exists in the CHIP inspection data")
    print("   Check data/db/chip_data_dummy.csv for valid barcodes")
    
    print("\n4. 🔄 Alternative - Use Mock Mode:")
    print("   If API is not needed for testing, the system will")
    print("   offer to proceed with mock validation when API fails")

def main():
    """Run comprehensive API diagnosis"""
    print("🚀 API Connection Diagnostic Tool")
    print("=" * 50)
    
    # Check server status first
    server_running = test_server_status()
    
    # Check database files
    check_database()
    
    if server_running:
        # Test API endpoints
        test_api_server()
        
        # Test API manager
        test_api_manager()
    else:
        print("\n⚠️  Cannot test APIs - Server is not running")
    
    # Provide solutions
    provide_solution()
    
    print("\n🎯 ROOT CAUSE ANALYSIS:")
    print("─" * 30)
    if not server_running:
        print("❌ Flask API server is not running")
        print("   This is why you're getting 'Unexpected API response'")
        print("   The API manager can't connect to validate barcodes")
    else:
        print("✅ Server is running - check individual API responses above")
    
    print("\n🔧 QUICK FIX:")
    print("1. Start server: python src/server/server.py")
    print("2. Try barcode validation again")
    print("3. If API error persists, choose 'Yes' when prompted to proceed anyway")

if __name__ == "__main__":
    main()