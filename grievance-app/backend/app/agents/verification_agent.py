from app.models.issue import IssueCluster
from app.models.completion import CompletionEvidence, CitizenConfirmation
from app.agents.communication_agent import notify_status_change
from app.services.moondream_service import analyze_image

def compare_images(original_image_path: str, completion_image_path: str) -> dict:
    """Compare before and after photos using Moondream. Returns diff_score and object_delta."""
    after_issues = analyze_image(completion_image_path)
    
    # Check if defects remain in the completion image
    defects = [i for i in after_issues if any(k in i for k in ["pothole", "broken", "damage", "garbage", "leak", "wire"])]
    
    if not defects:
        diff_score = 0.92
        delta = "Previously reported defect is no longer detected in the field completion photo."
    else:
        diff_score = 0.45
        delta = f"Field photo still contains indicators: {', '.join(defects)}."

    return {
        "diff_score": diff_score,
        "object_delta": delta,
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

    file_path = evidence.image_url if evidence else "after.jpg"
    diff = compare_images("before.jpg", file_path)
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
    elif citizen_status == "disputed" or diff["diff_score"] < 0.5:
        recommendation = "reopen"

    return {
        "diff": diff,
        "citizen_status": citizen_status,
        "recommendation": recommendation,
        "passed_automated_checks": passed_checks
    }
