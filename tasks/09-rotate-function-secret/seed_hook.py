"""Deploy both functions, set the OLD secret, and let one order bounce.

After this the project is in the state the prompt describes: the partner expects the new
secret, the notify-partner function still sends the old one, and deliveries get a 401.
"""
import hashlib
import pathlib
import time
import tomllib

from functions import deploy_function, set_secret
from mcp_call import env
from reset import sql

HERE = pathlib.Path(__file__).resolve().parent
OLD_SECRET = "whsec_trailhead_sandbox_OLD_3fK9pW1zR6"


def run():
    new_secret = tomllib.loads((HERE / "task.toml").read_text())["env"]["FULFILMENT_WEBHOOK_SECRET"]
    partner = (HERE / "partner/index.ts").read_text().replace(
        "__SECRET_SHA256__", hashlib.sha256(new_secret.encode()).hexdigest())
    deploy_function("fulfilment-partner", partner)
    deploy_function("notify-partner",
                    (HERE / "overlay/supabase/functions/notify-partner/index.ts").read_text())
    set_secret("PARTNER_SECRET", OLD_SECRET)
    sql(f"insert into public.integration_settings (key, value) values "
        f"('notify_partner_url', '{env()['SUPABASE_URL']}/functions/v1/notify-partner')")
    sql("insert into public.orders (member_id, item, quantity) "
        "select id, 'Titanium tent pegs', 6 from public.profiles where display_name = 'Bob'")
    for _ in range(15):
        time.sleep(2)
        if sql("select 1 from public.partner_inbox where not secret_ok"):
            return
    raise SystemExit("the planted fault did not show: no rejected delivery reached the partner")
