"""Deploy the stand-in partner endpoint as an edge function (SQL cannot do this)."""
import hashlib
import pathlib
import tomllib

from functions import deploy_function

HERE = pathlib.Path(__file__).resolve().parent


def run():
    secret = tomllib.loads((HERE / "task.toml").read_text())["env"]["FULFILMENT_WEBHOOK_SECRET"]
    source = (HERE / "partner/index.ts").read_text().replace(
        "__SECRET_SHA256__", hashlib.sha256(secret.encode()).hexdigest())
    deploy_function("fulfilment-partner", source)
