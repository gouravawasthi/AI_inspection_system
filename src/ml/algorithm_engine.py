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
import numpy as np

# load configuration
from config.algorithm_config import DEFAULT_ALGO_CONFIG, AlgoConfig

# optional OCR via easyocr
try:
    import easyocr
    _EASYOCR_AVAILABLE = True
    _OCR_READER = easyocr.Reader(['en'], gpu=False)
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
    def __init__(self, config: Optional[AlgoConfig] = None, debug: bool = False):
        """
        :param config: AlgoConfig instance (DEFAULT_ALGO_CONFIG used when None)
        :param debug: print debug traces on exceptions
        """
        self.debug = debug
        self.config = config if config is not None else DEFAULT_ALGO_CONFIG
        # thresholds & params
        self.diff_threshold = float(self.config.THRESHOLDS.diff_threshold)
        self.gradient_threshold = float(self.config.THRESHOLDS.gradient_threshold)
        self.plate_ratio_thresh = float(self.config.THRESHOLDS.plate_ratio_thresh)
        self.screw_ratio_thresh = float(self.config.THRESHOLDS.screw_ratio_thresh)
        # Hough params (use None for maxRadius to compute from ROI)
        self.hough_cfg = self.config.HOUGH
        # Registration params
        self.reg_cfg = self.config.REG
        # ORB: build with config values
        orb_cfg = self.config.ORB
        self._orb = cv2.ORB_create(nfeatures=int(orb_cfg.nfeatures),
                                   scaleFactor=float(orb_cfg.scaleFactor),
                                   nlevels=int(orb_cfg.nlevels),
                                   edgeThreshold=int(orb_cfg.edgeThreshold),
                                   firstLevel=int(orb_cfg.firstLevel),
                                   WTA_K=int(orb_cfg.WTA_K),
                                   scoreType=int(orb_cfg.scoreType),
                                   patchSize=int(orb_cfg.patchSize))
        self._bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        # storage
        self.references: Dict[str, np.ndarray] = {}
        self.masks: Dict[str, np.ndarray] = {}
        # ensure default paths resolved
        self.config.resolve_data_paths()

    # -------------------------
    # Reference / mask loading
    # -------------------------
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

    def load_defaults_from_data(self, data_root: Optional[str] = None) -> Dict[str, Any]:
        """Convenience: attempt to load references & masks using config.PATHS defaults."""
        data_root = data_root or self.config.PATHS.data_root
        summary = {'loaded_refs': [], 'loaded_masks': [], 'missing': []}
        p = self.config.PATHS

        # inline
        candidates = [
            ('inline_top', getattr(p, 'inline_top_ref', None)),
            ('inline_bottom', getattr(p, 'inline_bottom_ref', None))
        ]
        for key, path in candidates:
            if path and os.path.isfile(path):
                if self.load_reference(key, path):
                    summary['loaded_refs'].append((key, path))
            else:
                summary['missing'].append((key, path))

        # elot sides
        sides = ['front', 'rear', 'left', 'right']
        for s in sides:
            rpath = getattr(p, f'elot_{s}_ref', None) or getattr(p, f'elot_{s}_reference', None)
            mpath = getattr(p, f'elot_{s}_mask', None)
            keyr = f'elot_{s}'
            keym = f'elot_{s}_mask'
            if rpath and os.path.isfile(rpath):
                if self.load_reference(keyr, rpath):
                    summary['loaded_refs'].append((keyr, rpath))
            else:
                summary['missing'].append((keyr, rpath))
            if mpath and os.path.isfile(mpath):
                if self.load_mask(keym, mpath):
                    summary['loaded_masks'].append((keym, mpath))
            else:
                summary['missing'].append((keym, mpath))

        return summary

    # -------------------------
    # Modular detection helpers
    # -------------------------
    def _register(self, ref: np.ndarray, frame: np.ndarray) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Register frame to ref (ref coordinate). Returns warped frame sized to ref and homography or None."""
        try:
            ref_gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            k1, d1 = self._orb.detectAndCompute(ref_gray, None)
            k2, d2 = self._orb.detectAndCompute(frame_gray, None)
            if d1 is None or d2 is None or len(d1) < self.reg_cfg.min_match_count or len(d2) < self.reg_cfg.min_match_count:
                # fallback: resize
                warped = cv2.resize(frame, (ref.shape[1], ref.shape[0]))
                return warped, None
            matches = self._bf.match(d1, d2)
            matches = sorted(matches, key=lambda x: x.distance)
            if len(matches) < self.reg_cfg.min_match_count:
                warped = cv2.resize(frame, (ref.shape[1], ref.shape[0]))
                return warped, None
            src_pts = np.float32([k1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([k2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
            H, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, self.reg_cfg.ransac_thresh)
            if H is None:
                warped = cv2.resize(frame, (ref.shape[1], ref.shape[0]))
                return warped, None
            warped = cv2.warpPerspective(frame, H, (ref.shape[1], ref.shape[0]))
            return warped, H
        except Exception as e:
            if self.debug:
                print("register error:", e)
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
        dp = dp or self.hough_cfg.dp
        minDist = minDist or self.hough_cfg.minDist
        param1 = param1 or self.hough_cfg.param1
        param2 = param2 or self.hough_cfg.param2
        minRadius = minRadius or self.hough_cfg.minRadius

        if maxRadius is None:
            maxRadius = self.hough_cfg.maxRadius or int(min(img.shape[:2]) / 2)

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
                res = _OCR_READER.readtext(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                return bool(res and len(res) > 0)
           
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
                rois: Optional[Dict[str, Tuple[int,int,int,int]]] = None
                ) -> Dict[str, Any]:
        """
        Single-frame processing. Returns OrderedDict with keys:
        ['original_frame', 'processed_annotated', 'status', 'results']
        """
        original = np.array(frame, copy=True)
        annotated = original.copy()
        status = _InternalStatus(0, "OK")
        results: Dict[str, int] = {}

        try:
            if mode.lower() == 'elot':
                # single side processing
                if not side:
                    status = _InternalStatus(1, "EOLT requires 'side' parameter")
                    return self._make_output(original, annotated, status, results)
                side_key = side.lower()
                if side_key not in ('front','rear','left','right'):
                    status = _InternalStatus(1, f"EOLT invalid side '{side}'")
                    return self._make_output(original, annotated, status, results)
                # determine ref key
                ref_key_for_side = ref or (views.get(side_key) if views else None)
                if not ref_key_for_side:
                    status = _InternalStatus(1, f"EOLT missing reference for side '{side_key}'")
                    return self._make_output(original, annotated, status, results)
                if ref_key_for_side not in self.references:
                    status = _InternalStatus(1, f"EOLT reference '{ref_key_for_side}' not loaded")
                    return self._make_output(original, annotated, status, results)
                # determine mask key
                mask_key_for_side = mask or (masks_map.get(side_key) if masks_map else None)
                if mask_key_for_side and mask_key_for_side not in self.masks:
                    status = _InternalStatus(1, f"EOLT mask '{mask_key_for_side}' not loaded")
                    return self._make_output(original, annotated, status, results)

                ref_img = self.references[ref_key_for_side]
                warped, H = self._register(ref_img, original)
                mask_arr = self.masks.get(mask_key_for_side) if mask_key_for_side else None
                mad, vis = self.compare_gradient_diff(ref_img, warped, mask_arr)
                normalized = mad / 255.0
                passed = int(normalized <= self.diff_threshold)
                # annotate
                if mask_arr is not None:
                    bbox = self._mask_bbox(mask_arr)
                    if bbox:
                        x,y,w,h = bbox
                        color = (0,255,0) if passed else (0,0,255)
                        cv2.rectangle(annotated, (x,y), (x+w,y+h), color, 2)
                        cv2.putText(annotated, f"{side_key}:{'PASS' if passed else 'FAIL'}", (x,y-6),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                else:
                    cv2.putText(annotated, f"{side_key}:{'PASS' if passed else 'FAIL'}", (10,30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0) if passed else (0,0,255), 2)
                processed = self._make_side_by_side(warped, vis)
                results[side_key] = passed
                status = _InternalStatus(0, f"EOLT side '{side_key}' processed")
                return self._make_output(original, processed, status, results)

            elif mode.lower() == 'inline':
                if submode not in ('top','bottom'):
                    status = _InternalStatus(1, "INLINE requires submode 'top' or 'bottom'")
                    return self._make_output(original, annotated, status, results)
                if not ref or ref not in self.references:
                    status = _InternalStatus(1, f"INLINE missing reference '{ref}'")
                    return self._make_output(original, annotated, status, results)

                ref_img = self.references[ref]
                warped, H = self._register(ref_img, original)
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

                # bottom
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
                    ocr_present = 1 if self.detect_text_presence(crop) else 0
                    circles = self.detect_circles(crop, maxRadius=int(min(crop.shape[:2])/2))
                    circle_detected = 1 if len(circles) > 0 else 0
                    speaker_present = 1 if (ocr_present or circle_detected) else 0
                    color = (0,255,0) if speaker_present else (0,0,255)
                    x,y,w,h = speaker_roi
                    cv2.rectangle(annotated, (x,y), (x+w,y+h), color, 2)
                    if speaker_present:
                        cv2.putText(annotated, "speaker", (x,y-6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    if circles:
                        for (cx,cy,r) in circles:
                            cv2.circle(annotated, (x+cx, y+cy), r, (0,255,0), 2)

                if capacitor_roi is not None:
                    crop = crop_roi(warped, capacitor_roi)
                    capacitor_present = 1 if self.detect_text_presence(crop) else 0
                    color = (0,255,0) if capacitor_present else (0,0,255)
                    x,y,w,h = capacitor_roi
                    cv2.rectangle(annotated, (x,y), (x+w,y+h), color, 2)
                    if capacitor_present:
                        cv2.putText(annotated, "capacitor", (x,y-6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                if plate_roi is not None:
                    crop = crop_roi(warped, plate_roi)
                    plate_det, ratio = self.detect_gradient_presence(crop)
                    lap = cv2.Laplacian(cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY), cv2.CV_32F)
                    screw_px = (np.abs(lap) > (self.gradient_threshold/2)).sum()
                    screw_det = 1 if (screw_px / lap.size) > self.screw_ratio_thresh else 0
                    color = (0,255,0) if (plate_det and screw_det) else (0,0,255)
                    x,y,w,h = plate_roi
                    cv2.rectangle(annotated, (x,y), (x+w,y+h), color, 2)
                    cv2.putText(annotated, f"plate:{int(plate_det)} screw:{int(screw_det)}", (x,y-6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

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