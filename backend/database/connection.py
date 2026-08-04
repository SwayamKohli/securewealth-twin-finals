#PostgreSQL Connection using SQLAlchemy
#Every repo later uses this connection to connect to the database

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from core.config import settings

# This knows how to talk to PostgreSQL.
#
# Supabase (and most managed Postgres) drops idle connections after a few
# minutes, which surfaced as:
#   psycopg2.DatabaseError: SSL SYSCALL error: Can't assign requested address
# pool_recycle + pool_pre_ping retire stale sockets before they are used, and
# the TCP keepalives stop the connection going idle in the first place.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,      # validate a connection before handing it out
    pool_recycle=280,        # recycle before typical 5-minute idle timeouts
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    echo=False,
    connect_args={
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
