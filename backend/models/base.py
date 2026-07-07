# Without Base, SQLAlchemy wouldn't know that User represents a database table.
from sqlalchemy.orm import DeclarativeBase
import uuid


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    """
    pass


def generate_uuid():
    """
    Generates a UUID4 for primary keys.
    """
    return uuid.uuid4()