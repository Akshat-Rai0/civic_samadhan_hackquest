import math

BASE_SEVERITY = {
    "exposed wiring": 95,
    "open manhole": 90,
    "sewage overflow": 85,
    "water contamination": 85,
    "broken streetlight": 70,
    "pothole": 60,
    "road damage": 55,
    "broken curb": 40,
    "garbage pile": 35,
    "graffiti": 15,
    "default": 50,
}

def affected_count_multiplier(count: int) -> float:
    """Diminishing returns so a popular minor issue does not outrank a rare serious one."""
    if count <= 1:
        return 1.0
    return 1.0 + 0.4 * math.log2(count)

def compute_priority(issue_type: str, affected_count: int) -> float:
    base = BASE_SEVERITY.get(issue_type.lower(), BASE_SEVERITY["default"])
    multiplier = affected_count_multiplier(affected_count)
    return round(base * multiplier, 1)
