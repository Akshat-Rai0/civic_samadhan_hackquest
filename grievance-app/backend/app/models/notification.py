from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from app.database import Base

class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True)
    cluster_id = Column(Integer, ForeignKey('issue_clusters.id'), nullable=False)
    citizen_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    template = Column(String(100), nullable=False)
    lang = Column(String(10), default='en')
    message = Column(Text, nullable=True)
    sent_at = Column(DateTime, server_default=func.now())
    status = Column(String(20), default='sent')
