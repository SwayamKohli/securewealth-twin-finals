from typing import Generator

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.security import decode_access_token
from database.connection import SessionLocal
from models.user import User


from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()


# ----------------------------------------------------
# DATABASE
# ----------------------------------------------------

#This function says: Create DB Session -> Give it to the API -> When API finishes -> Automatically close it
#This prevents connection leaks.
def get_db():
    db = SessionLocal()

    try:
        yield db    #FastAPI pauses at yield, gives the session to the endpoint, and once the endpoint finishes, execution resumes after yield, allowing db.close() to run.

    finally:
        db.close()


# ----------------------------------------------------
# CURRENT USER
# ----------------------------------------------------


def get_current_user(

    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),

    db: Session = Depends(
        get_db
    ),

):

    # Extract JWT from the Authorization header
    token = credentials.credentials

    payload = decode_access_token(
        token
    )

    if not payload:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")

    if user_id is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = db.get(
        User,
        user_id,
    )

    if user is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user