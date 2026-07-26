from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


class ChallengeContext(BaseModel):
    active_behavior: List[str] = Field(..., description="Active behavioral signals")
    device: Dict[str, Any] = Field({}, description="Device information")
    risk_score: Optional[int] = Field(None, description="Risk score")
    unknown_risk: Optional[str] = Field(None, description="Unknown risk status")


class ChallengeRequirement(BaseModel):
    challenge_required: bool = Field(..., description="Whether challenge is required")
    challenge_type: str = Field("", description="Type of challenge")
    trigger_signal: str = Field("", description="Signal that triggered the challenge")
    
    def as_dict(self) -> Dict[str, Any]:
        return {
            "challenge_required": self.challenge_required,
            "challenge_type": self.challenge_type,
            "trigger_signal": self.trigger_signal,
        }


class ChallengeRequest(BaseModel):
    context_data: Dict[str, Any] = Field(..., description="Challenge context data")