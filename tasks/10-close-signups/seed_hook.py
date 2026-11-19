"""Refuse to start from an already-solved project: Auth settings survive the reset."""
from checklib import PUBLISHABLE, URL, http


def run():
    _, settings = http("GET", f"{URL}/auth/v1/settings", {"apikey": PUBLISHABLE})
    if settings.get("disable_signup"):
        raise SystemExit("Public sign-ups are already disabled on this project. Turn them back on "
                         "in the dashboard (Authentication > Sign In / Providers) before running this task.")
