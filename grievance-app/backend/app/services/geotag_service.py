from typing import Tuple, Optional, Dict, Any
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

DEFAULT_CIVIC_LOCATION = (28.6139, 77.2090)

CIVIC_ZONES = [
    {"id": "central", "name": "Central Zone (Connaught Place)", "lat": 28.6139, "lng": 77.2090, "postal_code": "110001"},
    {"id": "south", "name": "South Zone (Hauz Khas / Saket)", "lat": 28.5494, "lng": 77.2001, "postal_code": "110016"},
    {"id": "north", "name": "North Zone (Civil Lines)", "lat": 28.6812, "lng": 77.2228, "postal_code": "110054"},
    {"id": "east", "name": "East Zone (Mayur Vihar)", "lat": 28.6083, "lng": 77.2958, "postal_code": "110091"},
    {"id": "west", "name": "West Zone (Rajouri Garden)", "lat": 28.6415, "lng": 77.1209, "postal_code": "110027"},
]

def _convert_to_degrees(value):
    d = float(value[0])
    m = float(value[1])
    s = float(value[2])
    return d + (m / 60.0) + (s / 3600.0)

def extract_exif_gps(image_path: str) -> Optional[Tuple[float, float]]:
    try:
        image = Image.open(image_path)
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
            
            return round(lat, 6), round(lng, 6)
    except Exception:
        pass
    
    return None

def get_location(image_path: str, device_lat: Optional[float], device_lng: Optional[float]) -> Optional[Tuple[float, float]]:
    exif_loc = extract_exif_gps(image_path)
    if exif_loc:
        return exif_loc
    if device_lat is not None and device_lng is not None and (device_lat != 0.0 or device_lng != 0.0):
        return round(float(device_lat), 6), round(float(device_lng), 6)
    return None

def resolve_location(image_path: Optional[str], device_lat: Optional[float], device_lng: Optional[float]) -> Tuple[float, float, str]:
    """
    Returns (lat, lng, source) where source is 'exif', 'device', or 'civic_default'.
    """
    if image_path:
        exif_loc = extract_exif_gps(image_path)
        if exif_loc:
            return exif_loc[0], exif_loc[1], "exif"

    if device_lat is not None and device_lng is not None and (device_lat != 0.0 or device_lng != 0.0):
        return round(float(device_lat), 6), round(float(device_lng), 6), "device"

    return DEFAULT_CIVIC_LOCATION[0], DEFAULT_CIVIC_LOCATION[1], "civic_default"

def needs_manual_pin(image_path: str, device_lat: Optional[float], device_lng: Optional[float]) -> bool:
    return get_location(image_path, device_lat, device_lng) is None
