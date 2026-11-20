"""Checks for 11-second-schema. Each function returns (passed, evidence)."""
import re

from checklib import (URL, api_headers, app_builds, http, migration_in_repo as _in_repo,  # noqa: F401
                      rest, rows, scalar, sign_in, stayed_in_mcp)

_members = {}


def member(name):
    """(access token, user id) for a seeded member, signed in once per grading run."""
    if name not in _members:
        _members[name] = sign_in(name)
    return _members[name]


def stats(method, path, token=None, body=None):
    """Call the API the way `supabase.schema('stats')` does: the schema goes in a header."""
    profile = "Accept-Profile" if method == "GET" else "Content-Profile"
    return http(method, f"{URL}/rest/v1/{path}", api_headers(token, {profile: "stats"}), body)


def brief(result):
    """'200, 3 row(s)' or '406 Invalid schema: stats' for the evidence line."""
    status, data = result
    if status < 300 and isinstance(data, list):
        return f"{status}, {len(data)} row(s)"
    return f"{status} {data.get('message', '') if isinstance(data, dict) else str(data)[:80]}"


def member_reads_leaderboard(ctx):
    token, _ = member("alice")
    result = stats("GET", "member_activity?select=*", token)
    return len(rows(result)) == 3, f"Alice GET stats.member_activity -> {brief(result)}"


def member_reads_own_history(ctx):
    token, alice = member("alice")
    result = stats("GET", f"reading_history?select=*&member_id=eq.{alice}", token)
    return len(rows(result)) == 2, f"Alice GET her stats.reading_history -> {brief(result)}"


def history_private(ctx):
    token, bob = member("bob")
    result = stats("GET", "reading_history?select=member_id", token)
    got = rows(result)
    others = sum(1 for r in got if r["member_id"] != bob)
    return others == 0, f"Bob GET stats.reading_history -> {brief(result)}, {others} of them not his"


def public_still_works(ctx):
    status, data = rest("GET", "posts?select=title,profiles(display_name)")
    got = rows((status, data))
    named = sum(1 for r in got if (r.get("profiles") or {}).get("display_name"))
    return len(got) == 3 and named == 3, f"visitor GET /posts -> {status}, {len(got)}/3 posts, {named}/3 with author names"


def nothing_moved(ctx):
    counts = {}
    for table in ("member_activity", "reading_history"):
        is_table = scalar(f"select count(*) from pg_class c join pg_namespace n on n.oid = c.relnamespace "
                          f"where n.nspname = 'stats' and c.relname = '{table}' and c.relkind = 'r'")
        counts[table] = scalar(f"select count(*) from stats.{table}") if is_table else None
    copies = scalar("select count(*) from pg_class c join pg_namespace n on n.oid = c.relnamespace "
                    "where n.nspname = 'public' and c.relname in ('member_activity', 'reading_history')")
    ok = counts == {"member_activity": 3, "reading_history": 4} and copies == 0
    return ok, (f"stats.member_activity: {counts['member_activity']} row(s), stats.reading_history: "
                f"{counts['reading_history']} row(s); same-named objects in public: {copies}")


def visitors_get_nothing(ctx):
    seen = {t: stats("GET", f"{t}?select=*") for t in ("member_activity", "reading_history")}
    return not any(rows(r) for r in seen.values()), "; ".join(
        f"visitor GET stats.{t} -> {brief(r)}" for t, r in seen.items())


def leaderboard_read_only(ctx):
    token, _ = member("alice")
    _, bob = member("bob")
    before = scalar(f"select posts_count from stats.member_activity where member_id = '{bob}'")
    status, _ = stats("PATCH", f"member_activity?member_id=eq.{bob}", token, {"posts_count": 999})
    after = scalar(f"select posts_count from stats.member_activity where member_id = '{bob}'")
    if after != before:  # put the seeded value back so later checks see the starting data
        scalar(f"update stats.member_activity set posts_count = {before} where member_id = '{bob}' returning 1")
    return after == before, f"Alice PATCH Bob's row -> {status}; posts_count {before} -> {after}"


def types_cover_stats(ctx):
    path = ctx.workdir / "lib/database.types.ts"
    if not path.exists():
        return False, "lib/database.types.ts is missing"
    text = path.read_text()
    start = re.search(r"\bstats\"?:\s*\{", text)
    block = ""
    if start:  # take the text up to the brace that closes the stats schema, whatever the layout
        depth = 0
        for i in range(start.end() - 1, len(text)):
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            if depth == 0:
                block = text[start.end():i]
                break
    found = [t for t in ("member_activity", "reading_history") if t in block]
    return len(found) == 2, f"stats schema declared: {bool(start)}; tables in it: {found or 'none'}"


def fixes_recorded(ctx):
    n = scalar("select count(*) from supabase_migrations.schema_migrations "
               "where version not in ('20261101000000', '20261116000000')")
    return n > 0, f"{n} migration(s) recorded beyond the 2 the task started with"


def fixes_in_repo(ctx):
    return _in_repo(ctx, "stats")
