"""
Algorithm configuration centralization.

Usage:
    from config.algorithm_config import AlgoConfig
    cfg = AlgoConfig()
    cfg.REGISTRATION      -> registration / ORB params
    cfg.HOUGH             -> hough/circle params
    cfg.THRESHOLDS        -> gradient / diff thresholds
    cfg.PATHS             -> default reference & mask paths (resolved to Data/)
    cfg.ROIS              -> default ROIs (dict of names -> (x,y,w,h))
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, Tuple, Optional, Any
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_ROOT = os.path.join(PROJECT_ROOT, 'Data')

@dataclass
class ORBConfig:
    nfeatures: int = 1000
    scaleFactor: float = 1.2
    nlevels: int = 8
    edgeThreshold: int = 31
    firstLevel: int = 0
    WTA_K: int = 2
    scoreType: int = 0
    patchSize: int = 31
    fastThreshold: int = 20

@dataclass
class RegistrationConfig:
    ransac_thresh: float = 5.0
    min_match_count: int = 8
    resize_on_failure: bool = True

@dataclass
class HoughConfig:
    dp: float = 1.2
    minDist: int = 20
    param1: int = 50
    param2: int = 30
    minRadius: int = 5
    maxRadius: Optional[int] = None   # if None, compute from ROI size

@dataclass
class Thresholds:
    diff_threshold: float = 0.15     # normalized (0..1)
    gradient_threshold: float = 30.0 # absolute Sobel magnitude threshold
    plate_ratio_thresh: float = 0.02
    screw_ratio_thresh: float = 0.005

@dataclass
class PATHS:
    data_root: str = DATA_ROOT
    inline_top_ref: str = field(default_factory=lambda: os.path.join(DATA_ROOT, 'INLine', 'top_reference.jpg'))
    inline_bottom_ref: str = field(default_factory=lambda: os.path.join(DATA_ROOT, 'INLine', 'bottom_reference.jpg'))
    elot_front_ref: str = field(default_factory=lambda: os.path.join(DATA_ROOT, 'Elot', 'front_reference.jpg'))
    elot_rear_ref: str = field(default_factory=lambda: os.path.join(DATA_ROOT, 'Elot', 'rear_reference.jpg'))
    elot_left_ref: str = field(default_factory=lambda: os.path.join(DATA_ROOT, 'Elot', 'left_reference.jpg'))
    elot_right_ref: str = field(default_factory=lambda: os.path.join(DATA_ROOT, 'Elot', 'right_reference.jpg'))
    elot_front_mask: str = field(default_factory=lambda: os.path.join(DATA_ROOT, 'Elot', 'front_mask.png'))
    elot_rear_mask: str = field(default_factory=lambda: os.path.join(DATA_ROOT, 'Elot', 'rear_mask.png'))
    elot_left_mask: str = field(default_factory=lambda: os.path.join(DATA_ROOT, 'Elot', 'left_mask.png'))
    elot_right_mask: str = field(default_factory=lambda: os.path.join(DATA_ROOT, 'Elot', 'right_mask.png'))

@dataclass
class ROIs:
    # Default ROI examples (x,y,w,h) in reference coordinate space.
    # Replace with your real coordinates or load at runtime.
    inline_top_plate: Optional[Tuple[int,int,int,int]] = (100, 120, 400, 200)
    inline_bottom_antenna: Optional[Tuple[int,int,int,int]] = (50, 50, 200, 100)
    inline_bottom_speaker: Optional[Tuple[int,int,int,int]] = (220, 140, 200, 200)
    inline_bottom_plate: Optional[Tuple[int,int,int,int]] = (100, 200, 420, 200)
    inline_bottom_capacitor: Optional[Tuple[int,int,int,int]] = (300, 200, 60, 80)
    elot_front: Optional[Tuple[int,int,int,int]] = None
    elot_rear: Optional[Tuple[int,int,int,int]] = None
    elot_left: Optional[Tuple[int,int,int,int]] = None
    elot_right: Optional[Tuple[int,int,int,int]] = None

@dataclass
class AlgoConfig:
    ORB: ORBConfig = ORBConfig()
    REG: RegistrationConfig = RegistrationConfig()
    HOUGH: HoughConfig = HoughConfig()
    THRESHOLDS: Thresholds = Thresholds()
    PATHS: PATHS = PATHS()
    ROIS: ROIs = ROIs()

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def resolve_data_paths(self):
        """Ensure path strings are absolute and exist (only normalization)."""
        p = self.PATHS
        for k, v in vars(p).items():
            if isinstance(v, str):
                abs_p = os.path.abspath(v)
                setattr(p, k, abs_p)
        return p

# single instance convenience
DEFAULT_ALGO_CONFIG = AlgoConfig()
DEFAULT_ALGO_CONFIG.resolve_data_paths()