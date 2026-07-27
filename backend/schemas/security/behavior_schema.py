from pydantic import BaseModel, Field
from typing import List, Dict, Any


class BehaviorInput(BaseModel):
    transaction_hour_ist: int = Field(..., ge=0, le=23, description="Transaction hour in IST (0-23)")
    amount: float = Field(..., description="Transaction amount")
    ninety_day_median: float = Field(..., description="90-day median transaction amount")
    ninety_day_std: float = Field(..., description="90-day standard deviation")
    recipient_id: str = Field(..., description="Recipient identifier")
    known_recipients: List[str] = Field(..., description="List of known recipients")
    recent_transaction_timestamps: List[int] = Field(..., description="Recent transaction timestamps")
    last_20_amounts: List[float] = Field(..., description="Last 20 transaction amounts")
    otp_entry_ms: int = Field(9500, description="OTP entry time in milliseconds")


class BehaviorSignals(BaseModel):
    night_owl: bool = Field(False, description="Transaction outside normal hours")
    velocity_burst: bool = Field(False, description="Transaction velocity burst detected")
    amount_spike: bool = Field(False, description="Amount spike detected")
    new_recipient: bool = Field(False, description="New recipient detected")
    otp_distress: bool = Field(False, description="Fast OTP entry (distress)")
    otp_relay: bool = Field(False, description="Slow OTP entry (potential relay)")
    round_number_anomaly: bool = Field(False, description="Round number anomaly detected")
    
    def as_dict(self) -> Dict[str, bool]:
        return {
            "night_owl": self.night_owl,
            "velocity_burst": self.velocity_burst,
            "amount_spike": self.amount_spike,
            "new_recipient": self.new_recipient,
            "otp_distress": self.otp_distress,
            "otp_relay": self.otp_relay,
            "round_number_anomaly": self.round_number_anomaly,
        }
    
    def active(self) -> List[str]:
        return [k for k, v in self.as_dict().items() if v]