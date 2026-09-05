from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from app.database import Base


class ContractorEmailLog(Base):
    __tablename__ = 'contractor_email_log'

    id = Column(Integer, primary_key=True)
    cluster_id = Column(Integer, ForeignKey('issue_clusters.id'), nullable=False)
    officer_id = Column(Integer, ForeignKey('officers.id'), nullable=False)
    draft_id = Column(String(64), unique=True, nullable=False)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    recipient_email = Column(String(200), nullable=True)
    sent_at = Column(DateTime, nullable=True)
    approved_by_admin_id = Column(Integer, nullable=True)
    status = Column(String(20), default='draft')  # draft | approved | sent | error
    created_at = Column(DateTime, server_default=func.now())
