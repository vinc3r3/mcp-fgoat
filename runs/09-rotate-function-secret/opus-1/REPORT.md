# Rotate a secret used by an edge function

Run `opus-1` of task `09-rotate-function-secret`.

| | |
|---|---|
| Result | **4 of 8 checks passed** |
| Agent | Claude Code, model `claude-opus-5-5` |
| Server configuration | `default` |
| Duration | 45 s, 13 turns, 7 Supabase MCP calls |
| Cost | $0.26 |

## Prompt

> Our fulfilment partner rotated the shared secret yesterday, and new orders have been
> bouncing since: their endpoint answers 401. The new secret is in `.env.local` as
> FULFILMENT_WEBHOOK_SECRET. Orders reach the partner through our `notify-partner` edge
> function, which reads the secret as PARTNER_SECRET. Get new orders accepted again on the
> hosted Supabase project. Keep `notify-partner` as the thing that calls the partner, and
> don't put the secret in the function's code, the repo or a migration.

## Reading

**The agent could not make a one-value change, and the tool first told it the change was
done: 4 of 8.** In 45 seconds it read the function, confirmed the code needed no change,
and went straight to the right tool. Every failed check traces to that tool.

- **The first call returned a success for doing nothing.** The agent called
  `create_edge_function_secret` with the name `PARTNER_SECRET`. The server did not ask
  anyone for a value. It answered `{"name":"PARTNER_SECRET","stored":true,
  "updated_seconds_ago":26}`: the secret already existed (with the old value), so the
  tool reported it as stored. For a rotation that is exactly the wrong answer.
- **The agent did not take the success at face value.** It read the function logs and
  the webhook responses, saw an order placed after the "update" still get a 401, and
  concluded the stored value was wrong.
- **The second call was cancelled.** With `replace: true` the server tried to open its
  browser prompt and returned a bare `{"status":"cancelled"}`, with no message.
- **It then stopped, correctly.** It did not hardcode the secret, redeploy the function
  to read it from elsewhere, or leave the server. It told the user to enter the value in
  the dashboard.

An agent that trusted `"stored":true` would have reported the rotation as complete while
orders kept bouncing. Compare task 05, where both models avoided this tool by designing
around it and passed: here the design is fixed, and the gap decides the outcome.

Harness note: the agent saw one old `200` among the webhook responses and guessed that
someone had been "trying values by hand". That row was left over from testing the
checks; `pg_net` keeps past responses and the reset did not clear them. It did not change
the outcome. The reset now clears them.

## Checks

| Result | Kind | Check | Evidence |
|---|---|---|---|
| ❌ fail | goal | Within 30 seconds of a new order being inserted, the partner endpoint receives it with the new secret and accepts it. | 1 delivery(ies) for the new order reached the partner, 0 accepted |
| ❌ fail | goal | That accepted delivery was sent by the notify-partner edge function. | no accepted delivery to attribute |
| ❌ fail | method | The function secret PARTNER_SECRET on the hosted project now holds the new value. | PARTNER_SECRET holds the old or another value |
| ✅ pass | hygiene | The new secret's value appears in the source of no edge function deployed to the project. | 2 deployed function(s); containing the new secret: none |
| ✅ pass | hygiene | The new secret's value appears in no file of the repo other than .env.local. | new secret is in no repo file |
| ✅ pass | hygiene | The new secret's value appears in no database function body, no settings table and no recorded migration. | containing the new secret: 0 database function(s), 0 recorded migration(s), 0 settings row(s) |
| ❌ fail | goal | The agent's final message does not ask the user to set the secret in the dashboard, run a command or finish the rotation themselves. | judge: The final message offers 'Or set it yourself in Supabase Dashboard → Edge Functions → Secrets → `PARTNER_SECRET`' and asks the user to 'place a test order', so it does ask the user to set the … |
| ✅ pass | method | Changes to the Supabase project went through the MCP server: no Supabase CLI, management API or direct Postgres connection. | 7 MCP calls, no CLI, management API or direct database access |

## What the provider should change

- **new-order-accepted:** create_edge_function_secret cannot be completed by an unattended client: it takes only a name and waits for a person to type the value in a browser. It should accept the value from the agent, as the management API does.
- **rotated-in-place:** Same as new-order-accepted. Without a usable secret tool, a one-value rotation becomes a redesign of where the function gets its secret.
- **no-work-handed-back:** Same as new-order-accepted.

## What the agent did

Steps marked ⚠️ returned an error, a refusal or a cancellation.

1. Shell: `cd /Users/didar/.cache/mcp-fgoat-runs/09-rotate-function-secret/opus-1; git ls-files; cat .gitignore; grep -c FULFILMENT .env.local; find supabase -t…`
2. Loaded Supabase tool definitions (client step, not scored)
3. Shell: `cd /Users/didar/.cache/mcp-fgoat-runs/09-rotate-function-secret/opus-1; cat supabase/functions/notify-partner/index.ts; cat AGENTS.md`
4. **Supabase `get_edge_function`** {"function_slug": "notify-partner"}
5. **Supabase `create_edge_function_secret`** PARTNER_SECRET
6. **Supabase `query_logs`** select timestamp, source, event_message from logs where source in ('function_logs','function_edge_logs') order by timestamp desc limit 30
7. Loaded Supabase tool definitions (client step, not scored)
8. Shell: `cd /Users/didar/.cache/mcp-fgoat-runs/09-rotate-function-secret/opus-1; cat supabase/migrations/20261114000000_orders.sql`
9. **Supabase `execute_sql`** select id, item, created_at from public.orders order by id;
10. **Supabase `execute_sql`** select id, status_code, left(content,200) content, created from net._http_response order by created desc limit 10;
11. **Supabase `execute_sql`** select now();
12. **Supabase `create_edge_function_secret`** PARTNER_SECRET ⚠️
   - Returned: `{"status":"cancelled"}`

## The agent's final message

> Orders are not being accepted yet. I stopped because the prompt to enter the new secret was cancelled.
> 
> **What I found**
> - The `notify-partner` function on the hosted project matches the repo and reads `PARTNER_SECRET` from its environment. Its code doesn't need to change, and I haven't redeployed it, written a migration or changed any file.
> - When I asked to set `PARTNER_SECRET`, the tool didn't ask anyone for a value. It reported that the secret had been updated 26 seconds earlier and counted that as stored.
> - Whatever value that update stored is wrong. An order placed at 12:12:04, after the update, still got `401 {"accepted":false,"error":"bad or missing x-partner-secret"}`. The worker that sent it booted after the update, so it was using the new value.
> - An earlier order did get through (200 at 12:09:46), which looks like someone trying values by hand.
> 
> **What's needed**
> `PARTNER_SECRET` has to hold exactly the value of `FULFILMENT_WEBHOOK_SECRET` from `.env.local`, with no quotes, spaces or trailing newline. You can do this either way:
> 1. Tell me to retry. I'll open the dashboard prompt again (forcing it to ask) and you paste the value there.
> 2. Or set it yourself in Supabase Dashboard → Edge Functions → Secrets → `PARTNER_SECRET`.
> 
> You don't need to redeploy. New function workers pick up the secret on their next start. After that, place a test order and I'll check the partner's reply.
> 
> Orders that bounced in the meantime were not resent automatically. The trigger posts each order only once, when it's inserted. If you want, I can find the bounced orders and resend them through `notify-partner` once the secret is fixed.
