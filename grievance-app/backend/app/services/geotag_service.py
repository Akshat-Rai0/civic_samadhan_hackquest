from typing import Tuple, Optional
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

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
            
            return lat, lng
    except Exception:
        pass
    
    return None

def get_location(image_path: str, device_lat: Optional[float], device_lng: Optional[float]) -> Optional[Tuple[float, float]]:
    exif_loc = extract_exif_gps(image_path)
    if exif_loc:
        return exif_loc
    if device_lat is not None and device_lng is not None:
        return device_lat, device_lng
    return None

def needs_manual_pin(image_path: str, device_lat: Optional[float], device_lng: Optional[float]) -> bool:
    return get_location(image_path, device_lat, device_lng) is None
