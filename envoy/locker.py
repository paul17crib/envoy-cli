"""Locker: encrypt and decrypt .env files using a passphrase."""

import base64
import hashlib
import os
from typing import Dict

LOCK_HEADER = "# envoy:locked"


class LockError(Exception):
    """Raised when locking or unlocking fails."""


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a 32-byte key from a passphrase and salt using PBKDF2."""
    return hashlib.pbkdf2_hmac("sha256", passphrase.encode(), salt, 200_000, dklen=32)


def lock_env(env: Dict[str, str], passphrase: str) -> str:
    """Serialize and encrypt an env dict. Returns a locked string."""
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        raise LockError("cryptography package is required: pip install cryptography")

    salt = os.urandom(16)
    key = _derive_key(passphrase, salt)
    fernet_key = base64.urlsafe_b64encode(key)
    f = Fernet(fernet_key)

    from envoy.parser import serialize_env
    plaintext = serialize_env(env).encode()
    token = f.encrypt(plaintext)

    salt_b64 = base64.b64encode(salt).decode()
    token_b64 = token.decode()
    return f"{LOCK_HEADER}\n# salt:{salt_b64}\n{token_b64}\n"


def unlock_env(locked_content: str, passphrase: str) -> Dict[str, str]:
    """Decrypt a locked env string and return the env dict."""
    try:
        from cryptography.fernet import Fernet, InvalidToken
    except ImportError:
        raise LockError("cryptography package is required: pip install cryptography")

    lines = locked_content.strip().splitlines()
    if not lines or lines[0].strip() != LOCK_HEADER:
        raise LockError("Content does not appear to be a locked envoy file.")

    try:
        salt_line = next(l for l in lines if l.startswith("# salt:"))
        token_line = next(l for l in lines if not l.startswith("#"))
    except StopIteration:
        raise LockError("Malformed locked file: missing salt or token.")

    salt = base64.b64decode(salt_line.removeprefix("# salt:"))
    key = _derive_key(passphrase, salt)
    fernet_key = base64.urlsafe_b64encode(key)
    f = Fernet(fernet_key)

    try:
        plaintext = f.decrypt(token_line.encode()).decode()
    except InvalidToken:
        raise LockError("Decryption failed: incorrect passphrase or corrupted file.")

    from envoy.parser import parse_env_string
    return parse_env_string(plaintext)


def is_locked(content: str) -> bool:
    """Return True if the content looks like a locked envoy file."""
    return content.strip().startswith(LOCK_HEADER)
