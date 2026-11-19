#!/usr/bin/env python3
"""Return the eval project to an empty state.

Drops everything in the public schema, clears the migration history, and removes auth
users, storage buckets with their files and policies, and all edge functions. Uses the management API with the access
token from .env. Run before seeding a task.
"""
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mcp_call import env  # noqa: E402

E = env()
API = f"https://api.supabase.com/v1/projects/{E['SUPABASE_PROJECT_REF']}"
HEADERS = {
    "Authorization": f"Bearer {E['SUPABASE_ACCESS_TOKEN']}",
    "Content-Type": "application/json",
    "User-Agent": "mcp-fgoat-harness/0.1",
}

RESET_SQL = """
drop schema if exists public cascade;
create schema public;
grant usage on schema public to postgres, anon, authenticated, service_role;
alter default privileges in schema public grant all on tables to postgres, service_role;
alter default privileges in schema public grant all on functions to postgres, service_role;
alter default privileges in schema public grant all on sequences to postgres, service_role;
do $$ begin
  if to_regclass('supabase_migrations.schema_migrations') is not null then
    delete from supabase_migrations.schema_migrations;
  end if;
end $$;
delete from auth.users;
do $$ begin
  if to_regclass('vault.secrets') is not null then delete from vault.secrets; end if;
end $$;
do $$ declare p record; begin
  for p in select policyname from pg_policies where schemaname = 'storage' and tablename = 'objects' loop
    execute format('drop policy %I on storage.objects', p.policyname);
  end loop;
end $$;
notify pgrst, 'reload schema';
"""


def storage(method, path, body=None, tolerate=()):
    """Storage API as the service role: buckets cannot be emptied through SQL."""
    req = urllib.request.Request(
        f"{E['SUPABASE_URL']}/storage/v1/{path}", json.dumps(body).encode() if body is not None else None,
        {"apikey": E["SUPABASE_SECRET_KEY"], "Authorization": f"Bearer {E['SUPABASE_SECRET_KEY']}",
         "Content-Type": "application/json", "User-Agent": "mcp-fgoat-harness/0.1"}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as err:
        text = err.read().decode()[:300]
        if any(word in text for word in tolerate):
            return {"retry": text}
        sys.exit(f"storage {method} {path} -> {err.code}: {text}")


def reset_all():
    for bucket in storage("GET", "bucket") or []:
        # Emptying a bucket finishes in the background, so the delete may need a moment.
        for _ in range(10):
            storage("POST", f"bucket/{bucket['id']}/empty", {})
            if "retry" not in (storage("DELETE", f"bucket/{bucket['id']}", tolerate=("ResourceNotEmpty",)) or {}):
                break
            time.sleep(1)
    sql(RESET_SQL)
    for fn in api("GET", "/functions") or []:
        api("DELETE", f"/functions/{fn['slug']}")


def api(method, path, body=None):
    req = urllib.request.Request(
        API + path, json.dumps(body).encode() if body is not None else None, HEADERS, method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw.strip() else None
    except urllib.error.HTTPError as err:
        sys.exit(f"{method} {path} -> {err.code}: {err.read().decode()[:500]}")


def sql(query):
    # A statement that cannot get its lock should fail with a clear error, not stall the run.
    return api("POST", "/database/query", {"query": "set lock_timeout = '20s';\n" + query})


if __name__ == "__main__":
    reset_all()
    print("tables left in public:", sql("select count(*) from pg_tables where schemaname = 'public'"))
    print("migrations left:", sql("select count(*) from supabase_migrations.schema_migrations"))
