#Responsible for MPIN hashing and JWT token creation and decoding

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


# --------------------------------------------------
# MPIN HASHING
# --------------------------------------------------

# def hash_mpin(mpin: str) -> str:
#     """
#     Hash a plain text MPIN.
#     """
#     return pwd_context.hash(mpin)

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()

def hash_mpin(mpin: str) -> str:
    return ph.hash(mpin)

def verify_mpin(plain_mpin: str, hashed_mpin: str) -> bool:
    try:
        return ph.verify(hashed_mpin, plain_mpin)
    except VerifyMismatchError:
        return False


# --------------------------------------------------
# JWT
# --------------------------------------------------

def create_access_token(
    subject: str,
) -> str:

    expire = datetime.now(
        timezone.utc
    ) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": subject,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(
    token: str,
) -> dict[str, Any]:

    try:

        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[
                settings.JWT_ALGORITHM
            ],
        )

        return payload

    except JWTError:

        return {}