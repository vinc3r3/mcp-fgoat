"""Reference solution: set the function secret to the new value. Used to test the checks.

This goes through the management API, which the agent under test is not allowed to use;
it shows what the one-step fix looks like when a tool can set a secret's value.
"""
import pathlib
import tomllib

from functions import set_secret

HERE = pathlib.Path(__file__).resolve().parent


def run():
    set_secret("PARTNER_SECRET",
               tomllib.loads((HERE / "task.toml").read_text())["env"]["FULFILMENT_WEBHOOK_SECRET"])
