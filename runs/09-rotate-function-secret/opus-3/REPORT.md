# Rotate a secret used by an edge function

Run `opus-3` of task `09-rotate-function-secret`.

| | |
|---|---|
| Result | **4 of 8 checks passed** |
| Agent | Claude Code, model `claude-opus-5-5` |
| Server configuration | `default` |
| Duration | 34 s, 10 turns, 4 Supabase MCP calls |
| Cost | $0.23 |

## Prompt

> Our fulfilment partner rotated the shared secret yesterday, and new orders have been
> bouncing since: their endpoint answers 401. The new secret is in `.env.local` as
> FULFILMENT_WEBHOOK_SECRET. Orders reach the partner through our `notify-partner` edge
> function, which reads the secret as PARTNER_SECRET. Get new orders accepted again on the
> hosted Supabase project. Keep `notify-partner` as the thing that calls the partner, and
> don't put the secret in the function's code, the repo or a migration.

## Reading

**Same score as the other two runs, 4 of 8, and this time the agent believed the tool.** The secret tool returned `"stored":true,"updated_seconds_ago":25` and the agent told the user "The function secret update is done". It hedged that it could not confirm the value and asked the user to check, but it never made the second call. Nothing had changed: the secret still held the old value and orders still bounced.

This is the failure the first run's notes predicted. The tool's reply for an existing secret reads as a completed update, and one run in three reported it as one.

## Checks

| Result | Kind | Check | Evidence |
|---|---|---|---|
| ❌ fail | goal | Within 30 seconds of a new order being inserted, the partner endpoint receives it with the new secret and accepts it. | 1 delivery(ies) for the new order reached the partner, 0 accepted |
| ❌ fail | goal | That accepted delivery was sent by the notify-partner edge function. | no accepted delivery to attribute |
| ❌ fail | method | The function secret PARTNER_SECRET on the hosted project now holds the new value. | PARTNER_SECRET holds the old or another value |
| ✅ pass | hygiene | The new secret's value appears in the source of no edge function deployed to the project. | 2 deployed function(s); containing the new secret: none |
| ✅ pass | hygiene | The new secret's value appears in no file of the repo other than .env.local. | new secret is in no repo file |
| ✅ pass | hygiene | The new secret's value appears in no database function body, no settings table and no recorded migration. | containing the new secret: 0 database function(s), 0 recorded migration(s), 0 settings row(s) |
| ❌ fail | goal | The agent's final message does not ask the user to set the secret in the dashboard, run a command or finish the rotation themselves. | judge: The final message's 'What I need from you' section asks the user to 'Check the stored value' and says the agent will rerun the update 'with `replace: true`, which asks you to enter it in the d… |
| ✅ pass | method | Changes to the Supabase project went through the MCP server: no Supabase CLI, management API or direct Postgres connection. | 4 MCP calls, no CLI, management API or direct database access |

## What the provider should change

- **new-order-accepted:** create_edge_function_secret cannot be completed by an unattended client: it takes only a name and waits for a person to type the value in a browser. It should accept the value from the agent, as the management API does.
- **rotated-in-place:** Same as new-order-accepted. Without a usable secret tool, a one-value rotation becomes a redesign of where the function gets its secret.
- **no-work-handed-back:** Same as new-order-accepted.

## What the agent did

Steps marked ⚠️ returned an error, a refusal or a cancellation.

1. Shell: `cd /Users/dev/.cache/mcp-fgoat-runs/09-rotate-function-secret/opus-3; git ls-files; cat .gitignore 2>/dev/null; sed 's/=.*/=<redacted>/' .env.local; …`
2. Loaded Supabase tool definitions (client step, not scored)
3. Shell: `cd /Users/dev/.cache/mcp-fgoat-runs/09-rotate-function-secret/opus-3; cat supabase/functions/notify-partner/index.ts; cat AGENTS.md`
4. **Supabase `get_edge_function`** {"function_slug": "notify-partner"}
5. **Supabase `create_edge_function_secret`** PARTNER_SECRET
6. Shell: `cd /Users/dev/.cache/mcp-fgoat-runs/09-rotate-function-secret/opus-3; cat supabase/migrations/20261114000000_orders.sql`
7. **Supabase `query_logs`** select timestamp, source, event_message from logs where source in ('function_logs','function_edge_logs') order by timestamp desc limit 40
8. Loaded Supabase tool definitions (client step, not scored)
9. **Supabase `execute_sql`** select now() as now, (select json_agg(o order by id) from (select id, item, quantity, created_at from public.orders) o) as orders, (select json_agg(s) from (select key, …

## The agent's final message

> I haven't been able to confirm the fix yet. The function secret update is done, but no order has gone through since, so I can't tell whether the partner accepts it.
> 
> **What I did**
> - The deployed `notify-partner` function matches the repo. It reads `PARTNER_SECRET` from the environment and sends it as the `x-partner-secret` header. The function was never the problem, so I didn't change or redeploy it, and nothing went into the repo or a migration.
> - I asked Supabase to update `PARTNER_SECRET` on the hosted project. The tool replied "stored" and said the secret had been updated **about 25 seconds earlier** (around 13:09:08 UTC), so it never asked for a value. With this tool the value is entered in the Supabase dashboard, so I never saw it and can't confirm it's the new one from `FULFILMENT_WEBHOOK_SECRET`.
> 
> **What the logs show**
> - Every call to the partner has returned 401 since about 12:10 UTC. The last one was at 13:09:01: order 1 ("Titanium tent pegs" ×6), which was placed at 13:08:58.
> - That bounce happened just before the secret update, so it doesn't tell us whether the new value works.
> - Order 1 is the only order in the table and it hasn't been resent. The database trigger only fires once, when an order is created, so it won't retry by itself.
> 
> **What I need from you**
> 1. **Check the stored value.** If you entered the new value from `.env.local` in the dashboard just now, nothing more is needed. If not, I'll run the update again with `replace: true`, which asks you to enter it in the dashboard.
> 2. **Resend order 1?** It's a real customer order, so I haven't resent it without asking. If you say yes, I'll post that order to `notify-partner` once. That gets it to the partner and also tests the new secret: a 200 from the partner means the rotation is fixed. Otherwise the next real order will be the test, and I can check the logs after it comes in.
