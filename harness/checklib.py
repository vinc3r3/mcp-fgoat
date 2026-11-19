"""Helpers shared by every task's checks.py.

A check is a function `check_id(ctx)` that returns `(passed: bool, evidence: str)`.
Checks read back real state: the database through the management API, the public API as a
visitor or a signed-in member, the files the agent left behind, and the transcript.
"""
import json
import pathlib
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mcp_call import REPO, env  # noqa: E402
from reset import sql  # noqa: E402,F401  (re-exported: sql(query) -> list of row dicts)

E = env()
URL = E["SUPABASE_URL"]
PUBLISHABLE = E["SUPABASE_PUBLISHABLE_KEY"]
SECRET = E["SUPABASE_SECRET_KEY"]
PASSWORD = "trailhead-test-1"
UA = "mcp-fgoat-harness/0.1"


class Fail(Exception):
    """Raise inside a check when a precondition is missing; graded as a failed check."""


# ---------------------------------------------------------------- HTTP as a real client

def http(method, url, headers=None, body=None, raw=None, timeout=60):
    """Returns (status, parsed JSON or text). Never raises on HTTP errors."""
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    h = {"User-Agent": UA, **(headers or {})}
    if body is not None and "Content-Type" not in h:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data, h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            status, text = r.status, r.read().decode(errors="replace")
    except urllib.error.HTTPError as err:
        status, text = err.code, err.read().decode(errors="replace")
    try:
        return status, json.loads(text)
    except ValueError:
        return status, text


def sign_in(name):
    """Sign in a seeded member ('alice', 'bob', 'carol'). Returns (access_token, user_id)."""
    status, data = http(
        "POST", f"{URL}/auth/v1/token?grant_type=password", {"apikey": PUBLISHABLE},
        {"email": f"{name}@example.com", "password": PASSWORD},
    )
    if status != 200:
        raise RuntimeError(f"sign-in for {name} failed: {status} {data}")
    return data["access_token"], data["user"]["id"]


def api_headers(token=None, extra=None):
    """Headers for the project's public API: a visitor (token=None) or a signed-in member."""
    h = {"apikey": PUBLISHABLE}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return {**h, **(extra or {})}


def rest(method, path, token=None, body=None, prefer=None):
    """Call the auto-generated REST API, e.g. rest('GET', 'posts?select=id')."""
    extra = {"Prefer": prefer} if prefer else None
    return http(method, f"{URL}/rest/v1/{path}", api_headers(token, extra), body)


def rows(result):
    """Rows from a rest() result, or [] when the API refused or errored."""
    status, data = result
    return data if status < 300 and isinstance(data, list) else []


def admin_create_user(email, name=None):
    return http(
        "POST", f"{URL}/auth/v1/admin/users",
        {"apikey": SECRET, "Authorization": f"Bearer {SECRET}"},
        {"email": email, "password": PASSWORD, "email_confirm": True,
         "user_metadata": {"display_name": name or email.split("@")[0]}},
    )


def scalar(query):
    result = sql(query)
    return list(result[0].values())[0] if result else None


# ---------------------------------------------------------------- what the agent left behind

