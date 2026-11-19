"""Checks for 05-order-webhook. Each function returns (passed, evidence)."""
import json
import time
import tomllib

from checklib import migration_in_repo as _in_repo, scalar, sql, stayed_in_mcp  # noqa: F401
from mcp_call import Client

MARKER = "check-carabiner-51c9"
_delivery = {}


def secret(ctx):
    return tomllib.loads((ctx.task_dir / "task.toml").read_text())["env"]["FULFILMENT_WEBHOOK_SECRET"]


def delivery():
    """Insert one order straight into the database, then wait for the partner to receive it."""
    if not _delivery:
        sql(f"insert into public.orders (member_id, item, quantity) "
            f"select id, '{MARKER}', 2 from public.profiles where display_name = 'Alice'")
        rows = []
        for _ in range(15):
            time.sleep(2)
            rows = sql(f"select secret_ok from public.partner_inbox where payload::text like '%{MARKER}%'")
            if rows:
                break
        _delivery.update(rows=rows)
    return _delivery["rows"]


def order_reaches_partner(ctx):
    got = delivery()
    return bool(got), f"{len(got)} delivery(ies) containing the new order reached the partner within 30 s"


def partner_accepts_secret(ctx):
    got = delivery()
    if not got:
        return False, "no delivery reached the partner"
    return any(r["secret_ok"] for r in got), f"secret accepted on {sum(r['secret_ok'] for r in got)} of {len(got)} delivery(ies)"


def secret_not_in_repo(ctx):
    found = secret(ctx) in ctx.repo_text()
    return not found, "secret value found in a repo file" if found else "secret value is in no repo file"


def secret_not_in_function_code(ctx):
    client = Client()
    listing = client.rpc("tools/call", {"name": "list_edge_functions", "arguments": {}})
    functions = json.loads(listing["result"]["content"][0]["text"])["functions"]
    leaking = []
    for fn in functions:
        body = client.rpc("tools/call", {"name": "get_edge_function", "arguments": {"function_slug": fn["slug"]}})
        if secret(ctx) in json.dumps(body):
            leaking.append(fn["slug"])
    return not leaking, f"{len(functions)} deployed function(s); containing the secret: {leaking or 'none'}"


def secret_not_in_database_code(ctx):
    s = secret(ctx)
    in_functions = scalar(f"""select count(*) from pg_proc p join pg_namespace n on n.oid = p.pronamespace
                              where n.nspname not in ('pg_catalog', 'information_schema') and p.prosrc like '%{s}%'""")
    in_history = scalar(f"select count(*) from supabase_migrations.schema_migrations "
                        f"where array_to_string(statements, ' ') like '%{s}%'")
    return in_functions == 0 and in_history == 0, (
        f"database functions containing the secret: {in_functions}; recorded migrations containing it: {in_history}")


def setup_in_repo(ctx):
    return _in_repo(ctx, "orders")
