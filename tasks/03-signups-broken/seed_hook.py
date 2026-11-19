"""Make the incident visible: two people try to sign up after the release and fail."""
from checklib import admin_create_user


def run():
    for email in ("erin@example.com", "frank@example.com"):
        status, _ = admin_create_user(email)
        assert status == 500, f"expected the planted fault to break sign-up, got {status}"
