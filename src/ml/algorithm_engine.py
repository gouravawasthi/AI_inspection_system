"""
AlgorithmEngine - single-frame algorithm module for EOLT and INLINE processing.
Now consumes central configuration (src/config/algorithm_config.py) for all tunables.

Usage:
  from image_processing.algorithm_engine import AlgorithmEngine, DEFAULT_ALGO_CONFIG
  engine = AlgorithmEngine()            # uses DEFAULT_ALGO_CONFIG
  engine.load_reference('inline_top', '/path/to/ref.jpg')
  out = engine.process(frame, mode='inline', submode='top', ref='inline_top', rois={...})
"""

from collections import OrderedDict
from typing import Dict, Optional, Tuple, Any, List
from dataclasses import dataclass
from datetime import datetime
import os
import cv2
from pathlib import Path
import numpy as np
import json

# load configuration
def load_algo_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load algorithm configuration from JSON file."""
    if config_path is None:
        # Try to find configs/algo.json relative to project root
        proj_root = Path(__file__).resolve().parents[2]
        config_path = proj_root / "configs" / "algo.json"
    
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return json.load(f)

# optional OCR via easyocr
try:
    import easyocr
    _EASYOCR_AVAILABLE = True
    _OCR_READER = easyocr.Reader(['en'])
except Exception:
    _EASYOCR_AVAILABLE = False
    _OCR_READER = None

# -------------------------
# Internal status dataclass
# -------------------------
@dataclass
class _InternalStatus:
    code: int
    message: str

# -------------------------
# Algorithm engine
# -------------------------
class AlgorithmEngine:
    def __init__(self, config_path = "configs/algo.json", debug: bool = False):
        """
        :param config: AlgoConfig instance (DEFAULT_ALGO_CONFIG used when None)
        :param debug: print debug traces on exceptions
        """
        self.debug = debug
        self.config = load_algo_config(config_path)
        
        # thresholds & params
        thresholds = self.config.get("THRESHOLDS", {})
        self.diff_threshold = float(thresholds.get("diff_threshold", 0.05))
        self.gradient_threshold = float(thresholds.get("gradient_threshold", 30))
        self.plate_ratio_thresh = float(thresholds.get("plate_ratio_thresh", 0.01))
        self.screw_ratio_thresh = float(thresholds.get("screw_ratio_thresh", 0.01))

        # Hough params
        self.hough_cfg = self.config.get("HOUGH", {})

        # Registration params
        self.reg_cfg = self.config.get("REG", {})

        # ORB configuration
        self._orb = {}
        orb_sides_cfg = self.config.get("ORB_SIDES", {})

        for side, params in orb_sides_cfg.items():
            self._orb[side] = cv2.ORB_create(
                nfeatures=int(params.get("nfeatures", 1000)),
                scaleFactor=float(params.get("scaleFactor", 1.2)),
                nlevels=int(params.get("nlevels", 8)),
                edgeThreshold=int(params.get("edgeThreshold", 31)),
                firstLevel=int(params.get("firstLevel", 0)),
                WTA_K=int(params.get("WTA_K", 2)),
                scoreType=int(params.get("scoreType", 0)),
                patchSize=int(params.get("patchSize", 31)),
                fastThreshold=int(params.get("fastThreshold", 20))
            )
        

        # Matcher
        self._bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

        # Storage
        self.references: Dict[str, np.ndarray] = {}
        self.masks: Dict[str, np.ndarray] = {}

        self.load_all_defaults()
        

    # -------------------------
    # Reference / mask loading
    # -------------------------
   
    def load_all_defaults(self) -> Dict[str, bool]:
        """
        Load all default references and masks from config PATHS.
        Uses keys defined under "PATHS" in the JSON configuration.

        Returns:
            dict: Load status for each entry (True/False)
        """
        results = {}
        paths = self.config.get("PATHS", {})

        if self.debug:
            print("Loading defaults from config PATHS:")

        for key, path in paths.items():
            full_path = Path(path).resolve()

            # Identify if it's a mask or reference based on filename
            if "mask" in key.lower():
                success = self.load_mask(key, str(full_path))
                if self.debug:
                    print(f"  {'✓' if success else '✗'} mask {key}: {full_path}")
            else:
                success = self.load_reference(key, str(full_path))
                if self.debug:
                    print(f"  {'✓' if success else '✗'} reference {key}: {full_path}")

            results[key] = success

        if self.debug:
            loaded_count = sum(1 for v in results.values() if v)
            print(f"Load summary: {loaded_count}/{len(results)} loaded")

        return results

    def load_reference(self, name: str, source: Any) -> bool:
        """Load reference from file path or numpy array."""
        img = None
        if isinstance(source, str):
            if not os.path.isfile(source):
                return False
            img = cv2.imread(source, cv2.IMREAD_COLOR)
        else:
            img = np.array(source, copy=True)
        if img is None:
            return False
        self.references[name] = img.copy()
        return True

    def load_mask(self, name: str, source: Any) -> bool:
        """Load mask from file path or numpy array. Stored as binary uint8."""
        m = None
        if isinstance(source, str):
            if not os.path.isfile(source):
                return False
            m = cv2.imread(source, cv2.IMREAD_GRAYSCALE)
        else:
            m = np.array(source, copy=True)
            if m.ndim == 3:
                m = cv2.cvtColor(m, cv2.COLOR_BGR2GRAY)
        if m is None:
            return False
        _, mb = cv2.threshold(m, 10, 255, cv2.THRESH_BINARY)
        self.masks[name] = mb.astype(np.uint8)
        return True

   
    # -------------------------
    # Modular detection helpers
    # -------------------------
    def _register(self, side: str, frame: np.ndarray) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Register 'frame' to reference image of 'side' using ORB + RANSAC.
        Returns: (warped_frame, homography or None)
        """
        try:
            ref = self.references.get(f"{side}_ref")
            if ref is None:
                raise ValueError(f"Reference for '{side}' not found.")

            # --- Step 1: Preprocess (Histogram Equalization + Blurring) ---
            ref_eq = self.equalize_histogram_color(ref)
            frame_eq = self.equalize_histogram_color(frame)
            ref_gray = cv2.cvtColor(ref_eq, cv2.COLOR_BGR2GRAY)
            frame_gray = cv2.cvtColor(frame_eq, cv2.COLOR_BGR2GRAY)

            # Gentle smoothing reduces ORB noise
            ref_gray = cv2.GaussianBlur(ref_gray, (3, 3), 0)
            frame_gray = cv2.GaussianBlur(frame_gray, (3, 3), 0)

            # --- Step 2: Detect and compute ORB features ---
            orb = self._orb.get(side, self._orb.get("default"))
            k1, d1 = orb.detectAndCompute(ref_gray, None)
            k2, d2 = orb.detectAndCompute(frame_gray, None)

            if d1 is None or d2 is None or len(d1) < 15 or len(d2) < 15:
                if self.debug:
                    print(f"[WARN] Not enough features for side '{side}'.")
                return cv2.resize(frame, (ref.shape[1], ref.shape[0])), None

            # --- Step 3: Match descriptors with BFMatcher + filtering ---
            matches = self._bf.match(d1, d2)
            matches = sorted(matches, key=lambda x: x.distance)

            # Filter out poor matches using distance ratio test
            good_matches = [m for m in matches if m.distance < 0.75 * matches[-1].distance]

            if len(good_matches) < self.reg_cfg.get("min_match_count", 30):
                if self.debug:
                    print(f"[WARN] Only {len(good_matches)} good matches for '{side}'.")
                return cv2.resize(frame, (ref.shape[1], ref.shape[0])), None

            # --- Step 4: Build keypoint correspondence arrays ---
            src_pts = np.float32([k1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([k2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

            # --- Step 5: Estimate homography using RANSAC ---
            H, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, self.reg_cfg.get("ransac_thresh", 5.0))

            if H is None or np.linalg.cond(H) > 1e6:
                if self.debug:
                    print(f"[WARN] Homography unstable for '{side}' (bad conditioning).")
                return cv2.resize(frame, (ref.shape[1], ref.shape[0])), None

            # --- Step 6: Warp current frame to reference coordinates ---
            warped = cv2.warpPerspective(frame, H, (ref.shape[1], ref.shape[0]),
                                        flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP,
                                        borderMode=cv2.BORDER_REFLECT)

            # Optional: visualize registration quality in debug mode
            if self.debug:
                overlay = cv2.addWeighted(ref, 0.5, warped, 0.5, 0)
                print(f"[INFO] Registered '{side}' — good matches: {len(good_matches)}")
                

            return warped, H

        except Exception as e:
            if self.debug:
                print(f"[ERROR] register error for '{side}':", e)
            warped = cv2.resize(frame, (ref.shape[1], ref.shape[0])) if ref is not None else frame.copy()
            return warped, None


    def _sobel_mag(self, gray: np.ndarray) -> np.ndarray:
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        mag = cv2.magnitude(gx, gy)
        return mag

    def _masked_mean_abs_diff(self, a: np.ndarray, b: np.ndarray, mask: Optional[np.ndarray]) -> float:
        diff = np.abs(a.astype(np.float32) - b.astype(np.float32))
        if mask is None:
            return float(np.mean(diff))
        mask_bool = mask > 0
        if mask_bool.sum() == 0:
            return float(np.mean(diff))
        return float(np.mean(diff[mask_bool]))

    def _mask_bbox(self, mask: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        big = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(big)
        return (x, y, w, h)

    def _make_side_by_side(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        h = left.shape[0]
        right_resized = cv2.resize(right, (left.shape[1], h))
        sep = np.full((h, 2, 3), 255, dtype=np.uint8)
        return np.hstack([left, sep, right_resized])
    
    def detect_circles(self, img: np.ndarray,
                       dp: Optional[float] = None, minDist: Optional[int] = None,
                       param1: Optional[int] = None, param2: Optional[int] = None,
                       minRadius: Optional[int] = None, maxRadius: Optional[int] = None) -> List[Tuple[int,int,int]]:
        """Circle detection (Hough) using config defaults where arguments are None.

        Simpler filtering: accept Hough detections only if local contour has reasonable
        circularity and area coverage compared to the ideal circle. This rejects
        strongly elliptical / non-round shapes with minimal computation.
        """
        dp = dp or self.hough_cfg.get("dp", 1.2)
        minDist = minDist or self.hough_cfg.get("minDist", 20)
        param1 = param1 or self.hough_cfg.get("param1", 100)
        param2 = param2 or self.hough_cfg.get("param2", 30)
        minRadius = minRadius or self.hough_cfg.get("minRadius", 5)

        if maxRadius is None:
            maxRadius = self.hough_cfg.get("maxRadius", int(min(img.shape[:2]) / 2))

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 5)
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=dp, minDist=minDist,
                                   param1=param1, param2=param2,
                                   minRadius=minRadius, maxRadius=maxRadius)
        if circles is None:
            return []
        

        circles = np.uint16(np.around(circles))
        filtered: List[Tuple[int,int,int]] = []
        for (cx, cy, r) in circles[0, :]:
            # crop small patch around detection for quick contour check
            pad = max(5, int(r * 1.2))
            x0 = max(0, int(cx - pad)); y0 = max(0, int(cy - pad))
            x1 = min(img.shape[1], int(cx + pad)); y1 = min(img.shape[0], int(cy + pad))
            patch = gray[y0:y1, x0:x1]
            if patch.size == 0:
                continue

            edges = cv2.Canny(patch, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                continue
            largest = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest)
            perimeter = cv2.arcLength(largest, True)
            if perimeter <= 0:
                continue

            # circularity: 1.0 for perfect circle
            circularity = (4.0 * np.pi * area) / (perimeter * perimeter + 1e-12)
            # compare contour area to ideal circle area
            ideal_area = np.pi * (r ** 2)
            area_ratio = area / (ideal_area + 1e-12)

            # simple acceptance thresholds (tunable in config later)
            if circularity >= 0.65 and area_ratio >= 0.30:
                filtered.append((int(cx), int(cy), int(r)))

        return filtered

    def detect_text_presence(self, img: np.ndarray) -> bool:
        """Detect whether text-like content exists in ROI. Uses EasyOCR if available else heuristic."""
        try:
            if _EASYOCR_AVAILABLE and _OCR_READER is not None:
                res = _OCR_READER.readtext(img)
                return bool(len(res) > 0)
           
        except Exception:
            return False

    def detect_gradient_presence(self, img: np.ndarray, threshold: Optional[float] = None, ratio_thresh: Optional[float] = None) -> Tuple[bool, float]:
        """Detect strong Sobel gradients in ROI (metal/plate presence)."""
        threshold = threshold if threshold is not None else self.gradient_threshold
        ratio_thresh = ratio_thresh if ratio_thresh is not None else self.plate_ratio_thresh
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mag = self._sobel_mag(gray)
        strong_px = (mag > threshold).sum()
        total_px = mag.size
        strong_ratio = float(strong_px) / float(total_px) if total_px > 0 else 0.0
        present = strong_ratio > ratio_thresh
        return present, strong_ratio

    def compare_gradient_diff(self, ref: np.ndarray, cur: np.ndarray, mask: Optional[np.ndarray] = None) -> Tuple[float, np.ndarray]:
        """Compare Sobel gradients between ref and current, return MAD and visual map."""
        ref_gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
        cur_gray = cv2.cvtColor(cur, cv2.COLOR_BGR2GRAY)
        ref_mag = self._sobel_mag(ref_gray)
        cur_mag = self._sobel_mag(cur_gray)
        if mask is not None and mask.shape != ref_gray.shape:
            mask = cv2.resize(mask, (ref_gray.shape[1], ref_gray.shape[0]))
        mad = self._masked_mean_abs_diff(ref_mag, cur_mag, mask)
        diff = np.abs(ref_mag - cur_mag)
        d = np.clip((diff / (diff.max() + 1e-6)) * 255.0, 0, 255).astype(np.uint8)
        vis = cv2.applyColorMap(d, cv2.COLORMAP_JET)
        if mask is not None:
            vis[mask == 0] = 0
        return float(mad), vis
    def equalize_histogram_color(self,img):
        """
        Apply histogram equalization on a color image using YCrCb luminance channel.
        """
        if img is None or img.size == 0:
            raise ValueError("Empty image for histogram equalization.")

        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])  # Equalize Y (luminance)
        equalized = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
        return equalized


    def inspect_image(self, new_img, position_hint,side):
        """
        Compare new image with gold standard inside ROI after registration + histogram equalization.
        """
        try:
            # --- Step 0: Validate inputs ---
            # references/masks are stored with keys like '<side>_ref' and '<side>_mask'
            gold_img=self.references.get(f"{side}_ref")
            gold_mask=self.masks.get(f"{side}_mask")
            if gold_img is None or new_img is None or gold_mask is None:
                return {"Status": 0, "Message": "One or more input images are missing."}

            # --- Step (a) Histogram Equalization (Preprocessing) ---
            gold_img_eq = self.equalize_histogram_color(gold_img)
            new_img_eq = self.equalize_histogram_color(new_img)

            # --- Step (b) Register new image with gold image ---
            gray_gold = cv2.cvtColor(gold_img_eq, cv2.COLOR_BGR2GRAY)
            gray_new = cv2.cvtColor(new_img_eq, cv2.COLOR_BGR2GRAY)

            
            kp1, des1 = self._orb[side].detectAndCompute(gray_gold, None)
            kp2, des2 = self._orb[side].detectAndCompute(gray_new, None)

            if des1 is None or des2 is None:
                return {"Status": 0, "Message": f"Please keep the inspection object in {position_hint}"}

            
            matches = self._bf.match(des1, des2)
            matches = sorted(matches, key=lambda x: x.distance)

            if len(matches) < 100:
                return {"Status": 0, "Message": f"Not enough feature matches — adjust position: {position_hint}"}

            src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

            H, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)
            if H is None:
                return {"Status": 0, "Message": f"Registration failed — please keep the object in {position_hint}"}

            h, w = gray_gold.shape
            aligned_new = cv2.warpPerspective(new_img_eq, H, (w, h))

            # --- Step (c) Apply ROI mask ---
            roi_new = cv2.bitwise_and(aligned_new, aligned_new, mask=gold_mask)
            roi_gold = cv2.bitwise_and(gold_img_eq, gold_img_eq, mask=gold_mask)

            # --- Step (d) Gradient comparison ---
            def get_edges(img):
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
                blurred = cv2.GaussianBlur(gray, (3, 3), 0)
                edges = cv2.Canny(blurred, 50, 150)
                return edges

            edges_gold = get_edges(roi_gold)
            edges_new = get_edges(roi_new)

            # --- Step (e) Identify differences ---
            only_new = cv2.subtract(edges_new, edges_gold)
            only_gold = cv2.subtract(edges_gold, edges_new)
            common = cv2.bitwise_and(edges_gold, edges_new)

            result = np.zeros_like(gold_img)
            result[common > 0] = (255, 255, 255)  # white = matched edges
            result[only_new > 0] = (0, 0, 255)    # red = new edges
            result[only_gold > 0] = (255, 0, 0)   # blue = missing edges

            result = cv2.bitwise_and(result, result, mask=gold_mask)

            return {
                "Status": 1,
                "Message": "Inspection completed successfully (with histogram equalization)",
                "OutputImage": result
            }

        except Exception as e:
            return {"Status": 0, "Message": f"Exception: {str(e)}"}

    # -------------------------
    # Processing entrypoint
    # -------------------------
  

    def process(self, frame: np.ndarray, mode: str,
                # EOLT params (single side)
                side: Optional[str] = None,
                ref: Optional[str] = None,
                mask: Optional[str] = None,
                views: Optional[Dict[str, str]] = None,
                masks_map: Optional[Dict[str, str]] = None,
                # INLINE params
                submode: Optional[str] = None,
                rois: Optional[Dict[str, Tuple[int, int, int, int]]] = None
                ) -> Dict[str, Any]:
        """
        Single-frame processing. Returns OrderedDict with keys:
        ['original_frame', 'processed_annotated', 'status', 'results']
        """
        rois = self.config.get("ROIS",{})
        original = np.array(frame, copy=True)
        annotated = original.copy()
        status = _InternalStatus(0, "OK")
        results: Dict[str, int] = {}

        try:
            # EOLT processing (note: external callers use 'eolt')
            if mode.lower() == 'eolt':
                # ---- Input validation ----
                if not side:
                    status = _InternalStatus(1, "EOLT requires 'side' parameter")
                    return self._make_output(original, annotated, status, results)
                side_key = side.lower()
               
                if side_key not in ('front', 'rear', 'left', 'right'):
                    status = _InternalStatus(1, f"EOLT invalid side '{side}'")
                    return self._make_output(original, annotated, status, results)

                # ---- Reference + Mask selection ----
                ref_key_for_side = ref or (views.get(side_key) if views else None)
                if not ref_key_for_side:
                    status = _InternalStatus(1, f"EOLT missing reference for side '{side_key}'")
                    return self._make_output(original, annotated, status, results)
                if ref_key_for_side not in self.references:
                    status = _InternalStatus(1, f"EOLT reference '{ref_key_for_side}' not loaded")
                    return self._make_output(original, annotated, status, results)

                mask_key_for_side = mask or (masks_map.get(side_key) if masks_map else None)
                if mask_key_for_side and mask_key_for_side not in self.masks:
                    status = _InternalStatus(1, f"EOLT mask '{mask_key_for_side}' not loaded")
                    return self._make_output(original, annotated, status, results)

                # reference and mask are loaded from self.references/self.masks inside inspect_image
                ref_img = self.references[ref_key_for_side]
                mask_arr = self.masks.get(mask_key_for_side) if mask_key_for_side else None

                # ---- Gold vs Reference comparison ----
                # inspect_image expects (new_img, position_hint, side)
                # pass the captured frame as new_img and use side_key as the position_hint
                result = self.inspect_image(original, side_key, side_key)

                if result["Status"] == 0:
                    status = _InternalStatus(1, result["Message"])
                    return self._make_output(original, annotated, status, results)

                vis = result["OutputImage"]

                # ---- Compute difference metric ----
                red_pixels = np.sum(np.all(vis == (0, 0, 255), axis=-1))
                white_pixels = np.sum(np.all(vis == (255, 255, 255), axis=-1))
                total = red_pixels + white_pixels + 1e-6
                diff_ratio = red_pixels / total

                passed = int(diff_ratio <= self.diff_threshold)

                # ---- Annotation ----
                color = (0, 255, 0) if passed else (0, 0, 255)
                if mask_arr is not None:
                    bbox = self._mask_bbox(mask_arr)
                    if bbox:
                        x, y, w, h = bbox
                        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
                        cv2.putText(annotated, f"{side_key}:{'PASS' if passed else 'FAIL'}", (x, y - 6),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                else:
                    cv2.putText(annotated, f"{side_key}:{'PASS' if passed else 'FAIL'}", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

                # ---- Prepare final output ----
                processed = self._make_side_by_side(original, vis)
                results[side_key] = passed
                status = _InternalStatus(0, f"EOLT side '{side_key}' processed via goldvsref")

                return self._make_output(original, processed, status, results)
            
            elif mode.lower() == 'inline':
                
                if submode not in ('top','bottom'):
                    status = _InternalStatus(1, "INLINE requires submode 'top' or 'bottom'")
                    return self._make_output(original, annotated, status, results)
                if not ref or ref not in self.references:
                    status = _InternalStatus(1, f"INLINE missing reference '{ref}'")
                    return self._make_output(original, annotated, status, results)
                
                
                warped, H = self._register(submode,original)
                annotated = warped.copy()

                def crop_roi(img, r):
                    x,y,w,h = r
                    x,y,w,h = int(x), int(y), int(w), int(h)
                    return img[y:y+h, x:x+w]

                if submode == 'top':
                    plate_roi = rois.get('plate') if rois else None
                    if plate_roi is None:
                        status = _InternalStatus(1, "INLINE top missing 'plate' ROI")
                        return self._make_output(original, annotated, status, results)
                    crop = crop_roi(warped, plate_roi)
                    plate_present, ratio = self.detect_gradient_presence(crop)
                    screw_present = int(plate_present)
                    color = (0,255,0) if plate_present else (0,0,255)
                    x,y,w,h = plate_roi
                    cv2.rectangle(annotated, (x,y), (x+w,y+h), color, 2)
                    cv2.putText(annotated, f"plate:{int(plate_present)} screw:{int(screw_present)}", (x,y-6),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    results = {'plate': int(plate_present), 'screw': int(screw_present)}
                    status = _InternalStatus(0, "INLINE top processed")
                    processed = self._make_side_by_side(warped, annotated)
                    return self._make_output(original, processed, status, results)

                elif submode == 'bottom':
                    antenna_roi = rois.get('antenna') if rois else None
                    speaker_roi = rois.get('speaker') if rois else None
                    plate_roi = rois.get('plate') if rois else None
                    capacitor_roi = rois.get('capacitor') if rois else None

                    antenna_present = 0
                    speaker_present = 0
                    capacitor_present = 0

                    if antenna_roi is not None:
                        crop = crop_roi(warped, antenna_roi)
                        antenna_present = 1 if self.detect_text_presence(crop) else 0
                        color = (0,255,0) if antenna_present else (0,0,255)
                        x,y,w,h = antenna_roi
                        cv2.rectangle(annotated, (x,y), (x+w,y+h), color, 2)
                        if antenna_present:
                            cv2.putText(annotated, "antenna", (x,y-6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                    if speaker_roi is not None:
                        crop = crop_roi(warped, speaker_roi)
                        circles = self.detect_circles(crop)
                        circle_detected = 1 if len(circles) > 0 else 0
                        speaker_present = 1 if circle_detected else 0
                        color = (0,255,0) if speaker_present else (0,0,255)
                        x,y,w,h = speaker_roi
                        cv2.rectangle(annotated, (x,y), (x+w,y+h), color, 2)
                        if speaker_present:
                            cv2.putText(annotated, "speaker", (x,y-6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                        

                    if capacitor_roi is not None:
                        crop = crop_roi(warped, capacitor_roi)
                        capacitor_present = 1 if self.detect_text_presence(crop) else 0
                        color = (0,255,0) if capacitor_present else (0,0,255)
                        x,y,w,h = capacitor_roi
                        cv2.rectangle(annotated, (x,y), (x+w,y+h), color, 2)
                        if capacitor_present:
                            cv2.putText(annotated, "capacitor", (x,y-6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            
                results = {
                    'antenna_present': int(antenna_present),
                    'speaker_present': int(speaker_present),
                    'capacitor': int(capacitor_present)
                }
                status = _InternalStatus(0, "INLINE bottom processed")
                processed = self._make_side_by_side(warped, annotated)
                return self._make_output(original, processed, status, results)

            else:
                status = _InternalStatus(1, f"Unknown mode '{mode}'")
                return self._make_output(original, annotated, status, results)

        except Exception as e:
            if self.debug:
                import traceback
                traceback.print_exc()
            status = _InternalStatus(1, f"Processing failure: {str(e)}")
            return self._make_output(original, annotated, status, results)

    # -------------------------
    # Output helper (ensures key order)
    # -------------------------
    def _make_output(self, original: np.ndarray, annotated: np.ndarray,
                     status: _InternalStatus, results: Dict[str, int]) -> Dict[str, Any]:
        out = OrderedDict()
        out['original_frame'] = original
        out['processed_annotated'] = annotated
        out['status'] = {'status_code': int(status.code), 'message': str(status.message)}
        out['results'] = results
        return out