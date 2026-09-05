from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Department(Base):
    __tablename__ = 'departments'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False)
    parent_tier_id = Column(Integer, ForeignKey('departments.id'), nullable=True)

    parent_tier = relationship("Department", remote_side=[id])
