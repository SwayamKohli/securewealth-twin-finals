from __future__ import annotations

from typing import Any
from uuid import UUID

from models.audit import AuditLog
from models.audit_replica import (
    AuditReplica1,
    AuditReplica2,
    AuditReplica3,
)
from database.repositories.audit_repository import AuditRepository
from schemas.audit_schema import ReplicaVerificationResult


class ReplicaVerifier:

    def __init__(
        self,
        repository: AuditRepository,
        signature_service=None,
        public_key=None,
    ):
        self._repo = repository
        # Optional but strongly recommended: with the Ed25519 public key the
        # verifier can tell a GENUINE copy from a tampered one cryptographically,
        # instead of relying on head-count alone.
        self._signature = signature_service
        self._public_key = public_key

    def verify(
        self,
        audit_id: UUID,
    ) -> ReplicaVerificationResult:
        """
        Verify one audit record across the master and all three replicas using
        MAJORITY CONSENSUS.

        Why consensus and not "compare replicas against master":
            The realistic attack is an insider editing the MASTER row in
            `audit_logs` to hide a fraudulent decision. If the master were
            trusted as the reference, every replica would be declared corrupt
            and then "repaired" with the attacker's version — the tamper would
            be propagated instead of healed.

            Treating all four copies as equal voters means the three untouched
            replicas out-vote the tampered master, the master is flagged as
            CORRUPTED, and recovery restores the original value.
        """
        master = self._repo.get_by_id(audit_id)

        if master is None:
            raise ValueError(f"Audit record {audit_id} does not exist.")

        replicas = self._repo.get_all_replicas(audit_id)

        # ── Collect every available copy as an equal voter ──────────────────
        copies: dict[str, dict[str, Any]] = {"master": self._to_dict(master)}
        behind: list[str] = []

        for replica_name, replica in replicas.items():
            if replica is None:
                # Replica hasn't received the record yet — not a vote, and not
                # corruption either.
                behind.append(replica_name)
                continue
            copies[replica_name] = self._to_dict(replica)

        # ── Cryptographic authority (beats head-count) ───────────────────────
        # A pure majority vote loses if an attacker edits 3 of the 4 copies to
        # the same forged value. Signatures close that hole: the Ed25519
        # signature is generated with a private key the attacker does not have,
        # so ANY altered copy fails verification no matter how many rows they
        # change. A single signature-valid copy therefore outranks any number
        # of agreeing forgeries.
        signed_ok = self._signature_valid_copies(copies, master, replicas)

        if signed_ok:
            consensus_members = set(signed_ok)
            consensus_data = copies[next(iter(consensus_members))]
            authority = "cryptographic_signature"
        else:
            # No usable key (or every signature failed) — fall back to content
            # majority so the system still self-heals in a degraded mode.
            authority = "content_majority"
            votes: dict[str, list[str]] = {}
            for name, data in copies.items():
                votes.setdefault(self._fingerprint(data), []).append(name)
            consensus_key = max(
                votes,
                key=lambda k: (
                    len(votes[k]),
                    sum(1 for n in votes[k] if n != "master"),
                ),
            )
            consensus_members = set(votes[consensus_key])
            consensus_data = copies[next(iter(consensus_members))]

        # Legacy fingerprint vote retained for reporting only.
        votes = {}
        for name, data in copies.items():
            votes.setdefault(self._fingerprint(data), []).append(name)

        comparison: dict[str, dict] = {}
        corrupted: list[str] = []
        healthy = 0

        for name, data in copies.items():
            if name in consensus_members:
                comparison[name] = {"status": "HEALTHY", "mismatched_fields": []}
                healthy += 1
            else:
                comparison[name] = {
                    "status": "CORRUPTED",
                    "mismatched_fields": self._compare(consensus_data, data),
                }
                corrupted.append(name)

        for name in behind:
            comparison[name] = {"status": "REPLICA_BEHIND", "mismatched_fields": []}

        # Surface HOW the truth was established, for the audit trail and UI.
        comparison["_authority"] = {
            "status": authority,
            "mismatched_fields": [],
            "signature_valid_copies": sorted(signed_ok) if signed_ok else [],
            "majority_holders": sorted(max(votes.values(), key=len)),
        }

        return ReplicaVerificationResult(
            audit_id=audit_id,

            comparison=comparison,

            healthy_copies=healthy,

            corrupted_copies=corrupted,

            replicas_behind=behind,

            recovery_required=len(corrupted) > 0,

            # With cryptographic authority a SINGLE signature-valid copy is
            # provably genuine, so it alone is enough to restore from. Without
            # a key we fall back to needing an actual majority.
            recovery_possible=(
                healthy >= 1
                if authority == "cryptographic_signature"
                else healthy >= 2
            ),
        )

    def _signature_valid_copies(
        self,
        copies: dict[str, dict[str, Any]],
        master,
        replicas: dict[str, Any],
    ) -> list[str]:
        """Names of copies whose Ed25519 signature verifies against the key."""
        if self._signature is None or self._public_key is None:
            return []

        from audit.signature_service import SignatureStatus

        objects = {"master": master}
        objects.update({k: v for k, v in replicas.items() if v is not None})

        valid: list[str] = []
        for name, obj in objects.items():
            signature = getattr(obj, "digital_signature", None)
            if not signature:
                continue
            try:
                status = self._signature.verify_signature(
                    audit_record=copies[name],
                    signature_b64=signature,
                    public_key=self._public_key,
                )
                if status == SignatureStatus.VALID:
                    valid.append(name)
            except Exception:
                continue
        return valid

    @staticmethod
    def _fingerprint(data: dict[str, Any]) -> str:
        """Stable content fingerprint used for majority voting."""
        import hashlib

        parts = [f"{k}={data[k]!r}" for k in sorted(data)]
        return hashlib.sha256("|".join(parts).encode()).hexdigest()

    @staticmethod
    def _compare(
        source: dict[str, Any],
        target: dict[str, Any],
    ) -> list[str]:

        mismatches = []

        for key, value in source.items():

            if target.get(key) != value:
                mismatches.append(key)

        return mismatches

    @staticmethod
    def _to_dict(
        record: AuditLog
        | AuditReplica1
        | AuditReplica2
        | AuditReplica3,
    ) -> dict[str, Any]:

        # excluded = {
        #     "_sa_instance_state",
        #     "replica_record_id",
        #     "replica_name",
        #     "created_at",
        #     "updated_at",
        #     "chain_index",
        # }
        
        FIELDS_TO_COMPARE = {
            "audit_id",
            "transaction_id",
            "user_id",
            "device_id",
            "account_id",
            "event_type",
            "final_decision",
            "risk_score",
            "amount",
            "channel",
            "ai_status",
            "ai_confidence",
            "unknown_risk_severity",
            "unknown_risk_applied",
            "unknown_risk_decision",
            "unknown_risk_reason_code",
            "challenge_required",
            "challenge_type",
            "challenge_trigger_signal",
            "security_signals",
            "audit_note",
            "compliance_reference",
            "previous_hash",
            "current_hash",
            "digital_signature",
            "signature_algorithm",
            "record_status",
        }
        return {
            key: value
            for key, value in vars(record).items()
            if key in FIELDS_TO_COMPARE
        }