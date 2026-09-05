from datetime import datetime
from app.models.issue import IssueCluster
from app.models.escalation import EscalationLog
from app.models.department import Department
from app.models.officer import Officer

SLA_HOURS = {
    "high": 48,
    "medium": 96,
    "low": 168,
    "default": 120
}

def check_sla_timer(db, cluster_id: int) -> dict:
    cluster = db.query(IssueCluster).filter(IssueCluster.id == cluster_id).first()
    if not cluster:
        return {"time_remaining_hours": 0, "is_breached": False, "severity": "default"}

    severity = cluster.severity_hint or "default"
    now = datetime.utcnow()

    if cluster.sla_deadline:
        diff_seconds = (cluster.sla_deadline - now).total_seconds()
        remaining_hours = round(diff_seconds / 3600.0, 1)
        is_breached = remaining_hours < 0
    else:
        # Default SLA calculation
        hours = SLA_HOURS.get(severity.lower(), SLA_HOURS["default"])
        created = cluster.created_at or now
        deadline = created.timestamp() + (hours * 3600)
        remaining_hours = round((deadline - now.timestamp()) / 3600.0, 1)
        is_breached = remaining_hours < 0

    return {
        "time_remaining_hours": remaining_hours,
        "is_breached": is_breached,
        "severity": severity
    }

def escalate_ticket(db, cluster_id: int, reason: str) -> int:
    cluster = db.query(IssueCluster).filter(IssueCluster.id == cluster_id).first()
    if not cluster:
        return 0

    from_tier = cluster.escalation_tier or 0
    new_tier = min(from_tier + 1, 3)
    cluster.escalation_tier = new_tier
    db.commit()

    # Log escalation
    authority_id = notify_higher_authority(db, cluster)
    log_escalation(db, cluster_id, reason, from_tier, new_tier, authority_id)
    return new_tier

def notify_higher_authority(db, cluster: IssueCluster) -> int | None:
    if not cluster.department_id:
        return None
    dept = db.query(Department).filter(Department.id == cluster.department_id).first()
    if dept and dept.parent_tier_id:
        higher_officer = db.query(Officer).filter(
            Officer.department_id == dept.parent_tier_id,
            Officer.active == True
        ).first()
        if higher_officer:
            return higher_officer.id
    return None

def log_escalation(db, cluster_id: int, reason: str, from_tier: int, to_tier: int, authority_id: int | None):
    try:
        entry = EscalationLog(
            cluster_id=cluster_id,
            reason=reason,
            from_tier=from_tier,
            to_tier=to_tier,
            notified_authority_id=authority_id
        )
        db.add(entry)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error logging escalation: {e}")

def run_escalation_check(db):
    open_clusters = db.query(IssueCluster).filter(
        IssueCluster.status.notin_(["resolved", "closed"])
    ).all()

    for cluster in open_clusters:
        sla_info = check_sla_timer(db, cluster.id)
        if sla_info.get("is_breached") and cluster.escalation_tier < 3:
            reason = f"SLA deadline breached by {abs(sla_info.get('time_remaining_hours', 0))} hours."
            escalate_ticket(db, cluster.id, reason)
