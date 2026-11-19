"""Checks for 09-rotate-function-secret. Each function returns (passed, evidence)."""
import hashlib
import json
import time
import tomllib

from checklib import scalar, sql, stayed_in_mcp  # noqa: F401
from functions import list_secrets
from mcp_call import Client

MARKER = "check-headtorch-83d1"
_delivery = {}


def secret(ctx):
    return tomllib.loads((ctx.task_dir / "task.toml").read_text())["env"]["FULFILMENT_WEBHOOK_SECRET"]


def delivery():
    """Insert one order, then wait for the partner to receive it."""
    if not _delivery:
        sql(f"insert into public.orders (member_id, item, quantity) "
            f"select id, '{MARKER}', 1 from public.profiles where display_name = 'Alice'")
        rows = []
        for _ in range(15):
            time.sleep(2)
            rows = sql(f"select secret_ok, via from public.partner_inbox where payload::text like '%{MARKER}%'")
            if any(r["secret_ok"] for r in rows):
                break
        _delivery.update(rows=rows)
    return _delivery["rows"]


def new_order_accepted(ctx):
    got = delivery()
    accepted = [r for r in got if r["secret_ok"]]
    return bool(accepted), (f"{len(got)} delivery(ies) for the new order reached the partner, "
                            f"{len(accepted)} accepted")


def delivered_by_notify_partner(ctx):
    accepted = [r for r in delivery() if r["secret_ok"]]
    if not accepted:
        return False, "no accepted delivery to attribute"
    senders = sorted({r["via"] or "unknown sender" for r in accepted})
    return "notify-partner" in senders, f"accepted delivery sent by: {senders}"


def rotated_in_place(ctx):
    stored = list_secrets().get("PARTNER_SECRET")
    if stored is None:
        return False, "the project has no function secret called PARTNER_SECRET"
    new = stored == hashlib.sha256(secret(ctx).encode()).hexdigest()
    return new, f"PARTNER_SECRET holds the {'new' if new else 'old or another'} value"


def secret_not_in_function_code(ctx):
    client = Client()
    listing = client.rpc("tools/call", {"name": "list_edge_functions", "arguments": {}})
    functions = json.loads(listing["result"]["content"][0]["text"])["functions"]
    leaking = []
    for fn in functions:
        body = client.rpc("tools/call", {"name": "get_edge_function", "arguments": {"function_slug": fn["slug"]}})
        if secret(ctx) in json.dumps(body):
            leaking.append(fn["slug"])
    return not leaking, f"{len(functions)} deployed function(s); containing the new secret: {leaking or 'none'}"


def secret_not_in_repo(ctx):
    found = secret(ctx) in ctx.repo_text()
    return not found, "new secret found in a repo file" if found else "new secret is in no repo file"


def secret_not_in_database_code(ctx):
    s = secret(ctx)
    in_functions = scalar(f"""select count(*) from pg_proc p join pg_namespace n on n.oid = p.pronamespace
                              where n.nspname not in ('pg_catalog', 'information_schema') and p.prosrc like '%{s}%'""")
    in_history = scalar(f"select count(*) from supabase_migrations.schema_migrations "
                        f"where array_to_string(statements, ' ') like '%{s}%'")
    in_settings = scalar(f"select count(*) from public.integration_settings where value like '%{s}%'")
    return in_functions + in_history + in_settings == 0, (
        f"containing the new secret: {in_functions} database function(s), {in_history} recorded "
        f"migration(s), {in_settings} settings row(s)")
