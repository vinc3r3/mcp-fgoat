"""Deploy the stand-in partner endpoint as an edge function (SQL cannot do this)."""
import hashlib
import json
import pathlib
import tomllib
import urllib.error
import urllib.request
import uuid

from reset import API, HEADERS

HERE = pathlib.Path(__file__).resolve().parent
SLUG = "fulfilment-partner"


def run():
    secret = tomllib.loads((HERE / "task.toml").read_text())["env"]["FULFILMENT_WEBHOOK_SECRET"]
    source = (HERE / "partner/index.ts").read_text().replace(
        "__SECRET_SHA256__", hashlib.sha256(secret.encode()).hexdigest())
    boundary = uuid.uuid4().hex
    metadata = json.dumps({"name": SLUG, "entrypoint_path": "index.ts", "verify_jwt": False})
    body = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="metadata"\r\n'
        f"Content-Type: application/json\r\n\r\n{metadata}\r\n"
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="index.ts"\r\n'
        f"Content-Type: application/typescript\r\n\r\n{source}\r\n--{boundary}--\r\n"
    ).encode()
    headers = {**HEADERS, "Content-Type": f"multipart/form-data; boundary={boundary}"}
    req = urllib.request.Request(f"{API}/functions/deploy?slug={SLUG}", body, headers, method="POST")
    try:
        urllib.request.urlopen(req, timeout=90).read()
    except urllib.error.HTTPError as err:
        raise SystemExit(f"deploying {SLUG} -> {err.code}: {err.read().decode()[:400]}")
