from pathlib import Path

from audit.signature_service import SignatureService

KEY_DIR = Path("keys")
KEY_DIR.mkdir(exist_ok=True)

keypair = SignatureService.generate_keypair()

(KEY_DIR / "audit_private_key.pem").write_bytes(keypair.private_key_pem)
(KEY_DIR / "audit_public_key.pem").write_bytes(keypair.public_key_pem)

print("Audit keypair generated successfully.")