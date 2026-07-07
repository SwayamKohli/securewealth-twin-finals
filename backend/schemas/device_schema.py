from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from models.enums import DeviceType, TrustStatus


class RegisterDeviceRequest(BaseModel):
    device_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Device name",
    )

    device_type: DeviceType

    sim_id: str | None = Field(
        default=None,
        max_length=50,
        description="SIM identifier",
    )


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_id: UUID
    user_id: UUID
    device_name: str
    device_type: DeviceType
    sim_id: str | None
    trust_status: TrustStatus
    first_seen: datetime
    last_seen: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime