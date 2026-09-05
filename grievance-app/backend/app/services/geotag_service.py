import os
import math
from typing import Tuple, Optional, Dict, Any
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

# Known manipulation / synthetic generation software signatures for authenticity check
MANIPULATION_KEYWORDS = [
    "photoshop", "gimp", "canva", "picsart", "snapseed", "midjourney", 
    "stable diffusion", "dall-e", "dalle", "deepfake", "faceapp", 
    "lightroom", "pixlr", "affinity", "pixelmator"
]

def _convert_to_degrees(value):
    try:
        d = float(value[0])
        m = float(value[1])
        s = float(value[2])
        return d + (m / 60.0) + (s / 3600.0)
    except Exception:
        return 0.0

def check_image_authenticity(image_path: Optional[str], meta: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
    """
    Checks if an image is authentic or has been edited/manipulated/synthesized.
    Returns (is_authentic: bool, reason: str).
    """
    if meta:
        if (meta.get("is_authentic") is False or 
            meta.get("is_fake") is True or 
            meta.get("edited") is True or 
            meta.get("flagged") is True):
            return False, "Image explicitly flagged as edited/fake in metadata"

    if not image_path or not os.path.exists(image_path):
        return True, "No image file provided"

    try:
        with Image.open(image_path) as image:
            exif = image._getexif()
            if exif:
                for key, val in exif.items():
                    tag_name = TAGS.get(key, key)
                    if tag_name in ["Software", "ProcessingSoftware", "ImageDescription", "UserComment"]:
                        val_str = str(val).lower()
                        for kw in MANIPULATION_KEYWORDS:
                            if kw in val_str:
                                return False, f"Image edited with manipulation software: {val}"
    except Exception:
        pass

    return True, "Image authenticity check passed"

def extract_exif_gps(image_path: str) -> Optional[Tuple[float, float]]:
    """
    Read real GPS lat/long from EXIF only.
    Returns (lat, lng) if valid real coordinates exist, else None.
    """
    if not image_path or not os.path.exists(image_path):
        return None

    try:
        with Image.open(image_path) as image:
            exif = image._getexif()
            if not exif:
                return None

            gps_info = {}
            for key, val in exif.items():
                decode = TAGS.get(key, key)
                if decode == "GPSInfo":
                    for t in val:
                        sub_decoded = GPSTAGS.get(t, t)
                        gps_info[sub_decoded] = val[t]
            
            if 'GPSLatitude' in gps_info and 'GPSLongitude' in gps_info:
                lat = _convert_to_degrees(gps_info['GPSLatitude'])
                if gps_info.get('GPSLatitudeRef', 'N') != 'N':
                    lat = -lat
                
                lng = _convert_to_degrees(gps_info['GPSLongitude'])
                if gps_info.get('GPSLongitudeRef', 'E') != 'E':
                    lng = -lng
                
                # Real coordinate validation
                if -90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0 and not (lat == 0.0 and lng == 0.0):
                    return round(lat, 6), round(lng, 6)
    except Exception:
        pass
    
    return None

def extract_geotag(image_meta: Any, device_lat: Optional[float] = None, device_lng: Optional[float] = None) -> Dict[str, Any]:
    """
    Extract real geotag:
    - If authenticity check flags the image as edited/fake, do not generate a geotag for it at all.
    - Reads real GPS lat/long from EXIF only.
    - If EXIF GPS is missing/invalid, falls back to device geolocation.
    - If neither exists, prompts a manual pin (returns None coordinates, never invents a default).
    """
    meta_dict = image_meta if isinstance(image_meta, dict) else {}
    image_path = None
    if isinstance(image_meta, str):
        image_path = image_meta
    elif isinstance(image_meta, dict):
        image_path = image_meta.get("image_path") or image_meta.get("path")
        if device_lat is None:
            device_lat = image_meta.get("device_lat")
        if device_lng is None:
            device_lng = image_meta.get("device_lng")

    # 1. Authenticity check: if flagged as edited/fake, do not generate a geotag for it at all
    is_authentic, auth_reason = check_image_authenticity(image_path, meta=meta_dict)
    if not is_authentic:
        return {
            "lat": None,
            "lng": None,
            "source": None,
            "authenticity_flagged": True,
            "prompt_manual_pin": False,
            "valid": False,
            "reason": auth_reason
        }

    # 2. Read real GPS from EXIF only
    exif_coords = extract_exif_gps(image_path) if image_path else None
    if exif_coords:
        return {
            "lat": exif_coords[0],
            "lng": exif_coords[1],
            "source": "exif",
            "authenticity_flagged": False,
            "prompt_manual_pin": False,
            "valid": True
        }

    # 3. Fallback to device geolocation captured at upload
    if device_lat is not None and device_lng is not None:
        try:
            d_lat = float(device_lat)
            d_lng = float(device_lng)
            if -90.0 <= d_lat <= 90.0 and -180.0 <= d_lng <= 180.0 and not (d_lat == 0.0 and d_lng == 0.0):
                return {
                    "lat": round(d_lat, 6),
                    "lng": round(d_lng, 6),
                    "source": "device",
                    "authenticity_flagged": False,
                    "prompt_manual_pin": False,
                    "valid": True
                }
        except (ValueError, TypeError):
            pass

    # 4. Neither exists -> Prompt manual pin. Never invent a default zone or fallback coordinates.
    return {
        "lat": None,
        "lng": None,
        "source": "manual_required",
        "authenticity_flagged": False,
        "prompt_manual_pin": True,
        "valid": False
    }

def get_location(image_path: Optional[str], device_lat: Optional[float], device_lng: Optional[float], meta: Optional[dict] = None) -> Optional[Tuple[float, float]]:
    geotag = extract_geotag(image_path, device_lat=device_lat, device_lng=device_lng)
    if geotag.get("valid") and geotag.get("lat") is not None and geotag.get("lng") is not None:
        return geotag["lat"], geotag["lng"]
    return None

def resolve_location(image_path: Optional[str], device_lat: Optional[float], device_lng: Optional[float], meta: Optional[dict] = None) -> Tuple[Optional[float], Optional[float], str]:
    """
    Returns (lat, lng, source) where source is 'exif', 'device', 'manual_required', or 'unauthentic'.
    Never invents default coordinates or default zones.
    """
    geotag = extract_geotag(image_path, device_lat=device_lat, device_lng=device_lng)
    if geotag.get("authenticity_flagged"):
        return None, None, "unauthentic"
    if geotag.get("valid") and geotag.get("lat") is not None and geotag.get("lng") is not None:
        return geotag["lat"], geotag["lng"], geotag.get("source", "unknown")
    return None, None, "manual_required"

def needs_manual_pin(image_path: Optional[str], device_lat: Optional[float], device_lng: Optional[float]) -> bool:
    loc = get_location(image_path, device_lat, device_lng)
    return loc is None
