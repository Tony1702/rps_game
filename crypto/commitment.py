import hashlib
import secrets

def generate_nonce() -> str:
    return secrets.token_hex(32)

def make_commitment(vote: int, nonce: str) -> str:
    message = f"{vote}:{nonce}".encode("utf-8")
    return hashlib.sha256(message).hexdigest()

def verify_commitment(commitment: str, vote: int, nonce: str) -> bool:
    return secrets.compare_digest(commitment, make_commitment(vote, nonce))
