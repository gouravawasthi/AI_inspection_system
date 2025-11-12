#!/usr/bin/env python3
"""
Camera Detection and Live Streaming Setup
Detects available cameras and configures live streaming
"""

import sys
import os
import cv2
import json
from pathlib import Path

def detect_cameras():
    """Detect available camera devices"""
    print("🔍 Detecting available cameras...")
    available_cameras = []
    
    # Test camera indices 0-5
    for i in range(6):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                h, w = frame.shape[:2]
                print(f"✅ Camera {i}: Available ({w}x{h})")
                available_cameras.append({
                    'id': i,
                    'width': w,
                    'height': h,
                    'working': True
                })
            else:
                print(f"⚠️ Camera {i}: Detected but can't read frames")
                available_cameras.append({
                    'id': i,
                    'working': False
                })
            cap.release()
        else:
            print(f"❌ Camera {i}: Not available")
    
    if not available_cameras:
        print("🎮 No cameras detected - will use simulation mode")
    
    return available_cameras

def test_camera_streaming(camera_id):
    """Test live streaming from a specific camera"""
    print(f"\n📹 Testing camera {camera_id} streaming...")
    
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print(f"❌ Failed to open camera {camera_id}")
        return False
    
    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    # Test frame capture
    ret, frame = cap.read()
    if ret:
        h, w = frame.shape[:2]
        print(f"✅ Camera {camera_id} streaming test successful ({w}x{h})")
        
        # Test multiple frames
        for i in range(5):
            ret, frame = cap.read()
            if not ret:
                print(f"⚠️ Frame {i+1} failed")
                break
        else:
            print("✅ Multiple frame capture successful")
        
        cap.release()
        return True
    else:
        print(f"❌ Failed to capture frame from camera {camera_id}")
        cap.release()
        return False

def configure_live_streaming(camera_id=None):
    """Configure camera config for live streaming"""
    config_path = Path("configs/camera_config.json")
    
    # Load current config
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    if camera_id is not None:
        print(f"🔧 Configuring live streaming with camera {camera_id}...")
        config['camera_settings']['simulation_mode'] = False
        config['camera_settings']['camera_id'] = camera_id
    else:
        print("🎮 Configuring simulation mode (no camera available)...")
        config['camera_settings']['simulation_mode'] = True
        config['camera_settings']['camera_id'] = 0
    
    # Optimize settings for live streaming
    config['camera_settings']['fps'] = 30
    config['camera_settings']['frame_width'] = 640
    config['camera_settings']['frame_height'] = 480
    
    # Save updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Camera configuration updated: {config_path}")
    return config

def main():
    """Main camera setup function"""
    os.chdir(Path(__file__).resolve().parent)
    
    print("🚀 Camera Live Streaming Setup")
    print("=" * 50)
    
    # Detect available cameras
    cameras = detect_cameras()
    
    if cameras:
        # Find the best working camera
        working_cameras = [c for c in cameras if c.get('working', False)]
        
        if working_cameras:
            best_camera = working_cameras[0]
            camera_id = best_camera['id']
            
            print(f"\n🎯 Selected camera {camera_id} for live streaming")
            
            # Test streaming
            if test_camera_streaming(camera_id):
                # Configure for live streaming
                config = configure_live_streaming(camera_id)
                
                print("\n✅ LIVE STREAMING CONFIGURED!")
                print(f"📹 Using camera {camera_id}")
                print(f"🎥 Resolution: {config['camera_settings']['frame_width']}x{config['camera_settings']['frame_height']}")
                print(f"📊 FPS: {config['camera_settings']['fps']}")
                
                return 0
            else:
                print("❌ Camera streaming test failed")
        else:
            print("⚠️ Cameras detected but none are working properly")
    
    # Fallback to simulation mode
    print("\n🎮 Falling back to simulation mode...")
    configure_live_streaming(None)
    
    print("\n⚠️ SIMULATION MODE CONFIGURED")
    print("💡 To use live streaming:")
    print("   1. Connect a USB camera")
    print("   2. Run this script again")
    print("   3. Restart the main application")
    
    return 1

if __name__ == "__main__":
    exit(main())