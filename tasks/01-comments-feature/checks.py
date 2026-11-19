"""Checks for 01-comments-feature. Each function returns (passed, evidence)."""
import re

from checklib import (Fail, app_builds, migration_in_repo as _in_repo,  # noqa: F401
                      migration_recorded as _recorded, rest, rows, scalar, sign_in, sql,
                      stayed_in_mcp)

MARKER = "check-7f3a"


def columns():
    """The prompt names the table but not its columns, so find them by what they point at."""
    fks = sql("""
      select a.attname as col, c.confrelid::regclass::text as target
      from pg_constraint c
      join pg_attribute a on a.attrelid = c.conrelid and a.attnum = any (c.conkey)
      where c.conrelid = to_regclass('public.comments') and c.contype = 'f'
    """)
    post = next((f["col"] for f in fks if f["target"] in ("posts", "public.posts")), None)
    author = next((f["col"] for f in fks if f["target"] in ("profiles", "public.profiles", "auth.users")), None)
    text = scalar(f"""
      select column_name from information_schema.columns
      where table_schema = 'public' and table_name = 'comments'
        and data_type in ('text', 'character varying')
        and column_name not in ('{post}', '{author}')
      order by ordinal_position limit 1
    """)
    if not (post and author and text):
        raise Fail(f"no usable public.comments table (post link: {post}, author link: {author}, text column: {text})")
    return post, author, text


def first_post():
    return scalar("select id from public.posts order by id limit 1")


def seed_comment(member_id, text):
    post, author, body = columns()
    return scalar(f"insert into public.comments ({post}, {author}, {body}) "
                  f"values ({first_post()}, '{member_id}', '{text}') returning id")


def add_comment(token, me, text, recorded_as=None):
    """Add a comment as a signed-in member. A design may take the author from the session or
    expect it in the request, so both shapes are tried."""
    post, author, body = columns()
    base = {post: first_post(), body: text}
    attempts = [dict(base, **{author: recorded_as})] if recorded_as else [base, dict(base, **{author: me})]
    for payload in attempts:
        result = rest("POST", "comments", token, payload, prefer="return=minimal")
        if result[0] < 300:
            break
    return result


_members = {}


def member(name):
    """(access token, user id) for a seeded member, signed in once per grading run."""
    if name not in _members:
        _members[name] = sign_in(name)
    return _members[name]


def visitor_can_read_comments(ctx):
    _, alice = member("alice")
    seed_comment(alice, f"{MARKER}-read")
    status, data = rest("GET", "comments?select=*")
    got = rows((status, data))
    return len(got) > 0, f"GET /comments as visitor -> {status}, {len(got)} row(s): {str(data)[:120]}"


def member_can_comment(ctx):
    token, alice = member("alice")
    status, data = add_comment(token, alice, f"{MARKER}-write")
    n = scalar(f"select count(*) from public.comments where {columns()[2]} = '{MARKER}-write'")
    return n == 1, f"POST /comments as Alice -> {status}; rows stored: {n}. {str(data)[:120]}"


def visitor_cannot_comment(ctx):
    post, author, body = columns()
    _, alice = member("alice")
    for payload in ({post: first_post(), body: f"{MARKER}-anon"},
                    {post: first_post(), body: f"{MARKER}-anon", author: alice}):
        status, _ = rest("POST", "comments", None, payload, prefer="return=minimal")
    n = scalar(f"select count(*) from public.comments where {body} = '{MARKER}-anon'")
    return n == 0, f"POST /comments as visitor -> {status}; rows stored: {n}"


def no_impersonation(ctx):
    post, author, body = columns()
    token, alice = member("alice")
    _, bob = member("bob")
    status, _ = add_comment(token, alice, f"{MARKER}-forged", recorded_as=bob)
    n = scalar(f"select count(*) from public.comments where {body} = '{MARKER}-forged' and {author} = '{bob}'")
    return n == 0, f"Alice posting as Bob -> {status}; rows recorded under Bob: {n}"


def delete_own_only(ctx):
    alice_token, alice = member("alice")
    bob_token, _ = member("bob")
    cid = seed_comment(alice, f"{MARKER}-delete")
    pk = scalar("""select a.attname from pg_index i join pg_attribute a
                   on a.attrelid = i.indrelid and a.attnum = any (i.indkey)
                   where i.indrelid = 'public.comments'::regclass and i.indisprimary limit 1""")
    rest("DELETE", f"comments?{pk}=eq.{cid}", bob_token)
    after_bob = scalar(f"select count(*) from public.comments where {pk} = '{cid}'")
    rest("DELETE", f"comments?{pk}=eq.{cid}", alice_token)
    after_alice = scalar(f"select count(*) from public.comments where {pk} = '{cid}'")
    return after_bob == 1 and after_alice == 0, (
        f"after Bob's delete the row {'survived' if after_bob else 'was deleted'}; "
        f"after Alice's delete it {'is gone' if not after_alice else 'is still there'}")


def comments_on_home_page(ctx):
    _, alice = member("alice")
    seed_comment(alice, f"{MARKER}-page")
    ok, tail = ctx.build()
    if not ok:
        return False, f"build failed: {tail[-200:]}"
    status, html = ctx.fetch_page("/")
    return status == 200 and f"{MARKER}-page" in str(html), (
        f"GET / -> {status}; comment text {'found' if f'{MARKER}-page' in str(html) else 'not found'} in the HTML")


def reachable_from_first_migration(ctx):
    for n, (tool, args) in enumerate(ctx.supabase_calls(), start=1):
        query = args.get("query", "")
        if tool in ("apply_migration", "execute_sql") and re.search(r"create\s+table[^;(]*comments", query, re.I):
            granted = bool(re.search(r"grant\s[^;]*\bcomments\b", query, re.I))
            return granted, (f"MCP call #{n} created the table "
                             f"{'and granted it to the API roles' if granted else 'with no grant: the API refused every request until a later fix'}")
    return False, "no MCP call created the comments table"


def migration_recorded(ctx):
    return _recorded(ctx, "comments", seeded=1)


def migration_in_repo(ctx):
    return _in_repo(ctx, "comments")
