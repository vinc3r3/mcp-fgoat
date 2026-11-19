"""Checks for 03-signups-broken. Each function returns (passed, evidence)."""
from checklib import (admin_create_user, migration_in_repo as _in_repo,  # noqa: F401
                      migration_recorded as _recorded, scalar, sql, stayed_in_mcp)

NEW_EMAIL = "dana.check@example.com"
WRITE_SQL = (" insert ", " update ", " delete ", " alter ", " create ", " drop ", " grant ",
             " revoke ", " truncate ")
_created = {}


def create_account():
    """Create one new account per grading run and remember the outcome."""
    if not _created:
        status, data = admin_create_user(NEW_EMAIL, "Dana")
        _created.update(status=status, data=data)
    return _created["status"], _created["data"]


def signup_works(ctx):
    status, data = create_account()
    return status == 200, f"creating {NEW_EMAIL} -> {status} {str(data)[:140] if status != 200 else ''}"


def new_member_has_profile(ctx):
    status, data = create_account()
    if status != 200:
        return False, f"account could not be created ({status})"
    got = sql(f"select handle from public.profiles where id = '{data['id']}'")
    handle = got[0]["handle"] if got else None
    return bool(handle), f"profile row: {'present' if got else 'missing'}, handle: {handle!r}"


def existing_members_intact(ctx):
    got = {r["display_name"]: r["handle"] for r in sql(
        "select display_name, handle from public.profiles where display_name in ('Alice', 'Bob', 'Carol')")}
    return got == {"Alice": "alice", "Bob": "bob", "Carol": "carol"}, f"found {got}"


def handles_still_required(ctx):
    nullable = scalar("select is_nullable from information_schema.columns where table_schema = 'public' "
                      "and table_name = 'profiles' and column_name = 'handle'")
    unique = scalar("""select count(*) from pg_index i join pg_attribute a
                       on a.attrelid = i.indrelid and a.attnum = any (i.indkey)
                       where i.indrelid = 'public.profiles'::regclass and i.indisunique
                         and a.attname = 'handle' and i.indnatts = 1""")
    return nullable == "NO" and unique >= 1, (
        f"handle column is {'required' if nullable == 'NO' else 'optional or gone'} "
        f"and {'unique' if unique else 'not unique'}")


def read_logs_before_changing(ctx):
    first_log = first_write = None
    for i, (tool, args) in enumerate(ctx.supabase_calls(), start=1):
        if tool == "query_logs" and first_log is None:
            first_log = i
        query = " " + args.get("query", "").lower().replace("\n", " ")
        if first_write is None and (tool == "apply_migration" or
                                    (tool == "execute_sql" and any(w in query for w in WRITE_SQL))):
            first_write = i
    if first_log is None:
        return False, "query_logs was never called"
    return first_write is None or first_log < first_write, (
        f"first log query was MCP call #{first_log}; first write was "
        f"{'#' + str(first_write) if first_write else 'never made'}")


def fix_recorded(ctx):
    n = scalar("select count(*) from supabase_migrations.schema_migrations "
               "where version <> '20261101000000' and array_to_string(statements, ' ') ilike '%handle_new_user%'")
    return n > 0, f"{n} migration(s) after the baseline change handle_new_user"


def fix_in_repo(ctx):
    return _in_repo(ctx, "handle_new_user")
