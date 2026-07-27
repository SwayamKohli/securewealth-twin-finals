from pydantic import BaseModel, Field
from typing import Dict, Any, List
from enum import Enum


class DeviceStatus(str, Enum):
    FIRST_TIME_USER = "FIRST_TIME_USER"
    NEW_DEVICE = "NEW_DEVICE"
    KNOWN_DEVICE = "KNOWN_DEVICE"
    TRUSTED_DEVICE = "TRUSTED_DEVICE"
    INACTIVE_DEVICE = "INACTIVE_DEVICE"
    SUSPICIOUS_DEVICE = "SUSPICIOUS_DEVICE"
    ZERO_DAY_DEVICE = "ZERO_DAY_DEVICE"


class DeviceTrustRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    device_identifier: str = Field(..., description="Device identifier")
    attributes: Dict[str, Any] = Field(..., description="Device attributes")


class DeviceTrustResponse(BaseModel):
    device_status: str = Field(..., description="Device trust status")
    device_age_days: int = Field(..., description="Days since first seen")
    device_confidence: int = Field(..., ge=0, le=100, description="Device confidence score (0-100)")
    security_signals: List[str] = Field(..., description="Security signals detected")