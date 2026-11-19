#!/usr/bin/env python3
"""Put the eval project into the known starting state for a task.

  harness/seed.py [task-dir]

1. Empties the project (harness/reset.py).
2. Creates three test members and a few posts on the template's baseline schema.
3. Applies every migration in the template and in the task's overlay, and records each in
   the remote migration history, so repo and database start in agreement. Migrations named
   in task.toml under `unapplied_migrations` are left out on purpose.
4. Runs the task's seed.sql, if any. This is where a task plants changes that are NOT in
   the migration history (data, or schema edits "made in the dashboard").
5. Runs the task's seed_hook.py, if any, for setup that SQL cannot do.
"""
import importlib.util
import tomllib
import json
import pathlib
import sys
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mcp_call import REPO, env  # noqa: E402
from reset import reset_all, sql  # noqa: E402

E = env()
PASSWORD = "trailhead-test-1"
USERS = [("alice@example.com", "Alice"), ("bob@example.com", "Bob"), ("carol@example.com", "Carol")]


def create_user(email, name):
    req = urllib.request.Request(
        f"{E['SUPABASE_URL']}/auth/v1/admin/users",
        json.dumps({"email": email, "password": PASSWORD, "email_confirm": True,
                    "user_metadata": {"display_name": name}}).encode(),
        {"apikey": E["SUPABASE_SECRET_KEY"], "Authorization": f"Bearer {E['SUPABASE_SECRET_KEY']}",
         "Content-Type": "application/json", "User-Agent": "mcp-fgoat-harness/0.1"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())["id"]
    except urllib.error.HTTPError as err:
        sys.exit(f"create user {email} -> {err.code}: {err.read().decode()[:400]}")


def quote(text):
    return "$seed$" + text + "$seed$"


def main():
    task_dir = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None

    reset_all()

    sql("create schema if not exists supabase_migrations;"
        "create table if not exists supabase_migrations.schema_migrations "
        "(version text primary key, statements text[], name text);")
    task = tomllib.loads((task_dir / "task.toml").read_text()) if task_dir else {}
    skip = set(task.get("unapplied_migrations", []))
    files = list((REPO / "template/supabase/migrations").glob("*.sql"))
    if task_dir:
        files += list((task_dir / "overlay/supabase/migrations").glob("*.sql"))
    files = sorted(files, key=lambda p: p.name)

    def apply(path):
        version, name = path.stem.split("_", 1)
        body = path.read_text()
        sql(body)
        sql(f"insert into supabase_migrations.schema_migrations (version, name, statements) "
            f"values ('{version}', '{name}', array[{quote(body)}]);")
        print("applied migration", path.name)

    apply(files[0])  # baseline schema first: members and posts depend on it

    ids = {name: create_user(email, name) for email, name in USERS}
    sql(f"""
      insert into public.posts (author_id, title, body, created_at) values
        ('{ids['Alice']}', 'Three days on the Rennsteig', 'Mist until noon every day, and worth it.', now() - interval '6 days'),
        ('{ids['Alice']}', 'Winter overnighter in the Harz', 'Minus eight and a frozen stove. Bring a spare lighter.', now() - interval '3 days'),
        ('{ids['Bob']}', 'Malerweg, stage four', 'The ladders are fine. The stairs after them are not.', now() - interval '1 day');
    """)
    print("created members and posts")

    for path in files[1:]:
        if path.name in skip:
            print("left unapplied on purpose:", path.name)
        else:
            apply(path)

    if task_dir and (task_dir / "seed.sql").exists():
        sql((task_dir / "seed.sql").read_text())
        print("applied task seed.sql")
    if task_dir and (task_dir / "seed_hook.py").exists():
        spec = importlib.util.spec_from_file_location("seed_hook", task_dir / "seed_hook.py")
        hook = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(hook)
        hook.run()
        print("ran task seed_hook.py")

    sql("notify pgrst, 'reload schema';")
    print("state:", sql("select (select count(*) from public.profiles) as profiles, "
                        "(select count(*) from public.posts) as posts, "
                        "(select count(*) from supabase_migrations.schema_migrations) as migrations"))


if __name__ == "__main__":
    # Seeding starts from a full reset, so a stalled network call is safe to retry from the top.
    for attempt in (1, 2, 3):
        try:
            main()
            break
        except (TimeoutError, urllib.error.URLError) as err:
            print(f"seed attempt {attempt} stalled ({err!r}); starting over", file=sys.stderr)
    else:
        sys.exit("seeding failed three times")
