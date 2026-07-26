from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    SAFE = "SAFE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class PhishingScanRequest(BaseModel):
    """Request schema for phishing detection."""
    message: str = Field(..., description="The message text to scan for phishing content")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for behavioral analysis")


class PhishingScanResponse(BaseModel):
    """Response schema for phishing detection results."""
    phishing_score: float = Field(..., ge=0.0, le=1.0, description="Phishing probability score (0.0-1.0)")
    risk_level: RiskLevel = Field(..., description="Risk classification")
    fired_signals: List[str] = Field(..., description="List of triggered phishing signals")
    detected_keywords: Dict[str, List[str]] = Field(..., description="Keywords/phrases detected by signal")
    signal_groups_fired: List[str] = Field(..., description="Categories of signals triggered")
    negative_signals_found: List[str] = Field(..., description="Benign indicators that reduce risk")
    signal_count: int = Field(..., description="Total number of signals fired")
    top_signal: Optional[str] = Field(None, description="Highest contributing signal")
    message: str = Field(..., description="Original message that was scanned")
    scanned_at: str = Field(..., description="Timestamp of the scan")