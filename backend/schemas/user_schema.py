from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from models.enums import RiskProfile


class UpdateUserRequest(BaseModel):
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=120,
        description="Updated full name of the user",
    )

    email: EmailStr | None = Field(
        default=None,
        description="Updated email address",
    )


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    full_name: str
    phone: str
    email: EmailStr | None
    date_of_birth: date | None
    risk_profile: RiskProfile
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    message: str



# Future:

# class UpdateUserRequest(BaseModel):
#     full_name: str
#     email: EmailStr | None = None
#     phone: str = Field(
#         ...,
#         min_length=10,
#         max_length=15,
#         description="Updated mobile number",
#     )