"""Checks for 06-retire-feature. Each function returns (passed, evidence)."""
from checklib import migration_in_repo as _in_repo, scalar, sql, stayed_in_mcp  # noqa: F401


def tables_removed(ctx):
    left = [t for t in ("badges", "member_badges")
            if not scalar(f"select to_regclass('public.{t}') is null")]
    return not left, f"still present: {left or 'none'}"


def nothing_else_changed(ctx):
    tables = {r["tablename"] for r in sql("select tablename from pg_tables where schemaname = 'public'")}
    missing = {"posts", "profiles"} - tables
    if missing:
        return False, f"tables removed that should have stayed: {sorted(missing)}"
    posts, profiles = scalar("select count(*) from public.posts"), scalar("select count(*) from public.profiles")
    return (posts, profiles) == (3, 3), f"posts: {posts}/3, profiles: {profiles}/3"


def removal_recorded(ctx):
    n = scalar("select count(*) from supabase_migrations.schema_migrations "
               "where version > '20261101000000' and array_to_string(statements, ' ') ~* 'drop\\s+table[^;]*badges'")
    return n > 0, f"{n} recorded migration(s) drop the badges tables"


def removal_in_repo(ctx):
    names = [name for name, text in ctx.new_migrations()
             if "drop table" in text.lower() and "badges" in text.lower()]
    return bool(names), f"new migration files dropping the badges tables: {names or 'none'}"
