#PostgreSQL Connection using SQLAlchemy
#Every repo later uses this connection to connect to the database

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from core.config import settings

# This knows how to talk to PostgreSQL.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
