from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2.elements import WKTElement
from app.models.issue import IssueCluster, IssueImage
from app.services.phash_service import phash_distance

PHASH_THRESHOLD = 10
GPS_RADIUS_METERS = 20.0

def find_matching_cluster(db_session: Session, phash: str, lat: float, lng: float, issue_types: List[str]) -> Optional[IssueCluster]:
    point = WKTElement(f"POINT({lng} {lat})", srid=4326)
    
    nearby_clusters = db_session.query(IssueCluster).filter(
        IssueCluster.status != 'closed',
        IssueCluster.status != 'resolved',
        func.ST_DWithin(IssueCluster.location, point, GPS_RADIUS_METERS)
    ).all()

    for cluster in nearby_clusters:
        for image in cluster.images:
            if image.phash and phash_distance(image.phash, phash) < PHASH_THRESHOLD:
                return cluster
        
        if any(t.lower() in cluster.category.lower() for t in issue_types):
            return cluster
            
    return None

def add_to_cluster(db_session: Session, cluster: IssueCluster, image: IssueImage):
    cluster.affected_count += 1
    image.cluster_id = cluster.id
    db_session.add(cluster)
    db_session.add(image)
    db_session.commit()

def create_new_cluster(db_session: Session, category: str, severity_hint: str, confidence: float, lat: float, lng: float, image: IssueImage) -> IssueCluster:
    point = WKTElement(f"POINT({lng} {lat})", srid=4326)
    cluster = IssueCluster(
        category=category,
        severity_hint=severity_hint,
        confidence=confidence,
        location=point,
        lat=lat,
        lng=lng
    )
    db_session.add(cluster)
    db_session.flush()
    
    image.cluster_id = cluster.id
    db_session.add(image)
    db_session.commit()
    db_session.refresh(cluster)
    
    return cluster
