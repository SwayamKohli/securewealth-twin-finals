from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

class RegisterRequest(BaseModel):

    full_name: str

    phone: str = Field(
        min_length=10,
        max_length=15,
    )

    email: str | None = None

    date_of_birth: date | None = None

    mpin: str = Field(
        min_length=6,
        max_length=6,
    )


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

class LoginRequest(BaseModel):

    phone: str = Field(
        min_length=10,
        max_length=15,
    )

    mpin: str = Field(
        min_length=6,
        max_length=6,
    )


# --------------------------------------------------
# TOKEN
# --------------------------------------------------

class TokenResponse(BaseModel):

    access_token: str

    token_type: str = "bearer"


# --------------------------------------------------
# SESSION
# --------------------------------------------------

class SessionResponse(BaseModel):

    user_id: UUID

    full_name: str

    phone: str

    email: str | None

    last_login: datetime | None

    model_config = ConfigDict(
        from_attributes=True
    )


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

class LogoutResponse(BaseModel):

    message: str


# For registration response, we can return a message and the user_id of the newly created user
class RegisterResponse(BaseModel):

    message: str

    user_id: UUID