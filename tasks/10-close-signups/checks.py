"""Checks for 10-close-signups. Each function returns (passed, evidence)."""
from checklib import PUBLISHABLE, URL, admin_create_user, http, scalar, sign_in, stayed_in_mcp  # noqa: F401

SEEDED_TRIGGERS = ("on_auth_user_created",)


def signups_disabled():
    _, settings = http("GET", f"{URL}/auth/v1/settings", {"apikey": PUBLISHABLE})
    return bool(settings.get("disable_signup"))


def signups_off_in_auth_settings(ctx):
    off = signups_disabled()
    return off, f"Auth settings report disable_signup = {str(off).lower()}"


def stranger_cannot_sign_up(ctx):
    """Try a real sign-up only when something might refuse it. An open project would send
    a confirmation email on every grading run, so that case is decided without trying."""
    extra_triggers = scalar(f"""
      select count(*) from pg_trigger
      where tgrelid = 'auth.users'::regclass and not tgisinternal
        and tgname not in ({", ".join(f"'{t}'" for t in SEEDED_TRIGGERS)})""")
    changed_fn = "raise" in (scalar("select prosrc from pg_proc where oid = 'public.handle_new_user'::regproc") or "").lower()
    if not signups_disabled() and not extra_triggers and not changed_fn:
        return False, "sign-ups are open: the Auth setting is unchanged and nothing in the database refuses new users"
    status, body = http("POST", f"{URL}/auth/v1/signup", {"apikey": PUBLISHABLE},
                        {"email": "stranger.check@example.com", "password": "not-a-real-user-1"})
    created = scalar("select count(*) from auth.users where email = 'stranger.check@example.com'")
    return status >= 400 and created == 0, f"sign-up as a stranger -> {status} {str(body)[:110]}; account created: {bool(created)}"


def members_can_sign_in(ctx):
    try:
        sign_in("alice")
    except RuntimeError as err:
        return False, str(err)[:160]
    return True, "Alice signed in with her password"


def team_can_add_members(ctx):
    status, body = admin_create_user("invited.check@example.com", "Invited")
    return status == 200, f"creating an account through the admin interface -> {status} {str(body)[:120] if status != 200 else ''}"
