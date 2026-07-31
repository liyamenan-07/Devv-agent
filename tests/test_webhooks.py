import hashlib
import hmac

import pytest
from fastapi import HTTPException

from app.webhooks import verify_github_signature


def test_signature_validation_accepts_valid_signature():
    body, secret = b'{"ok": true}', "top-secret"
    sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    verify_github_signature(secret, body, sig)


def test_signature_validation_rejects_invalid_signature():
    with pytest.raises(HTTPException):
        verify_github_signature("secret", b"payload", "sha256=bad")
