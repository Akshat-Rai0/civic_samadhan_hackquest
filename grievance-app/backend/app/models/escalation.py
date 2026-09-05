from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base

class EscalationLog(Base):
    __tablename__ = 'escalation_logs'

    id = Column(Integer, primary_key=True)
    cluster_id = Column(Integer, ForeignKey('issue_clusters.id'), nullable=False)
    reason = Column(Text, nullable=False)
    from_tier = Column(Integer, nullable=False)
    to_tier = Column(Integer, nullable=False)
    notified_authority_id = Column(Integer, ForeignKey('officers.id'), nullable=True)
    logged_at = Column(DateTime, server_default=func.now())

    cluster = relationship("IssueCluster", back_populates="escalation_logs")
    notified_authority = relationship("Officer")
