#!/usr/bin/env python3
"""
Simple test for image padding functionality
"""

import sys
import numpy as np
import cv2
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def simple_test_padding():
    """Simple test of padding logic"""
    print("Starting simple padding test...")
    
    # Create a simple config-like object for testing
    class SimpleConfig:
        frame_width = 640
        frame_height = 480
    
    config = SimpleConfig()
    
    # Test frame (different aspect ratio)
    test_frame = np.random.randint(0, 255, (270, 480, 3), dtype=np.uint8)  # 16:9
    print(f"Original frame size: {test_frame.shape[1]}x{test_frame.shape[0]}")
    
    # Simple padding function (extracted from camera manager)
    def pad_frame(frame, target_width, target_height):
        """Pad frame to display size while maintaining aspect ratio"""
        # Get original frame dimensions
        original_height, original_width = frame.shape[:2]
        
        # Calculate scaling factor to fit within target dimensions
        scale_w = target_width / original_width
        scale_h = target_height / original_height
        scale = min(scale_w, scale_h)  # Use smaller scale to fit within bounds
        
        # Calculate new dimensions
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)
        
        # Resize frame with calculated dimensions
        resized_frame = cv2.resize(frame, (new_width, new_height))
        
        # Create padded frame with target dimensions
        padded_frame = np.zeros((target_height, target_width, 3), dtype=np.uint8)
        
        # Calculate padding offsets to center the image
        y_offset = (target_height - new_height) // 2
        x_offset = (target_width - new_width) // 2
        
        # Place resized frame in center of padded frame
        padded_frame[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized_frame
        
        return padded_frame
    
    # Apply padding
    padded_frame = pad_frame(test_frame, config.frame_width, config.frame_height)
    
    print(f"Target size: {config.frame_width}x{config.frame_height}")
    print(f"Padded frame size: {padded_frame.shape[1]}x{padded_frame.shape[0]}")
    
    # Verify dimensions
    if padded_frame.shape[1] == config.frame_width and padded_frame.shape[0] == config.frame_height:
        print("✅ Dimensions match!")
    else:
        print("❌ Dimension mismatch!")
        
    # Save test image
    cv2.imwrite("test_padding_simple.jpg", padded_frame)
    print("📷 Saved test_padding_simple.jpg")
    
    print("✅ Simple padding test completed!")

if __name__ == "__main__":
    simple_test_padding()