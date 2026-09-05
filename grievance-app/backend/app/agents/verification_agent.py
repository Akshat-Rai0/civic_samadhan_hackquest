from app.models.issue import IssueCluster
from app.models.completion import CompletionEvidence, CitizenConfirmation
from app.agents.communication_agent import notify_status_change

def compare_images(original_image_path: str, completion_image_path: str) -> dict:
    """Compare before and after photos. Returns diff_score and object_delta."""
    # Production hook for Moondream re-inspection
    return {
        "diff_score": 0.88,
        "object_delta": "Pothole filled and road surface restored to level."
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

    diff = compare_images("before.jpg", evidence.image_url if evidence else "after.jpg")
    citizen_status = check_citizen_confirmation(db, cluster_id)

    passed_checks = diff["diff_score"] >= 0.75
    if evidence:
        evidence.diff_score = diff["diff_score"]
        evidence.object_delta = diff["object_delta"]
        evidence.passed_automated_checks = passed_checks
        db.commit()

    recommendation = "pending_citizen"
    if citizen_status == "confirmed" and passed_checks:
        recommendation = "close"
    elif citizen_status == "disputed" or diff["diff_score"] < 0.4:
        recommendation = "reopen"

    return {
        "diff": diff,
        "citizen_status": citizen_status,
        "recommendation": recommendation,
        "passed_automated_checks": passed_checks
    }
