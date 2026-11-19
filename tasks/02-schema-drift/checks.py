"""Checks for 02-schema-drift. Each function returns (passed, evidence)."""
from checklib import Fail, scalar, sql, stayed_in_mcp  # noqa: F401
from reset import RESET_SQL

SNAPSHOT = """
  select table_name, column_name, data_type, is_nullable
  from information_schema.columns where table_schema = 'public'
  order by table_name, column_name
"""


def production_data_kept(ctx):
    posts = scalar("select count(*) from public.posts")
    if scalar("select to_regclass('public.post_reactions') is null"):
        return False, "the post_reactions table no longer exists"
    has_pinned = scalar("select count(*) from information_schema.columns where table_schema = 'public' "
                        "and table_name = 'posts' and column_name = 'pinned'")
    pinned = scalar("select count(*) from public.posts where pinned") if has_pinned else 0
    reactions = scalar("select count(*) from public.post_reactions")
    return (posts, pinned, reactions) == (3, 1, 4), f"posts: {posts}/3, pinned: {pinned}/1, reactions: {reactions}/4"


def pending_migration_applied(ctx):
    n = scalar("select count(*) from information_schema.columns where table_schema = 'public' "
               "and table_name = 'posts' and column_name = 'slug'")
    return n == 1, "posts.slug exists in production" if n else "posts.slug is missing in production"


def history_matches_repo(ctx):
    remote = {r["version"] for r in sql("select version from supabase_migrations.schema_migrations")}
    local = {p.name.split("_", 1)[0] for p in (ctx.workdir / "supabase/migrations").glob("*.sql")}
    return remote == local, (f"only in project history: {sorted(remote - local) or 'none'}; "
                             f"only in repo: {sorted(local - remote) or 'none'}")


def repo_rebuilds_production(ctx):
    """Destructive: wipes the project and replays the repo. Listed last for that reason."""
    production = sql(SNAPSHOT)
    sql(RESET_SQL)
    for path in sorted((ctx.workdir / "supabase/migrations").glob("*.sql")):
        try:
            sql(path.read_text())
        except SystemExit as err:
            raise Fail(f"replaying {path.name} on an empty database failed: {str(err)[:200]}")
    rebuilt = sql(SNAPSHOT)
    as_set = lambda snap: {tuple(r.values()) for r in snap}  # noqa: E731
    missing, extra = as_set(production) - as_set(rebuilt), as_set(rebuilt) - as_set(production)
    return not missing and not extra, (
        f"columns in production but not in a rebuild: {sorted(c[:2] for c in missing) or 'none'}; "
        f"in a rebuild but not in production: {sorted(c[:2] for c in extra) or 'none'}")
