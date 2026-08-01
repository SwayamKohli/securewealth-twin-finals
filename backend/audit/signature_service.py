# ==========================================================
# SecureWealth Twin - The Guardian Framework
# Signature Service: Ed25519 digital signatures for audit records.
#
# WHY Ed25519:
#   - Faster than RSA (signing & verification)
#   - Much smaller keys (32-byte public key vs RSA's 256+ bytes)
#   - Smaller signatures (64 bytes, fixed size)
#   - Modern, widely-vetted cryptographic standard
#   - Ideal for high-volume audit systems where many records
#     must be signed and verified quickly
# ==========================================================

from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

from .hash_chain import HashChainService

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

logger = logging.getLogger("guardian.signature_service")


class SignatureStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"


@dataclass
class KeyPair:
    private_key_pem: bytes
    public_key_pem: bytes


class SignatureService:
    """
    Provides Ed25519 signing and verification for audit records.

    Keys may be injected (dependency injection) so the same service
    can be reused by the replica verification engine and the recovery
    engine without re-loading keys each call.
    """

    def __init__(self, private_key: Ed25519PrivateKey | None = None) -> None:
        self._private_key = private_key

    # ------------------------------------------------------
    # Key management
    # ------------------------------------------------------
    @staticmethod
    def generate_keypair() -> KeyPair:
        """Generate a fresh Ed25519 keypair, returned as PEM bytes."""
        private_key = Ed25519PrivateKey.generate()
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        logger.info("Generated new Ed25519 keypair.")
        return KeyPair(private_key_pem=private_pem, public_key_pem=public_pem)

    @staticmethod
    def load_private_key(private_key_pem: bytes) -> Ed25519PrivateKey:
        """Load an Ed25519 private key from PEM bytes."""
        key = serialization.load_pem_private_key(private_key_pem, password=None)
        if not isinstance(key, Ed25519PrivateKey):
            raise ValueError("Provided PEM is not an Ed25519 private key.")
        return key

    @staticmethod
    def load_public_key(public_key_pem: bytes) -> Ed25519PublicKey:
        """Load an Ed25519 public key from PEM bytes."""
        key = serialization.load_pem_public_key(public_key_pem)
        if not isinstance(key, Ed25519PublicKey):
            raise ValueError("Provided PEM is not an Ed25519 public key.")
        return key

    # ------------------------------------------------------
    # Serialization
    # ------------------------------------------------------
    @staticmethod
    def _serialize(record: Dict[str, Any]) -> bytes:
        """
        Deterministically serialize an audit record before signing.

        Uses the exact same canonical representation as the hash chain
        service so both cryptographic operations operate on identical data.
        """

        canonical = HashChainService._canonical(record)

        return canonical.encode("utf-8")

    # ------------------------------------------------------
    # Signing / verification
    # ------------------------------------------------------
    def sign_audit_record(self, audit_record: Dict[str, Any]) -> str:
        """
        Sign the serialized audit record with the injected private key.
        Returns a base64-encoded signature string for storage.
        """
        if self._private_key is None:
            raise RuntimeError("No private key configured for signing.")
        message = self._serialize(audit_record)
        signature = self._private_key.sign(message)
        encoded = base64.b64encode(signature).decode("ascii")
        logger.debug("Signed audit record.")
        return encoded

    def verify_signature(
        self,
        audit_record: Dict[str, Any],
        signature_b64: str,
        public_key: Ed25519PublicKey,
    ) -> SignatureStatus:
        """
        Verify a base64 signature against the serialized record using the
        supplied public key. Returns VALID or INVALID.
        """
        message = self._serialize(audit_record)
        signature = base64.b64decode(signature_b64)
        try:
            public_key.verify(signature, message)
            return SignatureStatus.VALID
        except InvalidSignature:
            logger.warning("Signature verification failed.")
            return SignatureStatus.INVALID