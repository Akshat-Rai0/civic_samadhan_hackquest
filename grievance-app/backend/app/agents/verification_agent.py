import json
import math
from datetime import datetime
from app.models.issue import IssueCluster
from app.models.completion import CompletionEvidence, CitizenConfirmation
from app.agents.communication_agent import notify_status_change
from app.services.moondream_service import analyze_image
from app.services.geotag_service import extract_exif_capture_time, extract_exif_gps
from app.agents.classification_agent import get_taxonomy_tags

SAME_BLOCK_RADIUS_METERS = 150


def _distance_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6_371_000
    lat_delta = math.radians(lat2 - lat1)
    lng_delta = math.radians(lng2 - lng1)
    a = (
        math.sin(lat_delta / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(lng_delta / 2) ** 2
    )
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def compare_images(original_image_path: str, completion_image_path: str, category: str) -> dict:
    """Use Moondream on the actual before/after photos to verify the reported defect is gone."""
    original_issues = analyze_image(original_image_path)
    after_issues = analyze_image(completion_image_path)
    original_tags = get_taxonomy_tags("", original_issues)
    completion_tags = get_taxonomy_tags("", after_issues)
    target_category = category if category != "other" else next(iter(original_tags), "other")
    defect_remains = target_category != "other" and target_category in completion_tags

    if not defect_remains:
        diff_score = 0.92
        delta = "Moondream no longer detects the reported issue category in the completion photo."
    else:
        diff_score = 0.45
        delta = f"Moondream still detects the reported {target_category} issue category in the completion photo."

    return {
        "diff_score": diff_score,
        "object_delta": delta,
        "original_detected": original_issues,
        "original_tags": original_tags,
        "completion_detected": after_issues
    }

def check_citizen_confirmation(db, cluster_id: int) -> str:
    """Returns 'confirmed', 'disputed', or 'pending'."""
    conf = db.query(CitizenConfirmation).filter(
        CitizenConfirmation.cluster_id == cluster_id
    ).order_by(CitizenConfirmation.submitted_at.desc()).first()

    if conf:
        return conf.status
    return "pending"

def reopen_ticket(db, cluster_id: int, reason: str) -> str:
    cluster = db.query(IssueCluster).filter(IssueCluster.id == cluster_id).first()
    if cluster:
        cluster.status = "in_progress"
        db.commit()
        notify_status_change(db, cluster_id, "in_progress")
    return "in_progress"

def close_ticket(db, cluster_id: int) -> str:
    cluster = db.query(IssueCluster).filter(IssueCluster.id == cluster_id).first()
    if cluster:
        cluster.status = "resolved"
        db.commit()
        notify_status_change(db, cluster_id, "resolved")
    return "resolved"

def process_completion(db, cluster_id: int, evidence_id: int) -> dict:
    evidence = db.query(CompletionEvidence).filter(CompletionEvidence.id == evidence_id).first()
    cluster = db.query(IssueCluster).filter(IssueCluster.id == cluster_id).first()
    original_image = (
        sorted(cluster.images, key=lambda image: image.created_at or datetime.min)[0]
        if cluster and cluster.images
        else None
    )

    original_lat = None
    original_lng = None
    if original_image:
        original_lat = original_image.exif_lat if original_image.exif_lat is not None else original_image.device_lat
        original_lng = original_image.exif_lng if original_image.exif_lng is not None else original_image.device_lng
    if original_lat is None or original_lng is None:
        original_lat = cluster.lat if cluster else None
        original_lng = cluster.lng if cluster else None

    file_path = evidence.image_url if evidence else ""
    completion_coords = extract_exif_gps(file_path)
    completion_lat, completion_lng = completion_coords if completion_coords else (None, None)
    completion_timestamp = extract_exif_capture_time(file_path)
    original_uploaded_at = original_image.created_at if original_image else None

    distance = None
    location_passed = False
    if all(value is not None for value in [original_lat, original_lng, completion_lat, completion_lng]):
        distance = _distance_meters(original_lat, original_lng, completion_lat, completion_lng)
        location_passed = distance <= SAME_BLOCK_RADIUS_METERS

    date_passed = bool(
        completion_timestamp
        and original_uploaded_at
        and completion_timestamp > original_uploaded_at
    )

    diff = compare_images(original_image.image_url if original_image else "", file_path, cluster.category if cluster else "other")
    citizen_status = check_citizen_confirmation(db, cluster_id)

    visual_passed = diff["diff_score"] >= 0.75
    passed_checks = location_passed and date_passed and visual_passed
    if evidence:
        evidence.exif_lat = completion_lat
        evidence.exif_lng = completion_lng
        evidence.timestamp = completion_timestamp
        evidence.diff_score = diff["diff_score"]
        evidence.object_delta = (
            f"{diff['object_delta']} GPS check: "
            f"{'passed' if location_passed else 'failed'}"
            f"{f' ({distance:.0f} m from original)' if distance is not None else ' (GPS metadata unavailable)'}. "
            f"Capture date check: {'passed' if date_passed else 'failed'}."
        )
        evidence.moondream_recheck_output = json.dumps(diff)
        evidence.passed_automated_checks = passed_checks
        db.commit()

    recommendation = "pending_citizen"
    if citizen_status == "confirmed" and passed_checks:
        recommendation = "close"
    elif not passed_checks or citizen_status == "disputed" or diff["diff_score"] < 0.5:
        recommendation = "reopen"

    return {
        "diff": diff,
        "citizen_status": citizen_status,
        "recommendation": recommendation,
        "passed_automated_checks": passed_checks,
        "validation": {
            "location_passed": location_passed,
            "distance_meters": round(distance, 1) if distance is not None else None,
            "max_distance_meters": SAME_BLOCK_RADIUS_METERS,
            "date_passed": date_passed,
            "completion_captured_at": completion_timestamp.isoformat() if completion_timestamp else None,
            "original_uploaded_at": original_uploaded_at.isoformat() if original_uploaded_at else None,
            "visual_passed": visual_passed,
        },
    }
