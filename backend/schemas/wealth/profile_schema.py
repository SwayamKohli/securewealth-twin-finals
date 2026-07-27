from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


class ProfileRequest(BaseModel):
    aa_data: Dict[str, Any] = Field(..., description="Raw account aggregation data")


class ProfileResponse(BaseModel):
    profile: Dict[str, Any] = Field(..., description="Unified financial profile")