from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# ==============================================================
# Load environment variables from .env file
# ==============================================================

load_dotenv()

# ==============================================================
# Build the DATABASE_URL dynamically from environment variables
# ==============================================================

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# Construct PostgreSQL URL dynamically
DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# ==============================================================
# SQLAlchemy Engine & Session Configuration
# ==============================================================

# create_engine() establishes the connection to the database.
# You can set echo=True for debugging to view all executed SQL queries.
engine = create_engine(DATABASE_URL, future=True)

# Session factory configuration
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()

# ==============================================================
# Database Dependency for FastAPI
# ==============================================================
# This ensures a new session per request and proper cleanup after.

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
