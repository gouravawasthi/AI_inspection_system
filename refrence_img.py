import cv2
import numpy as np
import os
from datetime import datetime

class ReferenceImageCapture:
    def __init__(self, base_folder='data/reference_images/elot_testing'):
        self.base_folder = base_folder
        self.faces = ['front', 'rear', 'left', 'right']
        self.reference_frames = {}
        self.masks = {}
        self.current_face = None
        
        # Otsu parameters
        self.blur_size = 3
        self.morph_size = 3
        self.morph_iterations = 1
        self.use_inverse = 1  # 1 for THRESH_BINARY_INV, 0 for THRESH_BINARY
        
        # Create folder structure
        self.setup_folders()

    def edit_mask_manual(self, face_name):
        """Allow manual editing (painting) of mask with exact preview-to-save consistency.
        
        Robustness improvements:
        - Separates edit mask from display overlay completely
        - No floating-point conversions or intermediate transforms
        - Direct pixel-perfect drawing operations
        - Validates mask before/after operations
        - Handles edge cases for coordinate systems
        """
        if face_name not in self.reference_frames:
            print(f"Error: No reference frame for {face_name}")
            return False

        ref = self.reference_frames[face_name]
        h, w = ref.shape[:2]
        
        # Initialize working mask (uint8, values: 0 or 255 only)
        if face_name in self.masks and self.masks[face_name] is not None:
            edit_mask = self.masks[face_name].copy()
            # Ensure correct dimensions and binary values
            if edit_mask.shape != (h, w):
                edit_mask = cv2.resize(edit_mask, (w, h))
            edit_mask = edit_mask.astype(np.uint8)
            edit_mask = np.where(edit_mask > 127, 255, 0).astype(np.uint8)
        else:
            edit_mask = np.zeros((h, w), dtype=np.uint8)
        
        # Keep original for comparison/reset if needed
        original_mask = edit_mask.copy()
        
        window_name = f"Manual Mask Edit - {face_name.upper()}"
        brush_size = 12
        drawing = False
        erase_mode = False
        last_point = None
        mouse_x, mouse_y = -1, -1

        def mouse_cb(event, x, y, flags, param):
            nonlocal drawing, erase_mode, last_point, edit_mask, mouse_x, mouse_y
            
            # Clamp coordinates to image bounds
            x = max(0, min(x, w - 1))
            y = max(0, min(y, h - 1))
            mouse_x, mouse_y = x, y
            
            if event == cv2.EVENT_LBUTTONDOWN:
                drawing = True
                erase_mode = False
                last_point = (x, y)
                radius = max(1, brush_size // 2)
                cv2.circle(edit_mask, (x, y), radius, 255, -1)
                
            elif event == cv2.EVENT_RBUTTONDOWN:
                drawing = True
                erase_mode = True
                last_point = (x, y)
                radius = max(1, brush_size // 2)
                cv2.circle(edit_mask, (x, y), radius, 0, -1)
                
            elif event == cv2.EVENT_MOUSEMOVE:
                if drawing and last_point is not None:
                    color = 0 if erase_mode else 255
                    thickness = brush_size
                    cv2.line(edit_mask, last_point, (x, y), color, thickness)
                    last_point = (x, y)
            
            elif event in (cv2.EVENT_LBUTTONUP, cv2.EVENT_RBUTTONUP):
                drawing = False
                last_point = None

        # Create window with exact image dimensions
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, w, h)
        cv2.setMouseCallback(window_name, mouse_cb)

        print("\n" + "="*40)
        print("MANUAL MASK EDIT MODE")
        print("="*40)
        print("Controls:")
        print("  Left-click & drag: Paint mask (white)")
        print("  Right-click & drag: Erase mask (black)")
        print("  ↑ / ↓: Increase / Decrease brush size")
        print("  R: Reset to original mask")
        print("  SPACE: Save and exit")
        print("  Q: Cancel (discard all changes)")
        print("="*40 + "\n")

        while True:
            # Create display overlay (reference image + mask visualization)
            display = ref.copy()
            
            # Apply semi-transparent mask overlay
            mask_rgb = cv2.cvtColor(edit_mask, cv2.COLOR_GRAY2BGR)
            alpha = 0.4
            display = cv2.addWeighted(display, 1.0 - alpha, mask_rgb, alpha, 0)
            
            # Draw contours of masked region for clarity
            contours, _ = cv2.findContours(edit_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                cv2.drawContours(display, contours, -1, (0, 255, 0), 2)
            
            # Draw brush cursor
            if mouse_x >= 0 and mouse_y >= 0:
                radius = max(1, brush_size // 2)
                cv2.circle(display, (mouse_x, mouse_y), radius, (0, 255, 255), 2)
            
            # Add info overlays
            cv2.putText(display, f"Brush: {brush_size} px", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(display, "L:draw  R:erase  ↑↓:size  R:reset", (10, 55),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(display, "SPACE:save  Q:cancel", (10, 75),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            cv2.imshow(window_name, display)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q') or key == 27:  # Q or ESC
                print("✗ Editing cancelled. No changes saved.")
                cv2.destroyAllWindows()
                return False
                
            elif key == ord(' '):  # SPACE - save
                # Final validation: ensure binary mask
                final_mask = np.where(edit_mask > 127, 255, 0).astype(np.uint8)
                
                # Verify it's truly binary
                assert np.all((final_mask == 0) | (final_mask == 255)), "Mask contains invalid values"
                
                self.masks[face_name] = final_mask
                
                # Calculate statistics for confirmation
                white_pixels = np.sum(final_mask == 255)
                total_pixels = h * w
                coverage = (white_pixels / total_pixels) * 100
                
                print(f"✓ Mask saved: {white_pixels} pixels ({coverage:.1f}% coverage)")
                cv2.destroyAllWindows()
                return True
                
            elif key == ord('r'):  # Reset to original
                edit_mask = original_mask.copy()
                print("↶ Reset to original mask")
                
            elif key == 82:  # Up arrow
                brush_size = min(200, brush_size + 2)
                print(f"  Brush size: {brush_size}")
                
            elif key == 84:  # Down arrow
                brush_size = max(1, brush_size - 2)
                print(f"  Brush size: {brush_size}")

    def setup_folders(self):
        """Create base folder and subfolders for each face"""
        if not os.path.exists(self.base_folder):
            os.makedirs(self.base_folder)
            print(f"Created base folder: {self.base_folder}")
        
        for face in self.faces:
            face_path = os.path.join(self.base_folder, face)
            if not os.path.exists(face_path):
                os.makedirs(face_path)
                print(f"Created folder: {face_path}")
    
    def show_menu(self):
        """Display main menu and get user choice"""
        print("\n" + "="*50)
        print("  REFERENCE IMAGE CAPTURE - SELECT FACE")
        print("="*50)
        print("1. Front Face")
        print("2. Rear Face")
        print("3. Left Face")
        print("4. Right Face")
        print("5. Capture All Faces (Sequential)")
        print("6. Exit")
        print("="*50)
        
        while True:
            choice = input("\nEnter your choice (1-6): ").strip()
            if choice in ['1', '2', '3', '4', '5', '6']:
                return choice
            print("Invalid choice. Please enter 1-6.")
    
    def capture_reference(self, face_name):
        """Capture reference frame from webcam for specific face"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Error: Cannot open webcam")
            return False
        
        print(f"\n=== CAPTURE {face_name.upper()} FACE ===")
        print("Position your object/subject for the {} view".format(face_name))
        print("Press SPACE to capture frame")
        print("Press Q to skip this face")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Cannot read frame")
                break
            
            frame = cv2.flip(frame, 1)
            
            # Add text overlay
            display_frame = frame.copy()
            cv2.putText(display_frame, f'Capturing: {face_name.upper()}', (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(display_frame, 'SPACE: Capture | Q: Skip', (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            cv2.imshow(f'Webcam - {face_name.upper()} Face', display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '):  # Space key
                self.reference_frames[face_name] = frame.copy()
                print(f"✓ {face_name.upper()} face captured!")
                break
            elif key == ord('q'):
                print(f"Skipped {face_name} face")
                cap.release()
                cv2.destroyAllWindows()
                return False
        
        cap.release()
        cv2.destroyAllWindows()
        return True
    def capture_from_video(self, video_path, face_name):
        """Capture reference frame from a video clip for a specific face."""
        if not os.path.exists(video_path):
            print(f"Error: Video file not found at {video_path}")
            return False

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("Error: Cannot open video file")
            return False

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        print(f"\n=== CAPTURE FROM VIDEO: {os.path.basename(video_path)} ===")
        print(f"Total frames: {total_frames}, FPS: {fps:.2f}")
        print("Use keys to navigate: [A] Backward | [D] Forward | [SPACE] Capture | [Q] Quit")

        frame_index = 0
        step = int(fps) if fps > 0 else 10  # skip about 1 second per step

        while True:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ret, frame = cap.read()
            if not ret:
                print("End of video reached or error reading frame.")
                break

            display_frame = frame.copy()
            cv2.putText(display_frame, f"Frame {frame_index}/{total_frames}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            cv2.putText(display_frame, "[A/D]: Navigate | SPACE: Capture | Q: Quit", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            cv2.imshow(f'Video Capture - {face_name}', display_frame)
            key = cv2.waitKey(0) & 0xFF

            if key == ord('a'):  # backward
                frame_index = max(0, frame_index - step)
            elif key == ord('d'):  # forward
                frame_index = min(total_frames - 1, frame_index + step)
            elif key == ord(' '):  # capture
                self.reference_frames[face_name] = frame.copy()
                print(f"✓ Captured frame {frame_index} for {face_name}")
                cap.release()
                cv2.destroyAllWindows()
                return True
            elif key == ord('q'):
                print("Capture cancelled.")
                break

        cap.release()
        cv2.destroyAllWindows()
        return False

    def resize_to_same_size(self, images):
        """Resize all images to same dimensions"""
        if not images:
            return images
        
        # Get max dimensions
        max_h = max(img.shape[0] for img in images)
        max_w = max(img.shape[1] for img in images)
        
        resized = []
        for img in images:
            if img.shape[0] != max_h or img.shape[1] != max_w:
                resized.append(cv2.resize(img, (max_w, max_h)))
            else:
                resized.append(img)
        return resized
    
    def on_trackbar_change(self, val):
        """Dummy callback for trackbar"""
        pass
    
    def create_mask_auto(self, face_name):
        """Create mask from reference frame using Otsu thresholding with adjustable parameters"""
        if face_name not in self.reference_frames:
            print(f"Error: No reference frame for {face_name}")
            return False
        
        reference = self.reference_frames[face_name]
        
        print(f"\n=== AUTO-CREATE MASK FOR {face_name.upper()} FACE ===")
        print("Adjust parameters using sliders to refine the mask")
        print("Press SPACE to accept current mask")
        print("Press Q to cancel")
        
        window_name = f'Mask Creation - {face_name.upper()}'
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 800, 600)
        
        # Create trackbars
        cv2.createTrackbar('Blur (odd)', window_name, self.blur_size, 21, self.on_trackbar_change)
        cv2.createTrackbar('Morph Size', window_name, self.morph_size, 15, self.on_trackbar_change)
        cv2.createTrackbar('Morph Iter', window_name, self.morph_iterations, 10, self.on_trackbar_change)
        cv2.createTrackbar('Inverse', window_name, self.use_inverse, 1, self.on_trackbar_change)
        
        while True:
            # Get trackbar values
            blur_size = cv2.getTrackbarPos('Blur (odd)', window_name)
            morph_size = cv2.getTrackbarPos('Morph Size', window_name)
            morph_iterations = cv2.getTrackbarPos('Morph Iter', window_name)
            use_inverse = cv2.getTrackbarPos('Inverse', window_name)
            
            # Ensure blur size is odd and at least 1
            if blur_size % 2 == 0:
                blur_size += 1
            blur_size = max(1, blur_size)
            
            # Ensure morph size is at least 1
            morph_size = max(1, morph_size)
            
            # Process reference frame
            gray = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
            denoised = cv2.medianBlur(gray, blur_size)
            
            # Otsu threshold
            thresh_type = cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU if use_inverse else cv2.THRESH_BINARY + cv2.THRESH_OTSU
            _, otsu_thresh = cv2.threshold(denoised, 0, 255, thresh_type)
            
            # Morphological operations
            if morph_size > 0 and morph_iterations > 0:
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (morph_size, morph_size))
                mask = cv2.morphologyEx(otsu_thresh, cv2.MORPH_OPEN, kernel, iterations=morph_iterations)
            else:
                mask = otsu_thresh
            
            # Convert mask to BGR and add overlay with contours
            mask_display = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(mask_display, contours, -1, (0, 0, 255), 2)
            
            # Add parameter info on the mask
            param_text = f'Blur:{blur_size} | Morph:{morph_size}x{morph_iterations} | Inverse:{use_inverse}'
            cv2.putText(mask_display, param_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(mask_display, 'SPACE: Accept | Q: Cancel', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            cv2.imshow(window_name, mask_display)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '): 
                self.masks[face_name] = mask
                print(f"✓ Mask for {face_name} created!")
                print(f"  Parameters: Blur={blur_size}, Morph={morph_size}x{morph_iterations}, Inverse={use_inverse}")
                cv2.destroyAllWindows()
                return True
            elif key == ord('q'):  # Cancel
                print(f"Mask creation cancelled for {face_name}")
                cv2.destroyAllWindows()
                return False
        
        cv2.destroyAllWindows()
        return False
    
    def save_images(self, face_name):
        """Save reference image and mask for specific face"""
        if face_name not in self.reference_frames:
            print(f"Error: No reference frame for {face_name}")
            return False
        face_folder = os.path.join(self.base_folder, face_name)
        ref_path = os.path.join(face_folder, f'reference_{face_name}.png')
        
        cv2.imwrite(ref_path, self.reference_frames[face_name])
        print(f"✓ Saved {face_name} reference: {ref_path}")
        
        if face_name in self.masks:
            mask_path = os.path.join(face_folder, f'mask_{face_name}.png')
            cv2.imwrite(mask_path, self.masks[face_name])
            print(f"✓ Saved {face_name} mask: {mask_path}")
        
        return True
    
    def process_face(self, face_name):
        """Complete workflow for one face"""
        print(f"\n{'='*50}")
        print(f"  PROCESSING {face_name.upper()} FACE")
        print(f"{'='*50}")
        use_video = input("Use video file instead of webcam? (y/n): ").strip().lower() == 'y'
        if use_video:
            video_path = input("Enter video file path: ").strip()
            if not self.capture_from_video(video_path, face_name):
                return False
        else:
            if not self.capture_reference(face_name):
                return False
        

       
        
    
        create_mask_choice = input(f"\nCreate mask for {face_name} face? (y/n): ").strip().lower()
        if create_mask_choice == 'y':
            
            self.create_mask_auto(face_name)
                # Step 2: Option for manual editing
        manual_edit_choice = input(f"Do you want to manually refine the mask for {face_name}? (y/n): ").strip().lower()
        if manual_edit_choice == 'y':
            self.edit_mask_manual(face_name)

        
        # Step 3: Save images
        self.save_images(face_name)
        
        return True
    
    def capture_all_faces(self):
        """Sequential capture of all four faces"""
        print("\n" + "="*50)
        print("  SEQUENTIAL CAPTURE - ALL FACES")
        print("="*50)
        print("You will capture all four faces in order:")
        print("Front → Rear → Left → Right")
        input("\nPress ENTER to start...")
        
        for face in self.faces:
            self.process_face(face)
            
            # Pause between faces (except after the last one)
            if face != self.faces[-1]:
                input(f"\nReady for next face? Press ENTER to continue...")
        
        print("\n✓ All faces captured successfully!")
    
    def run(self):
        """Main application loop"""
        print("\n" + "="*60)
        print("  REFERENCE IMAGE & MASK CREATOR FOR IMAGE RESTORATION")
        print("="*60)
        
        while True:
            choice = self.show_menu()
            
            if choice == '1':
                self.process_face('front')
            elif choice == '2':
                self.process_face('rear')
            elif choice == '3':
                self.process_face('left')
            elif choice == '4':
                self.process_face('right')
            elif choice == '5':
                self.capture_all_faces()
            elif choice == '6':
                print("\n✓ Exiting")
                break
            
            # Ask if user wants to continue
            if choice != '6':
                continue_choice = input("\nReturn to main menu? (y/n): ").strip().lower()
                if continue_choice != 'y':
                    print("\n✓ Exiting")
                    break


if __name__ == "__main__":
    # Create capture object and run
    capture = ReferenceImageCapture(base_folder='ref_img')
    capture.run()