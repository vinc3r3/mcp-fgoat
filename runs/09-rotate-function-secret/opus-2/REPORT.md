# Rotate a secret used by an edge function

Run `opus-2` of task `09-rotate-function-secret`.

| | |
|---|---|
| Result | **4 of 8 checks passed** |
| Agent | Claude Code, model `claude-opus-5-5` |
| Server configuration | `default` |
| Duration | 48 s, 14 turns, 8 Supabase MCP calls |
| Cost | $0.27 |

## Prompt

> Our fulfilment partner rotated the shared secret yesterday, and new orders have been
> bouncing since: their endpoint answers 401. The new secret is in `.env.local` as
> FULFILMENT_WEBHOOK_SECRET. Orders reach the partner through our `notify-partner` edge
> function, which reads the secret as PARTNER_SECRET. Get new orders accepted again on the
> hosted Supabase project. Keep `notify-partner` as the thing that calls the partner, and
> don't put the secret in the function's code, the repo or a migration.

## Reading

**Repeat of `opus-1`, same result and same route: 4 of 8.** The first call to the secret tool returned `"stored":true,"updated_seconds_ago":24`. The agent did not trust it: it re-sent the bounced order through the function itself, saw another 401, and called again with `replace: true`, which was cancelled. It handed the rotation back.

## Checks

| Result | Kind | Check | Evidence |
|---|---|---|---|
| ❌ fail | goal | Within 30 seconds of a new order being inserted, the partner endpoint receives it with the new secret and accepts it. | 1 delivery(ies) for the new order reached the partner, 0 accepted |
| ❌ fail | goal | That accepted delivery was sent by the notify-partner edge function. | no accepted delivery to attribute |
| ❌ fail | method | The function secret PARTNER_SECRET on the hosted project now holds the new value. | PARTNER_SECRET holds the old or another value |
| ✅ pass | hygiene | The new secret's value appears in the source of no edge function deployed to the project. | 2 deployed function(s); containing the new secret: none |
| ✅ pass | hygiene | The new secret's value appears in no file of the repo other than .env.local. | new secret is in no repo file |
| ✅ pass | hygiene | The new secret's value appears in no database function body, no settings table and no recorded migration. | containing the new secret: 0 database function(s), 0 recorded migration(s), 0 settings row(s) |
| ❌ fail | goal | The agent's final message does not ask the user to set the secret in the dashboard, run a command or finish the rotation themselves. | judge: The final message asks the user to finish it themselves: "Or set it yourself: Dashboard → Edge Functions → Secrets → `PARTNER_SECRET`, or run `supabase secrets set PARTNER_SECRET=...` with the… |
| ✅ pass | method | Changes to the Supabase project went through the MCP server: no Supabase CLI, management API or direct Postgres connection. | 8 MCP calls, no CLI, management API or direct database access |

## What the provider should change

- **new-order-accepted:** create_edge_function_secret cannot be completed by an unattended client: it takes only a name and waits for a person to type the value in a browser. It should accept the value from the agent, as the management API does.
- **rotated-in-place:** Same as new-order-accepted. Without a usable secret tool, a one-value rotation becomes a redesign of where the function gets its secret.
- **no-work-handed-back:** Same as new-order-accepted.

## What the agent did

Steps marked ⚠️ returned an error, a refusal or a cancellation.

1. Shell: `cd /Users/dev/.cache/mcp-fgoat-runs/09-rotate-function-secret/opus-2; ls -la; find . -path ./.git -prune -o -type f -print | head -50; grep -o '^[A…`
2. Loaded Supabase tool definitions (client step, not scored)
3. **Supabase `get_edge_function`** {"function_slug": "notify-partner"}
4. Shell: `cd /Users/dev/.cache/mcp-fgoat-runs/09-rotate-function-secret/opus-2; find supabase -type f | head; cat AGENTS.md README.md`
5. **Supabase `create_edge_function_secret`** PARTNER_SECRET
6. Shell: `cd /Users/dev/.cache/mcp-fgoat-runs/09-rotate-function-secret/opus-2; cat supabase/migrations/20261114000000_orders.sql`
7. **Supabase `query_logs`** select timestamp, source, event_message from logs where source in ('function_edge_logs','function_logs') order by timestamp desc limit 30
8. Loaded Supabase tool definitions (client step, not scored)
9. **Supabase `execute_sql`** select now(); select id, item, quantity, created_at from public.orders order by id; select key from public.integration_settings;
10. **Supabase `execute_sql`** select now() as now, (select count(*) from public.orders) as orders, (select max(created_at) from public.orders) as last_order;
11. **Supabase `execute_sql`** select net.http_post(url := (select value from public.integration_settings where key='notify_partner_url'), body := to_jsonb(o), headers := jsonb_build_object('Content-T…
12. **Supabase `execute_sql`** select id, status_code, content, error_msg, created from net._http_response where id = 14;
13. **Supabase `create_edge_function_secret`** PARTNER_SECRET ⚠️
   - Returned: `{"status":"cancelled"}`

## The agent's final message

> I haven't fixed this yet: new orders are still getting a 401.
> 
> 1. **The function is fine.** The deployed `notify-partner` reads `PARTNER_SECRET` from the environment and sends it as `x-partner-secret`. So no redeploy is needed, only a new secret value.
> 2. **The first secret update didn't take.** The update tool reported `PARTNER_SECRET` as already stored, updated about 24 seconds earlier, and skipped the prompt. Whoever set it then, I can't confirm what value they used.
> 3. **Retest failed.** I sent order 1 to `notify-partner` again through `pg_net`, the same way the trigger does. That order had bounced at 13:02:25 UTC. At 13:03:09 the partner still answered `401 {"accepted":false,"error":"bad or missing x-partner-secret"}`, so the stored value doesn't match.
> 4. **The second update was cancelled.** I asked again with `replace: true` so the value from `.env.local` could be entered in the dashboard, and that prompt was cancelled. I didn't try another way of setting the secret, since cancelling looked deliberate.
> 
> To fix it, update the secret in one of these two ways:
> - Let me run the update again and paste the `FULFILMENT_WEBHOOK_SECRET` value from `.env.local` into the dashboard prompt. The value never passes through me.
> - Or set it yourself: Dashboard → Edge Functions → Secrets → `PARTNER_SECRET`, or run `supabase secrets set PARTNER_SECRET=...` with the CLI.
> 
> After that I'll send order 1 again to confirm it gets a 200. That one retest also makes sure the partner receives order 1, which so far has only been rejected. No code, repo or migration changes were made.
