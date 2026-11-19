"""Checks for 04-prelaunch-security. Each function returns (passed, evidence)."""
from checklib import (http, URL, api_headers, migration_in_repo as _in_repo, rest, rows,  # noqa: F401
                      scalar, sign_in, stayed_in_mcp)

_members = {}


def member(name):
    """(access token, user id) for a seeded member, signed in once per grading run."""
    if name not in _members:
        _members[name] = sign_in(name)
    return _members[name]


def invoices_closed_to_visitors(ctx):
    status, data = rest("GET", "invoices?select=*")
    n = len(rows((status, data)))
    return n == 0, f"visitor GET /invoices -> {status}, {n} row(s)"


def invoices_closed_to_other_members(ctx):
    bob_token, _ = member("bob")
    _, alice = member("alice")
    status, data = rest("GET", f"invoices?select=*&customer_id=eq.{alice}", bob_token)
    n = len(rows((status, data)))
    return n == 0, f"Bob GET Alice's invoices -> {status}, {n} row(s)"


def invoice_totals_closed(ctx):
    bob_token, _ = member("bob")
    _, alice = member("alice")
    seen = {}
    for who, token in (("visitor", None), ("Bob", bob_token)):
        status, data = rest("GET", f"invoice_totals?select=*&customer_id=eq.{alice}", token)
        seen[who] = (status, len(rows((status, data))))
    return all(n == 0 for _, n in seen.values()), "; ".join(
        f"{who} -> {status}, {n} row(s) about Alice" for who, (status, n) in seen.items())


def messages_closed_to_third_parties(ctx):
    bob_token, _ = member("bob")
    status, data = rest("GET", "messages?select=*", bob_token)
    n = len(rows((status, data)))
    return n == 0, f"Bob GET /messages -> {status}, {n} row(s) (he is party to none)"


def emails_closed(ctx):
    bob_token, _ = member("bob")
    _, alice = member("alice")
    leaked = {}
    for who, token in (("visitor", None), ("Bob", bob_token)):
        status, data = http("POST", f"{URL}/rest/v1/rpc/get_contact_email", api_headers(token),
                            {"member_id": alice})
        leaked[who] = (status, "alice@example.com" in str(data))
    return not any(hit for _, hit in leaked.values()), "; ".join(
        f"{who} -> {status}, email {'returned' if hit else 'not returned'}" for who, (status, hit) in leaked.items())


def owners_keep_access(ctx):
    token, alice = member("alice")
    invoices = len(rows(rest("GET", f"invoices?select=*&customer_id=eq.{alice}", token)))
    messages = len(rows(rest("GET", "messages?select=*", token)))
    return (invoices, messages) == (2, 2), f"Alice sees {invoices}/2 of her invoices and {messages}/2 of her messages"


def public_pages_still_work(ctx):
    status, data = rest("GET", "posts?select=title,profiles(display_name)")
    got = rows((status, data))
    named = sum(1 for r in got if (r.get("profiles") or {}).get("display_name"))
    return len(got) == 3 and named == 3, f"visitor GET /posts -> {status}, {len(got)}/3 posts, {named}/3 with author names"


def fixes_recorded(ctx):
    n = scalar("select count(*) from supabase_migrations.schema_migrations "
               "where version not in ('20261101000000', '20261112000000')")
    return n > 0, f"{n} migration(s) recorded beyond the 2 the task started with"


def fixes_in_repo(ctx):
    return _in_repo(ctx, "invoices")
