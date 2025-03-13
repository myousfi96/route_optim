"""
models.py

SQLAlchemy models for the application.
"""

import logging
from sqlalchemy import Column, Integer, Float, String
from database import Base

logger = logging.getLogger(__name__)

class Warehouse(Base):
    """
    A single warehouse, storing:
      id, name, latitude, longitude, inventory
    """
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    inventory = Column(Float, default=0.0)

    def __repr__(self):
        return (f"<Warehouse id={self.id}, name={self.name}, "
                f"lat={self.latitude}, lon={self.longitude}, inv={self.inventory}>")
