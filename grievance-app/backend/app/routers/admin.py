import os
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import get_settings
from app.models.issue import IssueCluster, IssueImage
from app.models.department import Department
from app.models.officer import Officer, Assignment
from app.models.escalation import EscalationLog
from app.models.completion import CompletionEvidence, CitizenConfirmation
from app.schemas.issue import HeatmapPoint
from app.agents.communication_agent import notify_status_change
from app.agents.verification_agent import process_completion, close_ticket, reopen_ticket

router = APIRouter(prefix="/api/admin", tags=["Admin"])
settings = get_settings()

@router.get("/queue")
def get_queue(
    department_id: Optional[int] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    query = db.query(IssueCluster)
    if department_id:
        query = query.filter(IssueCluster.department_id == department_id)
    if status_filter:
        query = query.filter(IssueCluster.status == status_filter)

    clusters = query.order_by(IssueCluster.priority_score.desc()).all()
    now = datetime.utcnow()

    items = []
    for c in clusters:
        created = c.created_at or now
        days_pending = max(0, (now - created).days)

        # Find assigned officer
        assignment = db.query(Assignment).filter(
            Assignment.cluster_id == c.id
        ).order_by(Assignment.assigned_at.desc()).first()

        officer_name = "Unassigned"
        if assignment:
            officer = db.query(Officer).filter(Officer.id == assignment.officer_id).first()
            if officer:
                officer_name = officer.name

        # Escalation info
        if c.escalation_tier > 0:
            esc_info = f"Escalated (Tier {c.escalation_tier})"
        elif c.sla_deadline and c.sla_deadline < now:
            esc_info = "SLA Breached"
        else:
            esc_info = "Within SLA"

        dept_name = "General"
        if c.department_id:
            dept = db.query(Department).filter(Department.id == c.department_id).first()
            if dept:
                dept_name = dept.name

        items.append({
            "id": c.id,
            "ticket_id": f"GR-{c.id}",
            "category": c.category,
            "department_id": c.department_id,
            "department_name": dept_name,
            "zone": c.zone,
            "postal_code": c.postal_code,
            "affected_count": c.affected_count,
            "priority_score": c.priority_score,
            "sla_deadline": c.sla_deadline,
            "escalation_tier": c.escalation_tier,
            "status": c.status,
            "created_at": c.created_at,
            "days_pending": days_pending,
            "officer_name": officer_name,
            "escalation_info": esc_info
        })

    return items

@router.get("/officers")
def get_officers(
    department_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Officer).filter(Officer.active == True)
    if department_id:
        query = query.filter(Officer.department_id == department_id)
    officers = query.all()

    # If DB is empty, provide seed officers
    if not officers:
        seeds = [
            {"id": 1, "department_id": 1, "name": "R. Verma", "email": "r.verma@city.gov.in"},
            {"id": 2, "department_id": 1, "name": "S. Iyer", "email": "s.iyer@city.gov.in"},
            {"id": 3, "department_id": 2, "name": "A. Sharma", "email": "a.sharma@city.gov.in"},
            {"id": 4, "department_id": 3, "name": "K. Patel", "email": "k.patel@city.gov.in"},
        ]
        return seeds

    return [{"id": o.id, "department_id": o.department_id, "name": o.name, "email": o.email} for o in officers]

@router.get("/issues/{cluster_id}")
def get_issue_detail(cluster_id: int, db: Session = Depends(get_db)):
    cluster = db.query(IssueCluster).filter(IssueCluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Issue cluster not found")

    images = db.query(IssueImage).filter(IssueImage.cluster_id == cluster_id).all()
    assignments = db.query(Assignment).filter(Assignment.cluster_id == cluster_id).order_by(Assignment.assigned_at.desc()).all()
    escalations = db.query(EscalationLog).filter(EscalationLog.cluster_id == cluster_id).order_by(EscalationLog.logged_at.desc()).all()
    evidences = db.query(CompletionEvidence).filter(CompletionEvidence.cluster_id == cluster_id).order_by(CompletionEvidence.id.desc()).all()

    dept = None
    if cluster.department_id:
        dept = db.query(Department).filter(Department.id == cluster.department_id).first()

    latest_officer = "Unassigned"
    if assignments:
        officer = db.query(Officer).filter(Officer.id == assignments[0].officer_id).first()
        if officer:
            latest_officer = officer.name

    citizen_text = ""
    for img in images:
        if img.moondream_output:
            try:
                parsed = json.loads(img.moondream_output)
                if isinstance(parsed, list):
                    citizen_text = ", ".join(parsed)
                else:
                    citizen_text = str(parsed)
            except Exception:
                citizen_text = str(img.moondream_output)
            if citizen_text:
                break

    from app.services.translation_service import translate_text
    translated_text = translate_text(citizen_text, "en") if citizen_text else ""

    return {
        "id": cluster.id,
        "ticket_id": f"GR-{cluster.id}",
        "category": cluster.category,
        "department_id": cluster.department_id,
        "department_name": dept.name if dept else "General Municipal",
        "zone": cluster.zone,
        "postal_code": cluster.postal_code,
        "lat": cluster.lat or 28.6139,
        "lng": cluster.lng or 77.2090,
        "affected_count": cluster.affected_count,
        "priority_score": cluster.priority_score,
        "sla_deadline": cluster.sla_deadline,
        "escalation_tier": cluster.escalation_tier,
        "status": cluster.status,
        "created_at": cluster.created_at,
        "assigned_officer": latest_officer,
        "citizen_text": citizen_text,
        "translated_text": translated_text,
        "images": [{"id": img.id, "image_url": img.image_url, "created_at": img.created_at} for img in images],
        "assignments": [{"id": a.id, "officer_id": a.officer_id, "assigned_at": a.assigned_at} for a in assignments],
        "escalation_logs": [
            {
                "id": e.id,
                "reason": e.reason,
                "from_tier": e.from_tier,
                "to_tier": e.to_tier,
                "logged_at": e.logged_at
            }
            for e in escalations
        ],
        "completion_evidence": [
            {
                "id": ev.id,
                "image_url": ev.image_url,
                "diff_score": ev.diff_score,
                "object_delta": ev.object_delta,
                "passed_automated_checks": ev.passed_automated_checks
            }
            for ev in evidences
        ]
    }


@router.post("/issues/{cluster_id}/assign")
def assign_officer(
    cluster_id: int,
    officer_id: int = Form(...),
    db: Session = Depends(get_db)
):
    cluster = db.query(IssueCluster).filter(IssueCluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Issue cluster not found")

    assignment = Assignment(
        cluster_id=cluster_id,
        officer_id=officer_id
    )
    db.add(assignment)

    if cluster.status in ("submitted", "in_review"):
        cluster.status = "assigned"

    db.commit()
    notify_status_change(db, cluster_id, cluster.status)

    # Auto-draft contractor email on assignment (5th agent trigger point)
    try:
        from app.agents.contractor_email_agent import draft_email
        draft_email(db, cluster_id, officer_id)
    except Exception as e:
        print(f"Contractor email draft notice: {e}")

    return {"status": "success", "message": "Officer assigned successfully."}


@router.get("/heatmap")
def get_heatmap_data(db: Session = Depends(get_db)):
    from app.services.clustering_service import update_hotspot_tiers
    update_hotspot_tiers(db)
    db.commit()

    clusters = db.query(IssueCluster).filter(
        IssueCluster.status.notin_(["closed"])
    ).all()

    points = []
    for c in clusters:
        if c.lat is None or c.lng is None:
            continue

        dept_name = "Unassigned Department"
        if c.department_id:
            dept = db.query(Department).filter(Department.id == c.department_id).first()
            if dept:
                dept_name = dept.name

        points.append({
            "id": c.id,
            "ticket_id": f"GR-{c.id}",
            "lat": c.lat,
            "lng": c.lng,
            "priority_score": c.priority_score,
            "category": c.category or "General",
            "affected_count": c.affected_count or 1,
            "hotspot_tier": c.hotspot_tier,
            "postal_code": c.postal_code,
            "department_id": c.department_id,
            "department_name": dept_name,
            "status": c.status
        })

    # If empty, provide representative points for demo
    if not points:
        points = [
            {"id": 101, "lat": 28.6139, "lng": 77.2090, "priority_score": 85.0, "category": "roads", "ticket_id": "GR-101", "affected_count": 4, "hotspot_tier": "high", "department_name": "Roads & Infrastructure"},
            {"id": 102, "lat": 28.6200, "lng": 77.2150, "priority_score": 70.0, "category": "electrical", "ticket_id": "GR-102", "affected_count": 2, "hotspot_tier": "medium", "department_name": "Electrical Department"},
            {"id": 103, "lat": 28.6080, "lng": 77.2020, "priority_score": 40.0, "category": "sanitation", "ticket_id": "GR-103", "affected_count": 2, "hotspot_tier": "low", "department_name": "Sanitation"},
        ]

    return points

@router.post("/issues/{cluster_id}/dispatch")
def dispatch_contractor(cluster_id: int, db: Session = Depends(get_db)):
    cluster = db.query(IssueCluster).filter(IssueCluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Issue cluster not found")

    cluster.status = "in_progress"
    db.commit()

    notify_status_change(db, cluster_id, "in_progress")
    return {"status": "success", "message": "Contractor dispatched. Ticket marked in progress."}

@router.post("/issues/{cluster_id}/completion-evidence")
async def upload_completion_evidence(
    cluster_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    cluster = db.query(IssueCluster).filter(IssueCluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Issue cluster not found")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    filename = f"completion_{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    evidence = CompletionEvidence(cluster_id=cluster_id, image_url=file_path)
    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    # Process with verification agent
    verification_result = process_completion(db, cluster_id, evidence.id)

    # Only valid, same-block, newer evidence that passes Moondream's recheck can
    # move the ticket to citizen confirmation. Invalid evidence stays in progress.
    cluster.status = "pending_confirmation" if verification_result["passed_automated_checks"] else "in_progress"
    db.commit()

    notify_status_change(db, cluster_id, cluster.status)

    return {
        "evidence_id": evidence.id,
        "verification": verification_result,
        "message": (
            "Completion evidence passed automated checks. Awaiting citizen and admin verification."
            if verification_result["passed_automated_checks"]
            else "Completion evidence failed automated checks and requires a new field photo."
        )
    }

@router.post("/issues/{cluster_id}/close")
def confirm_close(cluster_id: int, db: Session = Depends(get_db)):
    close_ticket(db, cluster_id)
    return {"status": "success", "message": "Issue confirmed resolved and closed."}

@router.post("/issues/{cluster_id}/reopen")
def confirm_reopen(
    cluster_id: int,
    reason: str = Form("Issue still persists after inspection."),
    db: Session = Depends(get_db)
):
    reopen_ticket(db, cluster_id, reason)
    return {"status": "success", "message": "Issue reopened for further action."}
