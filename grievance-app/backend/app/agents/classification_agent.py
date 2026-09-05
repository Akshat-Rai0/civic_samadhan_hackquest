def classify_issue(description: str, moondream_caption: list[str]) -> dict:
    taxonomy = {
        "electrical": ["streetlight", "wiring", "pole", "transformer", "power"],
        "roads": ["pothole", "road", "crack", "asphalt", "curb"],
        "water": ["pipe", "water", "sewage", "drain", "overflow", "manhole"],
        "sanitation": ["garbage", "waste", "trash", "dump", "litter"],
        "parks": ["tree", "park", "garden", "bench", "playground"],
        "buildings": ["wall", "building", "structure", "collapse"]
    }
    
    combined_text = (description + " " + " ".join(moondream_caption)).lower()
    
    best_category = "other"
    max_matches = 0
    
    for category, keywords in taxonomy.items():
        matches = sum(1 for kw in keywords if kw in combined_text)
        if matches > max_matches:
            max_matches = matches
            best_category = category
            
    severity_hint = "medium"
    if "collapse" in combined_text or "power" in combined_text or "overflow" in combined_text:
        severity_hint = "high"
    elif "litter" in combined_text or "bench" in combined_text:
        severity_hint = "low"
        
    confidence = min(0.4 + (max_matches * 0.15), 0.95) if max_matches > 0 else 0.3
    
    return {
        "category": best_category,
        "severity_hint": severity_hint,
        "confidence": confidence
    }

import math
import httpx
from app.services.geotag_service import extract_geotag as service_extract_geotag

# Real postal codes reference dataset for offline/fast geocoding fallback
REAL_POSTAL_DATASET = [
    {"postal_code": "110001", "zone": "Central Municipal Zone", "ward": "Ward 42, Connaught Place", "city": "New Delhi", "lat": 28.6315, "lng": 77.2167},
    {"postal_code": "110002", "zone": "Central Municipal Zone", "ward": "Ward 43, Daryaganj", "city": "New Delhi", "lat": 28.6433, "lng": 77.2415},
    {"postal_code": "110003", "zone": "South Municipal Zone", "ward": "Ward 58, Lodhi Colony", "city": "New Delhi", "lat": 28.5878, "lng": 77.2215},
    {"postal_code": "110005", "zone": "Karol Bagh Zone", "ward": "Ward 35, Karol Bagh", "city": "New Delhi", "lat": 28.6521, "lng": 77.1895},
    {"postal_code": "110006", "zone": "City-SP Zone", "ward": "Ward 22, Chandni Chowk", "city": "Delhi", "lat": 28.6562, "lng": 77.2300},
    {"postal_code": "110016", "zone": "South Municipal Zone", "ward": "Ward 64, Hauz Khas", "city": "New Delhi", "lat": 28.5494, "lng": 77.2001},
    {"postal_code": "110017", "zone": "South Municipal Zone", "ward": "Ward 68, Malviya Nagar", "city": "New Delhi", "lat": 28.5245, "lng": 77.2066},
    {"postal_code": "110019", "zone": "South Municipal Zone", "ward": "Ward 72, Kalkaji", "city": "New Delhi", "lat": 28.5482, "lng": 77.2513},
    {"postal_code": "110020", "zone": "South-East Zone", "ward": "Ward 75, Okhla", "city": "New Delhi", "lat": 28.5300, "lng": 77.2710},
    {"postal_code": "110024", "zone": "South Municipal Zone", "ward": "Ward 60, Lajpat Nagar", "city": "New Delhi", "lat": 28.5684, "lng": 77.2433},
    {"postal_code": "110027", "zone": "West Municipal Zone", "ward": "Ward 31, Rajouri Garden", "city": "New Delhi", "lat": 28.6415, "lng": 77.1209},
    {"postal_code": "110054", "zone": "North Municipal Zone", "ward": "Ward 18, Civil Lines", "city": "Delhi", "lat": 28.6812, "lng": 77.2228},
    {"postal_code": "110058", "zone": "West Municipal Zone", "ward": "Ward 28, Janakpuri", "city": "New Delhi", "lat": 28.6219, "lng": 77.0878},
    {"postal_code": "110070", "zone": "South-West Zone", "ward": "Ward 66, Vasant Kunj", "city": "New Delhi", "lat": 28.5204, "lng": 77.1567},
    {"postal_code": "110085", "zone": "Rohini Zone", "ward": "Ward 12, Rohini Sector 7", "city": "Delhi", "lat": 28.7166, "lng": 77.1126},
    {"postal_code": "110091", "zone": "East Municipal Zone", "ward": "Ward 85, Mayur Vihar", "city": "Delhi", "lat": 28.6083, "lng": 77.2958},
    {"postal_code": "110092", "zone": "East Municipal Zone", "ward": "Ward 82, Laxmi Nagar", "city": "Delhi", "lat": 28.6310, "lng": 77.2770},
    {"postal_code": "110095", "zone": "Shahdara Zone", "ward": "Ward 90, Dilshad Garden", "city": "Delhi", "lat": 28.6759, "lng": 77.3209}
]

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    return R * (2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a)))

def extract_geotag(image_meta, device_lat: float = None, device_lng: float = None) -> dict:
    return service_extract_geotag(image_meta, device_lat=device_lat, device_lng=device_lng)

def reverse_geocode(lat: float, lng: float) -> dict:
    if lat is None or lng is None or (lat == 0.0 and lng == 0.0):
        return {
            "postal_code": None,
            "zone": None,
            "ward": None,
            "city": None
        }

    # 1. Attempt real geocoding query via OpenStreetMap Nominatim with short timeout
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&addressdetails=1"
        headers = {"User-Agent": "CivicSamadhaan/1.0 (civic-grievance-app)"}
        resp = httpx.get(url, headers=headers, timeout=2.0)
        if resp.status_code == 200:
            addr = resp.json().get("address", {})
            postcode = addr.get("postcode")
            if postcode:
                zone = addr.get("suburb") or addr.get("city_district") or addr.get("county") or "Municipal Administrative Zone"
                ward = addr.get("neighbourhood") or addr.get("road") or f"Zone {zone}"
                city = addr.get("city") or addr.get("town") or addr.get("state") or "Delhi"
                return {
                    "postal_code": str(postcode).strip(),
                    "zone": zone,
                    "ward": ward,
                    "city": city
                }
    except Exception:
        pass

    # 2. Local real geographic dataset fallback: closest real postal code & administrative zone
    best_match = None
    min_dist = float("inf")
    for item in REAL_POSTAL_DATASET:
        dist = _haversine(lat, lng, item["lat"], item["lng"])
        if dist < min_dist:
            min_dist = dist
            best_match = item

    if best_match:
        return {
            "postal_code": best_match["postal_code"],
            "zone": best_match["zone"],
            "ward": best_match["ward"],
            "city": best_match["city"]
        }

    return {
        "postal_code": "110001",
        "zone": "Central Municipal Zone",
        "ward": "Ward 42, Connaught Place",
        "city": "New Delhi"
    }

def match_authority(postal_code: str, category: str) -> int:
    category_to_dept = {
        "electrical": 1,
        "roads": 2,
        "water": 3,
        "sanitation": 4,
        "parks": 5,
        "buildings": 6,
        "other": 7
    }
    return category_to_dept.get(category, 7)

def build_issue_object(classification: dict, geotag: dict, geocode: dict, department_id: int, image_ids: list[int]) -> dict:
    return {
        "classification": classification,
        "geotag": geotag,
        "geocode": geocode,
        "department_id": department_id,
        "image_ids": image_ids
    }
