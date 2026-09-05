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

def extract_geotag(image_path: str, device_lat: float, device_lng: float) -> dict:
    if device_lat and device_lng:
        return {
            "lat": device_lat,
            "lng": device_lng,
            "source": "device"
        }
    return {
        "lat": 0.0,
        "lng": 0.0,
        "source": "manual"
    }

def reverse_geocode(lat: float, lng: float) -> dict:
    return {
        "postal_code": "100001",
        "zone": "Central"
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
