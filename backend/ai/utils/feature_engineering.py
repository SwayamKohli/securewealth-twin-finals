"""
Feature Engineering Utilities for Fraud and Zero-Day Detection
"""
import numpy as np
from datetime import datetime
from typing import Dict, List, Any

# Define the feature columns that are used by both fraud_engine and zero_day_detector
FEATURE_COLS = [
    'hour_sin', 'hour_cos', 'day_sin', 'day_cos',
    'is_night_owl', 'amount_zscore', 'amount_ratio_to_median',
    'is_round_amount', 'otp_zscore', 'session_duration_minutes',
    'velocity_1h', 'velocity_24h', 'is_new_recipient',
    'is_new_device', 'time_since_last_login_minutes',
    'amount_times_otp_speed', 'session_count_recent',
    'amount_deviation_from_avg', 'time_since_account_creation_days',
    'device_trust_score', 'is_weekend', 'hour_category'
]

class FraudFeatureEngineer:
    """
    Feature engineering for fraud detection models.
    """
    def __init__(self, user_baselines: Dict[str, Any]):
        self.baselines = user_baselines

    def derive_features(self, transaction: Dict[str, Any]) -> Dict[str, float]:
        """
        Derive features from a transaction for fraud detection.
        """
        user_id = transaction.get('user_id', '')
        baseline = self.baselines.get(user_id) or self.baselines.get('__global_fallback__', {})
        
        hour = transaction.get('hour', 12)
        amount = transaction.get('amount', 0.0)
        otp_time = transaction.get('otp_time_sec', 9.5)
        
        # Hour encoding
        hour_rad = hour * 2 * np.pi / 24
        hour_sin = np.sin(hour_rad)
        hour_cos = np.cos(hour_rad)
        
        # Day encoding
        day = transaction.get('day_of_week', 0)
        day_rad = day * 2 * np.pi / 7
        day_sin = np.sin(day_rad)
        day_cos = np.cos(day_rad)
        
        # Baseline comparisons
        avg_amount = baseline.get('avg_amount', 5000.0)
        avg_otp_time = baseline.get('avg_otp_time', 9.5)
        
        amount_zscore = (amount - avg_amount) / max(baseline.get('std_amount', 1000.0), 1.0)
        otp_zscore = (otp_time - avg_otp_time) / max(baseline.get('std_otp_time', 3.0), 1.0)
        
        # Time-based features
        is_night_owl = 1.0 if (hour >= 23 or hour < 6) else 0.0
        is_weekend = 1.0 if day >= 5 else 0.0
        
        # Amount features
        median_amount = baseline.get('median_amount', 2000.0)
        amount_ratio = amount / max(median_amount, 1.0)
        is_round_amount = 1.0 if amount % 100 == 0 else 0.0
        
        # Velocity features
        txns_last_1h = transaction.get('txns_last_1h', 0)
        txns_last_24h = transaction.get('txns_last_24h', 0)
        
        # Recipient features
        recipient_id = transaction.get('recipient_id', '')
        known_recipients = baseline.get('known_recipients', [])
        is_new_recipient = 0.0 if recipient_id in known_recipients else 1.0
        
        # Device features
        device_id = transaction.get('device_id', '')
        known_devices = baseline.get('known_devices', [])
        is_new_device = 0.0 if device_id in known_devices else 1.0
        
        # Session features
        session_duration = transaction.get('session_duration', 120.0)
        session_duration_minutes = session_duration / 60.0
        
        # Composite features
        amount_times_otp_speed = amount * (1.0 / max(otp_time, 0.1))
        
        features = {
            'hour_sin': float(hour_sin),
            'hour_cos': float(hour_cos),
            'day_sin': float(day_sin),
            'day_cos': float(day_cos),
            'is_night_owl': float(is_night_owl),
            'amount_zscore': float(amount_zscore),
            'amount_ratio_to_median': float(amount_ratio),
            'is_round_amount': float(is_round_amount),
            'otp_zscore': float(otp_zscore),
            'session_duration_minutes': float(session_duration_minutes),
            'velocity_1h': float(txns_last_1h),
            'velocity_24h': float(txns_last_24h),
            'is_new_recipient': float(is_new_recipient),
            'is_new_device': float(is_new_device),
            'time_since_last_login_minutes': float(transaction.get('time_since_last_login_minutes', 0.0)),
            'amount_times_otp_speed': float(amount_times_otp_speed),
            'session_count_recent': float(transaction.get('session_count_recent', 0.0)),
            'amount_deviation_from_avg': abs(float(amount_zscore)),
            'time_since_account_creation_days': float(transaction.get('time_since_account_creation_days', 0.0)),
            'device_trust_score': float(transaction.get('device_trust_score', 0.5)),
            'is_weekend': float(is_weekend),
            'hour_category': float(1 if 9 <= hour <= 17 else 0)  # business hours
        }
        
        return features

    def derive_features_as_row(self, transaction: Dict[str, Any]) -> List[float]:
        """
        Derive features and return as an ordered list matching FEATURE_COLS.
        """
        features = self.derive_features(transaction)
        return [features[col] for col in FEATURE_COLS]