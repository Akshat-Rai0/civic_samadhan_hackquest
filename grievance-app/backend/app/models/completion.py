from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, func
from sqlalchemy.orm import relationship
from app.database import Base

class CompletionEvidence(Base):
    __tablename__ = 'completion_evidence'

    id = Column(Integer, primary_key=True)
    cluster_id = Column(Integer, ForeignKey('issue_clusters.id'), nullable=False)
    image_url = Column(String(500), nullable=False)
    exif_lat = Column(Float, nullable=True)
    exif_lng = Column(Float, nullable=True)
    timestamp = Column(DateTime, nullable=True)
    moondream_recheck_output = Column(Text, nullable=True)
    diff_score = Column(Float, nullable=True)
    object_delta = Column(Text, nullable=True)
    passed_automated_checks = Column(Boolean, nullable=True)
    confirmed_by_admin_id = Column(Integer, nullable=True)

    cluster = relationship("IssueCluster", back_populates="completion_evidence")

class CitizenConfirmation(Base):
    __tablename__ = 'citizen_confirmations'

    id = Column(Integer, primary_key=True)
    cluster_id = Column(Integer, ForeignKey('issue_clusters.id'), nullable=False)
    status = Column(String(20), default='pending')
    submitted_at = Column(DateTime, server_default=func.now())

    cluster = relationship("IssueCluster")
