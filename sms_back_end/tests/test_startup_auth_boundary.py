from __future__ import annotations

import os
import subprocess
import sys


def test_tutor_auth_import_has_no_external_identity_dependency():
    """Tutor auth imports without RSA key files or another product's config."""
    env = os.environ.copy()
    for key in (
        "JWT_PRIVATE_KEY",
        "JWT_PUBLIC_KEY",
        "JWT_PRIVATE_KEY_PATH",
        "JWT_PUBLIC_KEY_PATH",
        "AUTH_ISSUER",
        "AUTH_AUDIENCE",
        "PUSH_BASE_URL",
    ):
        env.pop(key, None)

    code = """
from utils.auth.tokens import get_current_user
from utils.decode_encode_token import create_access_token
assert callable(get_current_user)
assert callable(create_access_token)
print('Tutor auth is standalone.')
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=os.getcwd(),
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "Tutor auth is standalone" in completed.stdout
