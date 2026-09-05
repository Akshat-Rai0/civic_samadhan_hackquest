from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base

class Officer(Base):
    __tablename__ = 'officers'

    id = Column(Integer, primary_key=True)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)
    name = Column(String(200), nullable=False)
    email = Column(String(200))
    active = Column(Boolean, default=True)

class Assignment(Base):
    __tablename__ = 'assignments'

    id = Column(Integer, primary_key=True)
    cluster_id = Column(Integer, ForeignKey('issue_clusters.id'), nullable=False)
    officer_id = Column(Integer, ForeignKey('officers.id'), nullable=False)
    assigned_at = Column(DateTime, server_default=func.now())

    cluster = relationship("IssueCluster", back_populates="assignments")
    officer = relationship("Officer")
