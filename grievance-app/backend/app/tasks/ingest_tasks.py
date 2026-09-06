import json
from datetime import datetime, timedelta
from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models.issue import IssueImage, IssueCluster
from app.models.department import Department
from app.services.phash_service import compute_phash
from app.services.geotag_service import resolve_location
from app.services.moondream_service import analyze_image
from app.services.clustering_service import find_matching_cluster, add_to_cluster, create_new_cluster
from app.services.priority_service import resolve_issue_type
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

        resolved_lat, resolved_lng, source = resolve_location(
            file_path, image.device_lat, image.device_lng
        )
        if source == "exif":
            image.exif_lat, image.exif_lng = resolved_lat, resolved_lng
            image.device_lat, image.device_lng = resolved_lat, resolved_lng
        elif source == "device":
            image.exif_lat, image.exif_lng = None, None
            image.device_lat, image.device_lng = resolved_lat, resolved_lng
        else:
            image.exif_lat = None
            image.exif_lng = None

        detected = analyze_image(file_path, image.description)
        image.moondream_output = json.dumps(detected)

        db.commit()
    finally:
        db.close()

@celery_app.task(name="app.tasks.ingest_tasks.process_upload")
def process_upload(image_id: int):
    run_process_upload(image_id)

def run_process_confirmed_submission(image_id: int, override_lat: float = None, override_lng: float = None) -> int:
    """Synchronous implementation of confirmed submission."""
    db = SessionLocal()
    try:
        image = db.query(IssueImage).filter(IssueImage.id == image_id).first()
        if not image:
            return 0
        if image.cluster_id is not None:
            return image.cluster_id

        detected_issues = []
        if image.moondream_output:
            try:
                detected_issues = json.loads(image.moondream_output)
            except Exception:
                detected_issues = [image.moondream_output]

        classification = classify_issue(image.description or "", detected_issues)
        category = classification["category"]
        issue_type = resolve_issue_type(
            [*detected_issues, image.description or ""], category
        )
        severity_hint = classification["severity_hint"]
        confidence = classification["confidence"]

        if override_lat is not None and override_lng is not None:
            lat = float(override_lat)
            lng = float(override_lng)
            # A citizen-selected map pin is not camera EXIF metadata.
            image.device_lat = lat
            image.device_lng = lng
        else:
            lat = image.exif_lat if image.exif_lat is not None else image.device_lat
            lng = image.exif_lng if image.exif_lng is not None else image.device_lng

        if (
            lat is None
            or lng is None
            or not (-90.0 <= float(lat) <= 90.0)
            or not (-180.0 <= float(lng) <= 180.0)
            or (float(lat) == 0.0 and float(lng) == 0.0)
        ):
            raise ValueError("A valid location is required before creating an issue cluster")

        geo_info = reverse_geocode(lat, lng)
        zone = geo_info.get("zone") or "Municipal Administrative Zone"
        postal_code = geo_info.get("postal_code")
        if not postal_code:
            raise ValueError("A postal code could not be resolved from the selected issue location")
        department_id = match_authority(postal_code, category)

        # Check existing department or create fallback
        dept = db.query(Department).filter(Department.id == department_id).first()
        if not dept:
            dept = Department(id=department_id, name=f"{category.capitalize()} Department")
            db.merge(dept)
            db.commit()

        # Find or create cluster with postal code grouping & real GPS radius
        existing_cluster = find_matching_cluster(
            db=db,
            phash=image.phash or "",
            lat=lat,
            lng=lng,
            issue_type=issue_type,
            postal_code=postal_code
        )
        if existing_cluster:
            cluster = existing_cluster
            add_to_cluster(db, cluster, image)
            cluster_created = False
        else:
            cluster = create_new_cluster(
                db=db,
                category=category,
                issue_type=issue_type,
                severity_hint=severity_hint,
                confidence=confidence,
                lat=lat,
                lng=lng,
                image=image,
                department_id=department_id,
                zone=zone,
                postal_code=postal_code
            )

            hours = SLA_HOURS.get(severity_hint.lower(), SLA_HOURS["default"])
            cluster.sla_deadline = datetime.utcnow() + timedelta(hours=hours)
            db.commit()
            cluster_created = True

        if cluster_created:
            notify_status_change(db, cluster.id, "submitted")
        return cluster.id
    finally:
        db.close()

@celery_app.task(name="app.tasks.ingest_tasks.process_confirmed_submission")
def process_confirmed_submission(image_id: int):
    return run_process_confirmed_submission(image_id)
