from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.contractor_email import ContractorEmailLog
from app.agents.contractor_email_agent import draft_email, approve_send, send_email


router = APIRouter(prefix="/api/contractor-email", tags=["Contractor Email"])


# ── Request schemas ──

class DraftRequest(BaseModel):
    cluster_id: int
    officer_id: int


class ApproveRequest(BaseModel):
    draft_id: str
    admin_id: int = 1  # default admin for demo


class SendRequest(BaseModel):
    draft_id: str


# ── Endpoints ──

@router.post("/draft")
def create_draft(req: DraftRequest, db: Session = Depends(get_db)):
    """Draft an email for a cluster-officer assignment."""
    try:
        result = draft_email(db, req.cluster_id, req.officer_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve")
def approve_draft(req: ApproveRequest, db: Session = Depends(get_db)):
    """Approve a draft for sending. Requires admin action."""
    try:
        result = approve_send(db, req.draft_id, req.admin_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send")
def send_draft(req: SendRequest, db: Session = Depends(get_db)):
    """
    Send an approved draft. Rejects with 403 if not approved first.
    Hard rule: no autonomous send, ever.
    """
    try:
        result = send_email(db, req.draft_id)
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cluster_id}")
def get_email_status(cluster_id: int, db: Session = Depends(get_db)):
    """Return all contractor email drafts/sent records for a given cluster."""
    entries = db.query(ContractorEmailLog).filter(
        ContractorEmailLog.cluster_id == cluster_id
    ).order_by(ContractorEmailLog.id.desc()).all()

    return [
        {
            "id": e.id,
            "cluster_id": e.cluster_id,
            "officer_id": e.officer_id,
            "draft_id": e.draft_id,
            "subject": e.subject,
            "body": e.body,
            "recipient_email": e.recipient_email,
            "sent_at": e.sent_at.isoformat() if e.sent_at else None,
            "approved_by_admin_id": e.approved_by_admin_id,
            "status": e.status,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in entries
    ]
