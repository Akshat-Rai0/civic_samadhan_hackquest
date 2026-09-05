import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import get_settings
from app.database import Base, engine
from app.routers import auth_router, issues_router, admin_router
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

@app.on_event("startup")
async def startup_event():
    load_model()

@app.get("/")
def root():
    return {
        "service": "Auto Grievance Raiser API",
        "status": "running",
        "version": "1.0.0"
    }
