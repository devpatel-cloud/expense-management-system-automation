from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Text
from sqlalchemy.orm import relationship
from ..database import Base


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    log_type = Column(String, nullable=False)  # login, api, error, system
    action = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="system_logs")
