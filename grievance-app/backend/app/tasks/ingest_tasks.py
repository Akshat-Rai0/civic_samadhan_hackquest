import json
from datetime import datetime, timedelta
from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models.issue import IssueImage, IssueCluster
from app.models.department import Department
from app.services.phash_service import compute_phash
from app.services.geotag_service import extract_exif_gps, get_location
from app.services.moondream_service import analyze_image
from app.services.clustering_service import find_matching_cluster, add_to_cluster, create_new_cluster
from app.services.priority_service import compute_priority
from app.agents.classification_agent import classify_issue, reverse_geocode, match_authority
from app.agents.communication_agent import notify_status_change
from app.agents.escalation_agent import SLA_HOURS

def run_process_upload(image_id: int):
    """Synchronous implementation of upload processing."""
    db = SessionLocal()
    try:
        image = db.query(IssueImage).filter(IssueImage.id == image_id).first()
        if not image:
            return

        file_path = image.image_url

        try:
            image.phash = compute_phash(file_path)
        except Exception:
            image.phash = "0000000000000000"

        coords = get_location(file_path, image.device_lat, image.device_lng)
        if coords:
            image.exif_lat, image.exif_lng = coords
        else:
            image.exif_lat = image.device_lat
            image.exif_lng = image.device_lng

        detected = analyze_image(file_path)
        image.moondream_output = json.dumps(detected)

        db.commit()
    finally:
        db.close()

@celery_app.task(name="app.tasks.ingest_tasks.process_upload")
def process_upload(image_id: int):
    run_process_upload(image_id)

def run_process_confirmed_submission(image_id: int) -> int:
    """Synchronous implementation of confirmed submission."""
    db = SessionLocal()
    try:
        image = db.query(IssueImage).filter(IssueImage.id == image_id).first()
        if not image:
            return 0

        detected_issues = []
        if image.moondream_output:
            try:
                detected_issues = json.loads(image.moondream_output)
            except Exception:
                detected_issues = [image.moondream_output]

        classification = classify_issue("", detected_issues)
        category = classification["category"]
        severity_hint = classification["severity_hint"]
        confidence = classification["confidence"]

        lat = image.exif_lat or image.device_lat or 28.6139
        lng = image.exif_lng or image.device_lng or 77.2090

        geo_info = reverse_geocode(lat, lng)
        zone = geo_info.get("zone", "Central")
        postal_code = geo_info.get("postal_code", "110001")
        department_id = match_authority(postal_code, category)

        # Check existing department or create fallback
        dept = db.query(Department).filter(Department.id == department_id).first()
        if not dept:
            dept = Department(id=department_id, name=f"{category.capitalize()} Department")
            db.merge(dept)
            db.commit()

        # Find or create cluster
        existing_cluster = find_matching_cluster(db, image.phash or "", lat, lng, detected_issues)
        if existing_cluster:
            cluster = existing_cluster
            add_to_cluster(db, cluster, image)
            cluster.priority_score = compute_priority(cluster.category, cluster.affected_count)
            db.commit()
        else:
            cluster = create_new_cluster(
                db=db,
                category=category,
                severity_hint=severity_hint,
                confidence=confidence,
                lat=lat,
                lng=lng,
                image=image
            )
            cluster.department_id = department_id
            cluster.zone = zone
            cluster.postal_code = postal_code
            cluster.priority_score = compute_priority(category, cluster.affected_count)

            hours = SLA_HOURS.get(severity_hint.lower(), SLA_HOURS["default"])
            cluster.sla_deadline = datetime.utcnow() + timedelta(hours=hours)
            db.commit()

        notify_status_change(db, cluster.id, "submitted")
        return cluster.id
    finally:
        db.close()

@celery_app.task(name="app.tasks.ingest_tasks.process_confirmed_submission")
def process_confirmed_submission(image_id: int):
    return run_process_confirmed_submission(image_id)
