# from typing import Generator

# from fastapi import Depends, HTTPException, status
# from sqlalchemy.orm import Session

# from core.security import decode_access_token
# from database.connection import SessionLocal
# from models.user import User


# from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# security = HTTPBearer()


# # ----------------------------------------------------
# # DATABASE
# # ----------------------------------------------------

# #This function says: Create DB Session -> Give it to the API -> When API finishes -> Automatically close it
# #This prevents connection leaks.
# def get_db():
#     db = SessionLocal()

#     try:
#         yield db    #FastAPI pauses at yield, gives the session to the endpoint, and once the endpoint finishes, execution resumes after yield, allowing db.close() to run.

#     finally:
#         db.close()


# # ----------------------------------------------------
# # CURRENT USER
# # ----------------------------------------------------


# def get_current_user(

#     credentials: HTTPAuthorizationCredentials = Depends(
#         security
#     ),

#     db: Session = Depends(
#         get_db
#     ),

# ):

#     # Extract JWT from the Authorization header
#     token = credentials.credentials

#     payload = decode_access_token(
#         token
#     )

#     if not payload:

#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid or expired token",
#         )

#     user_id = payload.get("sub")

#     if user_id is None:

#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid token payload",
#         )

#     user = db.get(
#         User,
#         user_id,
#     )

#     if user is None:

#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="User not found",
#         )

#     return user


from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from database.connection import SessionLocal
from pathlib import Path

from functools import lru_cache


from audit.hash_chain import HashChainService
from audit.signature_service import SignatureService
from audit.replica_verifier import ReplicaVerifier
from audit.recovery_service import RecoveryService
from audit.tamper_monitor import TamperMonitor

from database.repositories.audit_repository import AuditRepository
from services.audit_service import AuditService
from core.security import decode_access_token
from database.connection import SessionLocal
from models.user import User
from database.repositories.audit_repository import AuditRepository
from services.audit_service import AuditService

security = HTTPBearer()


# ----------------------------------------------------
# DATABASE
# ----------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """
    Create a database session for each request and
    automatically close it afterwards.
    """
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ----------------------------------------------------
# CURRENT USER
# ----------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Retrieve the authenticated user from the JWT token.
    """

    token = credentials.credentials

    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


# ----------------------------------------------------
# AUDIT SERVICE
# ----------------------------------------------------

def get_audit_service(
    db: Session = Depends(get_db),
) -> AuditService:

    repository = AuditRepository(db)

    return AuditService(
        audit_repo=repository,
        hash_service=get_hash_chain_service(),
        signature_service=get_signature_service(),
    )

@lru_cache
def get_hash_chain_service() -> HashChainService:
    return HashChainService()

@lru_cache
def get_signature_service() -> SignatureService:

    private_key = SignatureService.load_private_key(
        Path("keys/audit_private_key.pem").read_bytes()
    )

    return SignatureService(
        private_key=private_key,
    )

def get_replica_verifier(
    db: Session = Depends(get_db),
) -> ReplicaVerifier:

    return ReplicaVerifier(
        AuditRepository(db),
    )

def get_recovery_service(
    db: Session = Depends(get_db),
) -> RecoveryService:

    return RecoveryService(
        AuditRepository(db),
    )

def get_tamper_monitor(
    db: Session = Depends(get_db),
) -> TamperMonitor:

    signature_service = get_signature_service()

    return TamperMonitor(
        hash_service=get_hash_chain_service(),

        signature_service=signature_service,

        replica_verifier=get_replica_verifier(db),

        recovery_service=get_recovery_service(db),

        audit_service=get_audit_service(db),

        public_key = SignatureService.load_public_key(Path("keys/audit_public_key.pem").read_bytes()),
    )



def build_tamper_monitor() -> TamperMonitor:
    """
    Creates a TamperMonitor outside FastAPI dependency injection.
    Used by the background scheduler.
    """

    db = SessionLocal()

    repository = AuditRepository(db)

    hash_service = get_hash_chain_service()
    signature_service = get_signature_service()

    audit_service = AuditService(
        audit_repo=repository,
        hash_service=hash_service,
        signature_service=signature_service,
    )

    replica_verifier = ReplicaVerifier(repository)

    recovery_service = RecoveryService(repository)

    return TamperMonitor(
        hash_service=hash_service,
        signature_service=signature_service,
        replica_verifier=replica_verifier,
        recovery_service=recovery_service,
        audit_service=audit_service,
        public_key = SignatureService.load_public_key(Path("keys/audit_public_key.pem").read_bytes()),
    )