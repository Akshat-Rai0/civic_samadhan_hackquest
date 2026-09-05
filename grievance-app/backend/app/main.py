import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import get_settings
from app.database import Base, engine
from app.routers import auth_router, issues_router, admin_router, contractor_email_router
from app.models.contractor_email import ContractorEmailLog  # noqa
from app.services.moondream_service import load_model

settings = get_settings()

# Create tables on startup (creates SQLite or Postgres tables)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Database initialization warning: {e}")

app = FastAPI(
    title="Auto Grievance Raiser API",
    description="Municipal grievance reporting, geo-clustering, and resolution verification system.",
    version="1.0.0"
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for uploads
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(auth_router)
app.include_router(issues_router)
app.include_router(admin_router)
app.include_router(contractor_email_router)


def seed_initial_data():
    from app.database import SessionLocal
    from app.models.department import Department
    from app.models.officer import Officer
    from app.models.user import User

    db = SessionLocal()
    try:
        try:
            from sqlalchemy import text
            db.execute(text("ALTER TABLE issue_clusters ADD COLUMN hotspot_tier VARCHAR(20)"))
            db.commit()
        except Exception:
            db.rollback()

        for column_sql in (
            "ALTER TABLE issue_clusters ADD COLUMN issue_type VARCHAR(100)",
            "ALTER TABLE issue_clusters ADD COLUMN priority_override FLOAT",
        ):
            try:
                db.execute(text(column_sql))
                db.commit()
            except Exception:
                db.rollback()

        departments = [
            (1, "Electrical Department"),
            (2, "Roads & Infrastructure"),
            (3, "Water & Sewage"),
            (4, "Sanitation"),
            (5, "Parks & Gardens"),
            (6, "Building Inspection"),
            (7, "General Municipal Administration"),
        ]
        for dept_id, name in departments:
            dept = db.query(Department).filter(Department.id == dept_id).first()
            if not dept:
                dept = Department(id=dept_id, name=name)
                db.add(dept)
        
        officers = [
            (1, 1, "Rajesh Sharma", "rajesh.sharma@delhi.gov.in"),
            (2, 2, "Vikram Patel", "vikram.patel@delhi.gov.in"),
            (3, 3, "Sunita Rao", "sunita.rao@delhi.gov.in"),
            (4, 4, "Amit Verma", "amit.verma@delhi.gov.in"),
        ]
        for off_id, dep_id, off_name, off_email in officers:
            off = db.query(Officer).filter(Officer.id == off_id).first()
            if not off:
                off = Officer(id=off_id, department_id=dep_id, name=off_name, email=off_email, active=True)
                db.add(off)

        user = db.query(User).filter(User.id == 1).first()
        if not user:
            user = User(id=1, mock_id_number="123456789012", name="Akshat Rai", phone="9876543210")
            db.add(user)

        db.commit()
        from app.services.priority_service import backfill_issue_types_and_priorities
        backfill_issue_types_and_priorities(db)
    except Exception as e:
        db.rollback()
        print(f"Initial seed notice: {e}")
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    seed_initial_data()
    load_model()

@app.get("/")
def root():
    return {
        "service": "Auto Grievance Raiser API",
        "status": "running",
        "version": "1.0.0"
    }
