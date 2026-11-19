"""Edge function and function-secret helpers for seed hooks and checks (management API)."""
import json
import pathlib
import sys
import urllib.error
import urllib.request
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from reset import API, HEADERS, api  # noqa: E402


def deploy_function(slug, source, verify_jwt=False):
    """Deploy a single-file edge function."""
    boundary = uuid.uuid4().hex
    metadata = json.dumps({"name": slug, "entrypoint_path": "index.ts", "verify_jwt": verify_jwt})
    body = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="metadata"\r\n'
        f"Content-Type: application/json\r\n\r\n{metadata}\r\n"
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="index.ts"\r\n'
        f"Content-Type: application/typescript\r\n\r\n{source}\r\n--{boundary}--\r\n"
    ).encode()
    headers = {**HEADERS, "Content-Type": f"multipart/form-data; boundary={boundary}"}
    req = urllib.request.Request(f"{API}/functions/deploy?slug={slug}", body, headers, method="POST")
    try:
        urllib.request.urlopen(req, timeout=90).read()
    except urllib.error.HTTPError as err:
        raise SystemExit(f"deploying {slug} -> {err.code}: {err.read().decode()[:400]}")


def set_secret(name, value):
    api("POST", "/secrets", [{"name": name, "value": value}])


def list_secrets():
    """Custom function secrets as {name: sha256 hex digest of the value}."""
    return {s["name"]: s.get("value") for s in api("GET", "/secrets") or []
            if not s["name"].startswith("SUPABASE_")}


def delete_secrets():
    names = list(list_secrets())
    if names:
        api("DELETE", "/secrets", names)
