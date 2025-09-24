from __future__ import annotations

"""
Simple HMAC-based signed URL generator/validator for local files.
"""

import base64
import hashlib
import hmac
import time
from urllib.parse import urlencode


def generate_signed_url(path: str, secret: str, expires_in: int = 900) -> str:
    exp = int(time.time()) + expires_in
    payload = f"{path}:{exp}".encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).digest()
    token = base64.urlsafe_b64encode(sig).decode("utf-8").rstrip("=")
    return f"{path}?{urlencode({'exp': exp, 'sig': token})}"


def validate_signed_url(path: str, secret: str, exp: int, sig: str) -> bool:
    if int(time.time()) > int(exp):
        return False
    payload = f"{path}:{exp}".encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).digest()
    expected_token = base64.urlsafe_b64encode(expected).decode("utf-8").rstrip("=")
    return hmac.compare_digest(expected_token, sig)


