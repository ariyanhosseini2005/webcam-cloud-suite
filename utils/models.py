
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .db import Base

class Media(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True)
    device_id = Column(String, index=True)
    filename = Column(String, unique=True)
    media_type = Column(String)  # image | video
    mime = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    note = Column(String, nullable=True)
