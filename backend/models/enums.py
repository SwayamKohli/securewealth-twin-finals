from enum import StrEnum


class RiskProfile(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DeviceType(StrEnum):
    ANDROID = "ANDROID"
    IOS = "IOS"
    TABLET = "TABLET"
    LAPTOP = "LAPTOP"


class TrustStatus(StrEnum):
    TRUSTED = "TRUSTED"
    UNTRUSTED = "UNTRUSTED"
    PENDING = "PENDING"


class AccountType(StrEnum):
    SAVINGS = "SAVINGS"
    CURRENT = "CURRENT"
    SALARY = "SALARY"


class DepositType(StrEnum):
    FD = "FD"
    RD = "RD"


class LoanType(StrEnum):
    HOME = "HOME"
    CAR = "CAR"
    PERSONAL = "PERSONAL"
    EDUCATION = "EDUCATION"


class CardType(StrEnum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class TransactionChannel(StrEnum):
    UPI = "UPI"
    IMPS = "IMPS"
    NEFT = "NEFT"
    RTGS = "RTGS"
    CARD = "CARD"


class TransactionStatus(StrEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class RecommendationType(StrEnum):
    EMERGENCY_FUND = "EMERGENCY_FUND"
    FD = "FD"
    RD = "RD"
    SIP = "SIP"