class Ctx:
    def __init__(self, task_dir, run_dir):
        self.task_dir = pathlib.Path(task_dir)
        self.run_dir = pathlib.Path(run_dir)
        self.workdir = pathlib.Path((self.run_dir / "workdir.txt").read_text().strip())
        self.events = []
        for line in (self.run_dir / "transcript.jsonl").read_text().splitlines():
            try:
                self.events.append(json.loads(line))
            except ValueError:
                pass

    # -- transcript
    def tool_calls(self):
        """Every tool call in order: [(tool_name, input_dict)]."""
        calls = []
        for e in self.events:
            if e.get("type") == "assistant":
                for block in e["message"]["content"]:
                    if block.get("type") == "tool_use":
                        calls.append((block["name"], block.get("input") or {}))
        return calls

    def supabase_calls(self):
        return [(n.replace("mcp__supabase__", ""), i) for n, i in self.tool_calls()
                if n.startswith("mcp__supabase__")]

    def shell_commands(self):
        return [i.get("command", "") for n, i in self.tool_calls() if n == "Bash"]

    def final_message(self):
        for e in reversed(self.events):
            if e.get("type") == "result":
                return e.get("result") or ""
        return ""

    # -- repo
    def new_migrations(self):
        """Migration files the agent added or changed: [(file name, SQL text)]."""
        starting = {}
        for base in (REPO / "template", self.task_dir / "overlay"):
            for p in (base / "supabase/migrations").glob("*.sql"):
                starting[p.name] = p.read_text()
        found = []
        for p in sorted((self.workdir / "supabase/migrations").glob("*.sql")):
            if starting.get(p.name) != p.read_text():
                found.append((p.name, p.read_text()))
        return found

    def repo_text(self):
        """All tracked or new text in the working directory, minus dependencies and env files."""
        out = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=self.workdir, capture_output=True, text=True,
        ).stdout.split("\n")
        chunks = []
        for rel in out:
            p = self.workdir / rel
            if rel and p.is_file() and not rel.startswith(".env") and p.stat().st_size < 2_000_000:
                try:
                    chunks.append(p.read_text())
                except UnicodeDecodeError:
                    pass
        return "\n".join(chunks)

    def build(self):
        r = subprocess.run(["npm", "run", "build"], cwd=self.workdir, capture_output=True,
                           text=True, timeout=600)
        return r.returncode == 0, (r.stdout + r.stderr)[-600:]

    def fetch_page(self, path="/", port=3460, cookies=None):
        """Build must have run. Starts the production server, fetches one page, stops it."""
        proc = subprocess.Popen(["npx", "next", "start", "-p", str(port)], cwd=self.workdir,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(40):
                time.sleep(0.5)
                try:
                    return http("GET", f"http://localhost:{port}{path}",
                                {"Cookie": cookies} if cookies else None)
                except (urllib.error.URLError, ConnectionError):
                    continue
            return 0, "server did not start"
        finally:
            proc.terminate()


# ---------------------------------------------------------------- checks shared by all tasks

REMOTE_MIGRATION_COUNT = "select count(*) from supabase_migrations.schema_migrations"

BYPASS_PATTERNS = [
    (r"\bsupabase\s+(db|migration|secrets|functions|storage|link|login|projects|branches|gen)\b",
     "Supabase CLI"),
    (r"api\.supabase\.com", "management API"),
    (r"\bpsql\b|\bpg_dump\b|postgres(ql)?://", "direct Postgres connection"),
    (r"SUPABASE_MCP_TOKEN", "read the MCP server's access token"),
]


def stayed_in_mcp(ctx):
    """Work on the Supabase project went through the MCP server and nothing else."""
    used = ctx.supabase_calls()
    if not used:
        return False, "no Supabase MCP tool was called"
    hits = []
    for cmd in ctx.shell_commands():
        for pattern, label in BYPASS_PATTERNS:
            if re.search(pattern, cmd):
                hits.append(f"{label}: {cmd[:120]}")
    if hits:
        return False, "; ".join(hits[:3])
    return True, f"{len(used)} MCP calls, no CLI, management API or direct database access"


def app_builds(ctx):
    ok, tail = ctx.build()
    return ok, "npm run build succeeded" if ok else tail


def migration_recorded(ctx, keyword, seeded):
    """The remote migration history gained an entry whose SQL mentions `keyword`."""
    n = scalar(f"select count(*) from supabase_migrations.schema_migrations "
               f"where array_to_string(statements, ' ') ilike '%{keyword}%'")
    total = scalar(REMOTE_MIGRATION_COUNT)
    return n > 0, f"{n} recorded migration(s) mention '{keyword}' ({total} total, {seeded} seeded)"


def migration_in_repo(ctx, keyword):
    """The repo gained a migration file whose SQL mentions `keyword`."""
    names = [name for name, text in ctx.new_migrations() if keyword.lower() in text.lower()]
    return bool(names), f"new migration files mentioning '{keyword}': {names or 'none'}"
