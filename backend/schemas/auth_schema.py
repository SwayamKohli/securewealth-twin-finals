from datetime import date, datetime
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


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
    """
    Bank-grade login (task 2.2). `login_id` is the customer's SecureWealth ID
    (CIF-style, e.g. SW1A2B3C4D). The accepted identifier types are
    configurable via LOGIN_METHODS (CUSTOMER_ID and/or PHONE); phone login is
    disabled by default on evaluator guidance.
    """

    login_id: str = Field(
        min_length=6,
        max_length=20,
        validation_alias=AliasChoices("login_id", "customer_id", "phone"),
        description="SecureWealth ID / CIF (e.g. SW1A2B3C4D).",
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

    customer_id: str | None = None

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

    # The customer's permanent login identifier — shown ONCE at registration,
    # exactly like a bank issuing a CIF number.
    customer_id: str