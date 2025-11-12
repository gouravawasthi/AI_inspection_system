#!/usr/bin/env python3
"""
Test script to verify image padding functionality
Tests the camera manager's new padding feature
"""

import sys
import numpy as np
import cv2
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from camera.camera_manager import CameraManager
from config import config_manager

def test_padding_functionality():
    """Test the new padding functionality"""
    print("Testing image padding functionality...")
    
    # Load camera config
    config = config_manager.load_config()
    camera_manager = CameraManager(config)
    
    # Create test frames with different aspect ratios
    test_frames = {
        "landscape_16_9": np.random.randint(0, 255, (270, 480, 3), dtype=np.uint8),  # 16:9
        "portrait_9_16": np.random.randint(0, 255, (480, 270, 3), dtype=np.uint8),   # 9:16  
        "square_1_1": np.random.randint(0, 255, (400, 400, 3), dtype=np.uint8),      # 1:1
        "wide_21_9": np.random.randint(0, 255, (200, 467, 3), dtype=np.uint8),       # 21:9
    }
    
    # Test each frame type
    for name, frame in test_frames.items():
        print(f"\nTesting {name} frame:")
        print(f"  Original size: {frame.shape[1]}x{frame.shape[0]}")
        
        # Apply padding
        padded_frame = camera_manager._pad_frame_to_display_size(frame)
        print(f"  Padded size: {padded_frame.shape[1]}x{padded_frame.shape[0]}")
        
        # Verify dimensions match config
        expected_width = camera_manager.config.frame_width
        expected_height = camera_manager.config.frame_height
        
        assert padded_frame.shape[1] == expected_width, f"Width mismatch: {padded_frame.shape[1]} != {expected_width}"
        assert padded_frame.shape[0] == expected_height, f"Height mismatch: {padded_frame.shape[0]} != {expected_height}"