import math
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.issue import IssueCluster, IssueImage
from app.services.phash_service import phash_distance

PHASH_THRESHOLD = 10
GPS_RADIUS_METERS = 20.0

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in meters."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def find_matching_cluster(db: Session, phash: str, lat: Optional[float], lng: Optional[float], issue_types: List[str]) -> Optional[IssueCluster]:
    active_clusters = db.query(IssueCluster).filter(
        IssueCluster.status != 'closed',
        IssueCluster.status != 'resolved'
    ).all()

    for cluster in active_clusters:
        # Check GPS proximity if coordinates exist
        is_nearby = True
        if lat is not None and lng is not None and cluster.lat is not None and cluster.lng is not None:
            dist = haversine_distance(lat, lng, cluster.lat, cluster.lng)
            if dist > GPS_RADIUS_METERS:
                is_nearby = False

        if not is_nearby:
            continue

        for image in cluster.images:
            if image.phash and phash and phash_distance(image.phash, phash) < PHASH_THRESHOLD:
                return cluster
        
        if any(t.lower() in (cluster.category or "").lower() for t in issue_types):
            return cluster
            
    return None

def add_to_cluster(db: Session, cluster: IssueCluster, image: IssueImage):
    cluster.affected_count += 1
    image.cluster_id = cluster.id
    db.add(cluster)
    db.add(image)
    db.commit()

def create_new_cluster(db: Session, category: str, severity_hint: str, confidence: float, lat: Optional[float], lng: Optional[float], image: IssueImage) -> IssueCluster:
    cluster = IssueCluster(
        category=category,
        severity_hint=severity_hint,
        confidence=confidence,
        lat=lat,
        lng=lng
    )
    db.add(cluster)
    db.flush()
    
    image.cluster_id = cluster.id
    db.add(image)
    db.commit()
    db.refresh(cluster)
    
    return cluster
