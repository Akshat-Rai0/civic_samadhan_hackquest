from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    mock_id_number = Column(String(12), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    phone = Column(String(15), nullable=True)
    preferred_lang = Column(String(10), default='en')
    created_at = Column(DateTime, server_default=func.now())
