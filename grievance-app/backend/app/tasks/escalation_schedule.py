from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.agents.escalation_agent import run_escalation_check

@celery_app.task(name="app.tasks.escalation_schedule.run_escalation_sweep")
def run_escalation_sweep():
    db = SessionLocal()
    try:
        run_escalation_check(db)
    finally:
        db.close()
