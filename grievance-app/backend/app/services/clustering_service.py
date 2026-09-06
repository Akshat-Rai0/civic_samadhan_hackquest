import math
from typing import List, Optional
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models.issue import IssueCluster, IssueImage
from app.services.phash_service import phash_distance
from app.services.priority_service import compute_priority

PHASH_THRESHOLD = 10
GPS_RADIUS_METERS = 20.0

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two GPS points in meters."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def find_matching_cluster(
    db: Session,
    phash: str,
    lat: Optional[float],
    lng: Optional[float],
    issue_type: str,
    postal_code: Optional[str] = None
) -> Optional[IssueCluster]:
    """
    A duplicate must be both the same normalized defect type and within the
    physical radius of an open cluster. pHash is used to prefer an exact-photo
    match among otherwise valid candidates; it can never merge distant or
    different defects on its own.
    """
    active_clusters = db.query(IssueCluster).filter(
        IssueCluster.status != 'closed',
        IssueCluster.status != 'resolved'
    ).all()

    normalized_issue_type = (issue_type or "").strip().lower()
    type_and_location_matches = []

    for cluster in active_clusters:
        # Same postal code condition
        if postal_code and cluster.postal_code:
            if str(postal_code).strip() != str(cluster.postal_code).strip():
                continue

        # 1. pHash match: perceptual hash distance below threshold
        has_phash_match = False
        if phash and phash != "0000000000000000":
            for image in cluster.images:
                if image.phash and image.phash != "0000000000000000":
                    if phash_distance(image.phash, phash) < PHASH_THRESHOLD:
                        has_phash_match = True
                        break

        # 2. GPS radius check: real great-circle distance between two GPS points (~15-20m)
        is_within_gps_radius = False
        if lat is not None and lng is not None and cluster.lat is not None and cluster.lng is not None:
            dist = haversine_distance(lat, lng, cluster.lat, cluster.lng)
            if dist <= GPS_RADIUS_METERS:
                is_within_gps_radius = True

        # 3. Defect type must match. Legacy clusters fall back to category only
        # until their startup backfill has populated issue_type.
        cluster_issue_type = (cluster.issue_type or cluster.category or "").strip().lower()
        has_type_match = bool(normalized_issue_type and normalized_issue_type == cluster_issue_type)

        if not (is_within_gps_radius and has_type_match):
            continue
        if has_phash_match:
            return cluster
        type_and_location_matches.append(cluster)

    # Same defect at the same physical location may be photographed from a
    # different angle, so pHash is intentionally not a mandatory final gate.
    return type_and_location_matches[0] if type_and_location_matches else None

def calculate_tier_from_percentile(score: float, all_scores: List[float]) -> str:
    """
    Compute tier from existing priority_score relative to currently open clusters:
    High -> red (top band of priority_score)
    Medium -> orange (middle band of priority_score)
    Low -> default/blue-gray (lower band of priority_score)
    """
    if not all_scores:
        return "low"

    unique_scores = sorted(list(set(all_scores)))
    if len(unique_scores) <= 2:
        if score >= 70.0:
            return "high"
        elif score >= 45.0:
            return "medium"
        else:
            return "low"

    # Normalized percentile rank across open cluster scores
    rank = unique_scores.index(score) if score in unique_scores else 0
    pct = rank / float(len(unique_scores) - 1)
    if pct >= 0.66:
        return "high"
    elif pct >= 0.33:
        return "medium"
    else:
        return "low"

def update_hotspot_tiers(db: Session):
    """
    Recompute tier live whenever affected_count increments or priority_score changes.
    A cluster becomes hotspot-eligible once affected_count crosses the config threshold.
    """
    settings = get_settings()
    threshold = getattr(settings, "HOTSPOT_AFFECTED_THRESHOLD", 2)

    open_clusters = db.query(IssueCluster).filter(
        IssueCluster.status.notin_(["closed", "resolved"])
    ).all()

    if not open_clusters:
        return

    scores = [float(c.priority_score or 0.0) for c in open_clusters]

    for cluster in open_clusters:
        count = cluster.affected_count or 1
        if count >= threshold:
            cluster.hotspot_tier = calculate_tier_from_percentile(
                float(cluster.priority_score or 0.0), 
                scores
            )
        else:
            cluster.hotspot_tier = None
        db.add(cluster)

    db.flush()

def add_to_cluster(db: Session, cluster: IssueCluster, image: IssueImage):
    """
    Adds a report to an existing cluster:
    - Increments affected_count
    - Recalculates cluster location as the actual lat/long centroid of all its reporting points
    - Recomputes priority_score and updates hotspot tier live
    """
    cluster.affected_count = (cluster.affected_count or 1) + 1
    image.cluster_id = cluster.id
    db.add(cluster)
    db.add(image)
    db.flush()

    # Centroid calculation: actual lat/long centroid of all reporting points
    points = []
    all_images = db.query(IssueImage).filter(IssueImage.cluster_id == cluster.id).all()
    for img in all_images:
        pt_lat = img.exif_lat if img.exif_lat is not None else img.device_lat
        pt_lng = img.exif_lng if img.exif_lng is not None else img.device_lng
        if pt_lat is not None and pt_lng is not None and not (pt_lat == 0.0 and pt_lng == 0.0):
            points.append((float(pt_lat), float(pt_lng)))

    if points:
        cluster.lat = round(sum(p[0] for p in points) / len(points), 6)
        cluster.lng = round(sum(p[1] for p in points) / len(points), 6)

    # An explicit admin override remains authoritative. Automatic scores still
    # recalculate as affected-count grows when no override exists.
    if cluster.priority_override is None:
        cluster.priority_score = compute_priority(cluster.issue_type or cluster.category or "default", cluster.affected_count)
    db.add(cluster)
    db.flush()

    # Update hotspot tiers dynamically across open clusters
    update_hotspot_tiers(db)
    db.commit()
    db.refresh(cluster)

def create_new_cluster(
    db: Session,
    category: str,
    severity_hint: str,
    confidence: float,
    issue_type: str,
    lat: Optional[float],
    lng: Optional[float],
    image: IssueImage,
    department_id: Optional[int] = None,
    zone: Optional[str] = None,
    postal_code: Optional[str] = None
) -> IssueCluster:
    priority = compute_priority(issue_type or category or "default", 1)
    cluster = IssueCluster(
        category=category,
        issue_type=issue_type,
        severity_hint=severity_hint,
        confidence=confidence,
        lat=lat,
        lng=lng,
        department_id=department_id,
        zone=zone,
        postal_code=postal_code,
        affected_count=1,
        priority_score=priority
    )
    db.add(cluster)
    db.flush()

    image.cluster_id = cluster.id
    db.add(image)
    db.flush()

    update_hotspot_tiers(db)
    db.commit()
    db.refresh(cluster)

    return cluster
