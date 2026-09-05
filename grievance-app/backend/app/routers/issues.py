import os
import json
import uuid
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import get_settings
from app.models.user import User
from app.models.issue import IssueImage, IssueCluster
from app.models.department import Department
from app.models.notification import Notification
from app.models.completion import CompletionEvidence, CitizenConfirmation
from app.schemas.issue import (
    IssueImageOut,
    IssueClusterOut,
    IssueClusterDetail,
    CitizenConfirmationCreate,
)
from app.routers.auth import get_current_user
from app.tasks.ingest_tasks import process_upload, run_process_upload, run_process_confirmed_submission
from app.agents.classification_agent import classify_issue, get_taxonomy_tags, match_authority, reverse_geocode

router = APIRouter(prefix="/api/issues", tags=["Issues"])
settings = get_settings()

class ConfirmIssueRequest(BaseModel):
    lat: Optional[float] = None
    lng: Optional[float] = None


def has_valid_coordinates(lat: Optional[float], lng: Optional[float]) -> bool:
    return (
        lat is not None
        and lng is not None
        and -90.0 <= lat <= 90.0
        and -180.0 <= lng <= 180.0
        and (lat != 0.0 or lng != 0.0)
    )

@router.post("/upload")
async def upload_issue(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    device_lat: Optional[float] = Form(None),
    device_lng: Optional[float] = Form(None),
    description: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    user_id = int(current_user["id"])

    # Ensure user exists in database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, mock_id_number=current_user.get("mock_id_number", f"ID_{user_id}"), name=current_user.get("name", "Citizen"))
        db.add(user)
        db.commit()

    # Resolve EXIF GPS or device GPS. Missing data is handled by the manual-pin
    # step on the confirmation screen; a location is never fabricated.
    from app.services.geotag_service import resolve_location
    resolved_lat, resolved_lng, geo_src = resolve_location(file_path, device_lat, device_lng)

    # Create unclustered issue image
    image_record = IssueImage(
        uploaded_by_user_id=user_id,
        image_url=file_path,
        device_lat=resolved_lat,
        device_lng=resolved_lng,
        exif_lat=resolved_lat if geo_src == "exif" else None,
        exif_lng=resolved_lng if geo_src == "exif" else None,
        description=description.strip() if description else None,
    )
    db.add(image_record)
    db.commit()
    db.refresh(image_record)

    # Queue background analysis (try Celery, fallback to FastAPI background task)
    try:
        process_upload.delay(image_record.id)
    except Exception:
        background_tasks.add_task(run_process_upload, image_record.id)

    return {
        "image_id": image_record.id,
        "status": "processing",
        "message": "Photo uploaded. Visual analysis running in background."
    }

@router.get("/{image_id}/preview")
async def get_preview(
    image_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    image = db.query(IssueImage).filter(IssueImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    if image.uploaded_by_user_id != int(current_user["id"]):
        raise HTTPException(status_code=403, detail="You can only preview your own uploads")

    if not image.moondream_output:
        # If still processing, run now if needed
        run_process_upload(image_id)
        db.refresh(image)

    detected = []
    if image.moondream_output:
        try:
            detected = json.loads(image.moondream_output)
        except Exception:
            detected = [image.moondream_output]

    lat = image.exif_lat if image.exif_lat is not None else image.device_lat
    lng = image.exif_lng if image.exif_lng is not None else image.device_lng

    if has_valid_coordinates(lat, lng):
        geo_info = reverse_geocode(lat, lng)
        source_label = "EXIF metadata" if image.exif_lat is not None else "Device GPS"
        prompt_manual = False
    else:
        geo_info = {"postal_code": None, "zone": None, "ward": None, "city": None}
        source_label = "manual_required"
        prompt_manual = True

    classification = classify_issue(image.description or "", detected)
    taxonomy_tags = get_taxonomy_tags(image.description or "", detected)
    if has_valid_coordinates(lat, lng):
        dept_id = match_authority(geo_info.get("postal_code"), classification["category"])
        dept = db.query(Department).filter(Department.id == dept_id).first()
        department_name = dept.name if dept else f"{classification['category'].capitalize()} Department"
    else:
        department_name = None

    return {
        "image_id": image.id,
        # Never expose Moondream's free-form caption in the citizen UI.
        "detected_issues": taxonomy_tags,
        "category": classification["category"],
        "severity_hint": classification["severity_hint"],
        "routed_department": department_name,
        "geotag": {
            "lat": round(lat, 6) if lat is not None else None,
            "lng": round(lng, 6) if lng is not None else None,
            "zone": geo_info.get("zone"),
            "postal_code": geo_info.get("postal_code"),
            "ward": geo_info.get("ward"),
            "city": geo_info.get("city"),
            "source": source_label,
            "prompt_manual_pin": prompt_manual
        }
    }

@router.post("/{image_id}/confirm")
async def confirm_issue(
    image_id: int,
    confirm_data: Optional[ConfirmIssueRequest] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    image = db.query(IssueImage).filter(IssueImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    if image.uploaded_by_user_id != int(current_user["id"]):
        raise HTTPException(status_code=403, detail="You can only confirm your own uploads")
    if image.cluster_id is not None:
        return {
            "cluster_id": image.cluster_id,
            "status": "confirmed",
            "already_confirmed": True,
            "message": "This report was already submitted to the municipal department.",
        }

    override_lat = confirm_data.lat if confirm_data else None
    override_lng = confirm_data.lng if confirm_data else None
    if (override_lat is None) != (override_lng is None):
        raise HTTPException(status_code=422, detail="Both latitude and longitude are required for a manual map pin.")
    image_lat = image.exif_lat if image.exif_lat is not None else image.device_lat
    image_lng = image.exif_lng if image.exif_lng is not None else image.device_lng
    selected_lat = override_lat if override_lat is not None else image_lat
    selected_lng = override_lng if override_lng is not None else image_lng

    if not has_valid_coordinates(selected_lat, selected_lng):
        raise HTTPException(
            status_code=422,
            detail="Location is required before submission. Choose a map pin when automatic geotagging is unavailable.",
        )

    # If asynchronous analysis has not finished, complete it only after the
    # report has passed the mandatory location gate.
    if not image.moondream_output:
        run_process_upload(image_id)
        db.refresh(image)

    cluster_id = run_process_confirmed_submission(image_id, override_lat=override_lat, override_lng=override_lng)
    return {
        "cluster_id": cluster_id,
        "status": "confirmed",
        "message": "Your report has been submitted to the municipal department."
    }

@router.get("/track/{cluster_id}")
async def track_issue(
    cluster_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cluster = db.query(IssueCluster).filter(IssueCluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Issue report not found")

    notifications = db.query(Notification).filter(
        Notification.cluster_id == cluster_id
    ).order_by(Notification.sent_at.desc()).all()

    evidence = db.query(CompletionEvidence).filter(
        CompletionEvidence.cluster_id == cluster_id
    ).order_by(CompletionEvidence.id.desc()).first()

    citizen_conf = db.query(CitizenConfirmation).filter(
        CitizenConfirmation.cluster_id == cluster_id
    ).order_by(CitizenConfirmation.submitted_at.desc()).first()

    dept = None
    if cluster.department_id:
        dept = db.query(Department).filter(Department.id == cluster.department_id).first()

    images = db.query(IssueImage).filter(IssueImage.cluster_id == cluster_id).all()

    return {
        "id": cluster.id,
        "ticket_id": f"GR-{cluster.id}",
        "category": cluster.category,
        "department_name": dept.name if dept else "General Municipal",
        "zone": cluster.zone,
        "postal_code": cluster.postal_code,
        "affected_count": cluster.affected_count,
        "status": cluster.status,
        "created_at": cluster.created_at,
        "images": [{"id": img.id, "image_url": img.image_url} for img in images],
        "notifications": [
            {
                "id": n.id,
                "template": n.template,
                "message": n.message,
                "sent_at": n.sent_at
            }
            for n in notifications
        ],
        "completion_evidence": {
            "id": evidence.id,
            "image_url": evidence.image_url,
            "diff_score": evidence.diff_score,
            "object_delta": evidence.object_delta,
            "passed_automated_checks": evidence.passed_automated_checks
        } if evidence else None,
        "citizen_confirmation_status": citizen_conf.status if citizen_conf else None
    }

@router.post("/confirm-resolution")
async def confirm_resolution(
    data: CitizenConfirmationCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cluster = db.query(IssueCluster).filter(IssueCluster.id == data.cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Issue cluster not found")

    conf = CitizenConfirmation(
        cluster_id=data.cluster_id,
        status=data.status
    )
    db.add(conf)

    if data.status == "confirmed":
        cluster.status = "closed"
    elif data.status == "disputed":
        cluster.status = "in_progress"

    db.commit()

    return {
        "status": "success",
        "confirmation": data.status,
        "cluster_status": cluster.status,
        "message": "Thank you for confirming the status of this issue."
    }

@router.get("/my-issues")
async def get_my_issues(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = int(current_user["id"])
    images = db.query(IssueImage).filter(
        IssueImage.uploaded_by_user_id == user_id,
        IssueImage.cluster_id.isnot(None)
    ).all()

    cluster_ids = list(set(img.cluster_id for img in images))
    if not cluster_ids:
        # Fallback to recent clusters for demo
        clusters = db.query(IssueCluster).order_by(IssueCluster.created_at.desc()).limit(10).all()
    else:
        clusters = db.query(IssueCluster).filter(IssueCluster.id.in_(cluster_ids)).all()

    results = []
    for c in clusters:
        results.append({
            "id": c.id,
            "ticket_id": f"GR-{c.id}",
            "category": c.category,
            "status": c.status,
            "zone": c.zone,
            "affected_count": c.affected_count,
            "priority_score": c.priority_score,
            "created_at": c.created_at
        })
    return results
