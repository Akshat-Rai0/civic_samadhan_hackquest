from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.database import Base

class IssueCluster(Base):
    __tablename__ = 'issue_clusters'

    id = Column(Integer, primary_key=True)
    category = Column(String(100))
    issue_type = Column(String(100), nullable=True)
    severity_hint = Column(String(50))
    confidence = Column(Float)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=True)
    zone = Column(String(100))
    postal_code = Column(String(20))
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    affected_count = Column(Integer, default=1)
    priority_score = Column(Float, default=0.0)
    priority_override = Column(Float, nullable=True)
    sla_deadline = Column(DateTime, nullable=True)
    escalation_tier = Column(Integer, default=0)
    status = Column(String(30), default='submitted')
    created_at = Column(DateTime, server_default=func.now())
    hotspot_tier = Column(String(20), nullable=True)

    images = relationship("IssueImage", back_populates="cluster")
    assignments = relationship("Assignment", back_populates="cluster")
    escalation_logs = relationship("EscalationLog", back_populates="cluster")
    completion_evidence = relationship("CompletionEvidence", back_populates="cluster")

class IssueImage(Base):
    __tablename__ = 'issue_images'

    id = Column(Integer, primary_key=True)
    cluster_id = Column(Integer, ForeignKey('issue_clusters.id'), nullable=True)
    uploaded_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    image_url = Column(String(500), nullable=False)
    phash = Column(String(64))
    exif_lat = Column(Float, nullable=True)
    exif_lng = Column(Float, nullable=True)
    device_lat = Column(Float, nullable=True)
    device_lng = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    moondream_output = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    cluster = relationship("IssueCluster", back_populates="images")
