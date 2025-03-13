"""
database.py

Sets up the SQLAlchemy engine, session factory, and a function to initialize the DB.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Configure logger for this module
logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite:///./demo_warehouses.db"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """
    Create all tables in the database (if not exist).
    """
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created or already exist.")
