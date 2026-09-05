import uuid
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.models.contractor_email import ContractorEmailLog
from app.models.issue import IssueCluster, IssueImage
from app.models.officer import Officer


def get_officer_email(db, officer_id: int) -> str | None:
    """Read-only lookup of officer email from the officers table."""
    officer = db.query(Officer).filter(Officer.id == officer_id).first()
    if officer:
        return officer.email
    return None


def draft_email(db, cluster_id: int, officer_id: int) -> dict:
    """
    Build email subject + body from ticket details (category, zone, priority, images).
    Creates a ContractorEmailLog row with status 'draft'.
    Returns draft_id, subject, body, recipient_email.
    """
    cluster = db.query(IssueCluster).filter(IssueCluster.id == cluster_id).first()
    if not cluster:
        raise ValueError(f"Issue cluster {cluster_id} not found")

    recipient_email = get_officer_email(db, officer_id)
    if not recipient_email:
        raise ValueError(f"Officer {officer_id} not found or has no email")

    # Gather ticket details
    category = cluster.category or "General"
    zone = cluster.zone or "Unknown Zone"
    postal_code = cluster.postal_code or "N/A"
    priority_score = cluster.priority_score or 0.0
    affected_count = cluster.affected_count or 1
    escalation_tier = cluster.escalation_tier or 0

    # Determine priority label
    if priority_score >= 80:
        priority_label = "CRITICAL"
    elif priority_score >= 60:
        priority_label = "HIGH"
    elif priority_score >= 40:
        priority_label = "MEDIUM"
    else:
        priority_label = "LOW"

    # Gather image URLs for reference
    images = db.query(IssueImage).filter(IssueImage.cluster_id == cluster_id).all()
    image_refs = [img.image_url for img in images] if images else []

    # Build subject
    subject = (
        f"[Nagar Seva] [{priority_label}] Assignment: {category.title()} Issue "
        f"in {zone} — Ticket GR-{cluster_id}"
    )

    # Build body
    image_section = ""
    if image_refs:
        image_list = "\n".join(f"  - {url}" for url in image_refs)
        image_section = f"\nReference Photos:\n{image_list}\n"

    body = f"""Dear Officer,

You have been assigned to a new civic grievance ticket.

Ticket Details:
  Ticket ID:       GR-{cluster_id}
  Category:        {category.title()}
  Location:        {zone} (PIN {postal_code})
  Priority Score:  {priority_score} ({priority_label})
  Affected Reports: {affected_count} citizen report(s)
  Escalation Tier: {escalation_tier}
{image_section}
Please review the issue and initiate appropriate action at the earliest.
You can view the full ticket details on the Nagar Seva admin dashboard.

This is an automated notification from the Nagar Seva Grievance Redressal System.
Do not reply to this email.

Regards,
Nagar Seva Auto Grievance Raiser
Municipal Corporation Grievance Redressal System
"""

    # Generate unique draft ID
    draft_id = uuid.uuid4().hex

    # Persist draft
    log_entry = ContractorEmailLog(
        cluster_id=cluster_id,
        officer_id=officer_id,
        draft_id=draft_id,
        subject=subject,
        body=body,
        recipient_email=recipient_email,
        status="draft"
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    return {
        "draft_id": draft_id,
        "subject": subject,
        "body": body,
        "recipient_email": recipient_email
    }


def approve_send(db, draft_id: str, admin_id: int) -> dict:
    """
    Mark a draft as approved. Requires an admin action.
    Sets approved_by_admin_id and status to 'approved'.
    """
    entry = db.query(ContractorEmailLog).filter(
        ContractorEmailLog.draft_id == draft_id
    ).first()

    if not entry:
        raise ValueError(f"Draft {draft_id} not found")

    if entry.status == "sent":
        raise ValueError(f"Draft {draft_id} has already been sent")

    entry.approved_by_admin_id = admin_id
    entry.status = "approved"
    db.commit()
    db.refresh(entry)

    return {
        "draft_id": draft_id,
        "status": "approved",
        "approved_by_admin_id": admin_id
    }


def send_email(db, draft_id: str) -> dict:
    """
    Send the email for an approved draft.
    HARD RULE: Refuses and logs an error if approve_send was not called first.
    No autonomous send, ever.
    """
    entry = db.query(ContractorEmailLog).filter(
        ContractorEmailLog.draft_id == draft_id
    ).first()

    if not entry:
        raise ValueError(f"Draft {draft_id} not found")

    # ── HARD RULE: reject unapproved sends ──
    if entry.status != "approved":
        error_msg = (
            f"REJECTED: Cannot send draft {draft_id} — current status is '{entry.status}'. "
            f"approve_send() must be called before send_email(). No autonomous send allowed."
        )
        print(f"[ContractorEmailAgent ERROR] {error_msg}")

        # Log the rejection
        if entry.status == "draft":
            entry.status = "error"
            db.commit()

        raise PermissionError(error_msg)

    # ── Attempt to send ──
    now = datetime.utcnow()
    try:
        _dispatch_smtp(entry.recipient_email, entry.subject, entry.body)
    except Exception as e:
        # SMTP not configured — log to console as fallback
        print(f"[ContractorEmailAgent] SMTP send skipped (not configured): {e}")
        print(f"[ContractorEmailAgent] Would send to: {entry.recipient_email}")
        print(f"[ContractorEmailAgent] Subject: {entry.subject}")

    entry.sent_at = now
    entry.status = "sent"
    db.commit()
    db.refresh(entry)

    return {
        "draft_id": draft_id,
        "status": "sent",
        "sent_at": now.isoformat(),
        "recipient_email": entry.recipient_email
    }


def log_email_sent(db, cluster_id: int, officer_id: int, timestamp: datetime) -> dict:
    """
    Convenience writer — records a sent-email event to the contractor_email_log table.
    Used for external tracking/auditing.
    """
    entry = db.query(ContractorEmailLog).filter(
        ContractorEmailLog.cluster_id == cluster_id,
        ContractorEmailLog.officer_id == officer_id,
        ContractorEmailLog.status == "sent"
    ).order_by(ContractorEmailLog.id.desc()).first()

    if entry:
        return {
            "id": entry.id,
            "draft_id": entry.draft_id,
            "sent_at": entry.sent_at.isoformat() if entry.sent_at else None,
            "status": entry.status
        }

    return {
        "cluster_id": cluster_id,
        "officer_id": officer_id,
        "timestamp": timestamp.isoformat(),
        "status": "no_record_found"
    }


def _dispatch_smtp(to_email: str, subject: str, body: str):
    """
    Internal helper: attempt SMTP delivery.
    Raises if SMTP is not configured — caller handles the fallback.
    """
    import os
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")

    if not smtp_host or not smtp_user:
        raise RuntimeError("SMTP not configured (SMTP_HOST / SMTP_USER not set)")

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
