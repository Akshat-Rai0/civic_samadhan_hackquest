from app.models.notification import Notification
from app.models.issue import IssueCluster, IssueImage
from app.models.department import Department
from app.models.user import User
from app.services.translation_service import translate_text

def detect_status_change(db, cluster_id: int, new_status: str, old_status: str) -> bool:
    return new_status != old_status

def translate_message(text: str, lang: str) -> str:
    return translate_text(text, lang)

def send_notification(db, cluster_id: int, citizen_id: int, template: str, lang: str, message: str):
    if db is not None:
        try:
            record = Notification(
                cluster_id=cluster_id,
                citizen_id=citizen_id,
                template=template,
                lang=lang,
                message=message,
                status="sent"
            )
            db.add(record)
            db.commit()
            return record
        except Exception as e:
            db.rollback()
            print(f"Error saving notification: {e}")
        print(f"Notification to User {citizen_id} for Cluster {cluster_id}: {message}")
    return None

def notify_status_change(db, cluster_id: int, new_status: str):
    templates = {
        "submitted": "Your report has been received. Ticket #{id}.",
        "in_review": "Your report is being reviewed by {department}.",
        "assigned": "An officer has been assigned to your report.",
        "in_progress": "Work is in progress on your reported issue.",
        "pending_confirmation": "The reported issue has been marked as fixed. Please confirm.",
        "resolved": "Your report has been resolved. Thank you for reporting.",
        "closed": "Your report is now closed. Thank you for making our city better."
    }

    department_name = "Concerned Department"
    citizen_ids = []

    if db is not None:
        try:
            cluster = db.query(IssueCluster).filter(IssueCluster.id == cluster_id).first()
            if cluster and cluster.department_id:
                dept = db.query(Department).filter(Department.id == cluster.department_id).first()
                if dept:
                    department_name = dept.name
            
            # Find all citizens who reported this issue cluster
            images = db.query(IssueImage).filter(IssueImage.cluster_id == cluster_id).all()
            citizen_ids = list(set(img.uploaded_by_user_id for img in images if img.uploaded_by_user_id))
        except Exception as e:
            print(f"Error reading cluster info for notification: {e}")

    if not citizen_ids:
        citizen_ids = [1]

    template_str = templates.get(new_status, "Status updated to {status}.")
    message = template_str.format(id=cluster_id, department=department_name, status=new_status)

    for cid in citizen_ids:
        lang = "en"
        if db is not None:
            try:
                user = db.query(User).filter(User.id == cid).first()
                if user and user.preferred_lang:
                    lang = user.preferred_lang
            except Exception:
                lang = "en"
        final_message = translate_message(message, lang)
        send_notification(db, cluster_id, cid, new_status, lang, final_message)
