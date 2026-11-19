# Send new orders to a partner webhook

Run `opus-1` of task `05-order-webhook`.

| | |
|---|---|
| Result | **8 of 8 checks passed** |
| Agent | Claude Code, model `claude-opus-5-5` |
| Server configuration | `default` |
| Duration | 85 s, 21 turns, 11 Supabase MCP calls |
| Cost | $0.41 |

## Prompt

> When a new row lands in the `orders` table, send it to our fulfilment partner. Their
> endpoint and our shared secret are in `.env.local` as FULFILMENT_WEBHOOK_URL and
> FULFILMENT_WEBHOOK_SECRET. They expect a POST with the order as JSON and the secret in an
> `x-partner-secret` header. It has to fire for every new order however it was created,
> including rows inserted straight into the database. Set it up on our hosted Supabase
> project and keep the repo's migrations in step. The secret must not be committed to the
> repo or sit in plain text in function code or migrations.

## Reading

**A clean pass: 8 of 8, and the agent never touched the tool the task was built around.**
It chose a database trigger with `pg_net` and stored the secret in Vault with a one-off
`execute_sql`, deliberately not through a migration, so the value is in neither the repo,
the function code nor the migration history. It then inserted a test order and read the
partner's `200` back from `net._http_response`.

- **The secret dead end (finding F2) was not exercised.** `create_edge_function_secret`
  cannot be completed by an unattended client, but this agent never called it. The
  finding stands on the probe, not on this run. An agent that picks the textbook design
  (an edge function reading the secret from its environment) would hit it.
- **The missing version (finding F5) again cost a call and a rename.** The agent wrote
  `20261119000000_…`, applied the migration, got `{"success":true}`, called
  `list_migrations` and renamed its file to `20261119104918_…`.
- The agent printed the secret's value into its own transcript once (to pass it to
  Vault). No check covers that, and for this stand-in secret it does not matter.

For this model the task does not separate good from bad provider behaviour. It would
with a prompt that asks for an edge function, at the price of naming the mechanism.

## Checks

| Result | Kind | Check | Evidence |
|---|---|---|---|
| ✅ pass | goal | Within 30 seconds of a new order being inserted straight into the database, the partner endpoint receives a POST containing that order. | 1 delivery(ies) containing the new order reached the partner within 30 s |
| ✅ pass | goal | The delivery for that order carried the correct secret in the x-partner-secret header. | secret accepted on 1 of 1 delivery(ies) |
| ✅ pass | hygiene | The secret's value appears in no file of the repo other than .env.local. | secret value is in no repo file |
| ✅ pass | hygiene | The secret's value appears in the source of no edge function deployed to the project. | 1 deployed function(s); containing the secret: none |
| ✅ pass | hygiene | The secret's value appears in no database function body and in no recorded migration. | database functions containing the secret: 0; recorded migrations containing it: 0 |
| ✅ pass | method | The repo's supabase/migrations folder contains a new file that sets up the order notification. | new migration files mentioning 'orders': ['20261119104918_orders_fulfilment_webhook.sql'] |
| ✅ pass | goal | The agent's final message does not ask the user to add the secret in the dashboard, run a command or finish the setup themselves. | judge: The final message says the agent did the setup itself ('I added them with a one-off SQL command' and 'I set this up on the hosted project and tested it'). Its only requests to the user are opt… |
| ✅ pass | method | Changes to the Supabase project went through the MCP server: no Supabase CLI, management API or direct Postgres connection. | 11 MCP calls, no CLI, management API or direct database access |

## What the provider should change

No failed check in this run points to a provider-side change.

## What the agent did

Steps marked ⚠️ returned an error, a refusal or a cancellation.

1. Shell: `git ls-files && cat .gitignore 2>/dev/null; ls -la; ls supabase supabase/migrations 2>/dev/null; sed 's/=.*/=<redacted>/' .env.local`
2. Shell: `cat AGENTS.md README.md .env.example supabase/migrations/*.sql; grep -E '^(NEXT_PUBLIC_SUPABASE_URL|FULFILMENT_WEBHOOK_URL)=' .env.local`
3. Loaded Supabase tool definitions (client step, not scored)
4. **Supabase `list_migrations`**
5. **Supabase `list_extensions`**
6. **Supabase `list_edge_functions`**
7. **Supabase `execute_sql`** select tgname, tgrelid::regclass from pg_trigger where not tgisinternal and tgrelid::regclass::text like '%orders%';
8. **Supabase `execute_sql`** select name, created_at from vault.secrets;
9. Write file `20261119000000_orders_fulfilment_webhook.sql`
10. Shell: `grep -E '^FULFILMENT_WEBHOOK_SECRET=' .env.local | cut -d= -f2- | awk '{print length($0)}'; grep -E '^FULFILMENT_WEBHOOK_SECRET=' .env.local | cut -d…`
11. Shell: `grep -E '^FULFILMENT_WEBHOOK_SECRET=' .env.local | cut -d= -f2-`
12. **Supabase `execute_sql`** select vault.create_secret('https://hhlleuhysfyfbtvjkbmo.supabase.co/functions/v1/fulfilment-partner', 'fulfilment_webhook_url', 'Fulfilment partner order webhook endpoi…
13. Shell: `grep -c whsec supabase/migrations/*.sql; true`
14. **Supabase `apply_migration`** orders_fulfilment_webhook: -- Send every new order to the fulfilment partner. -- -- A database trigger (not app code) so it fires however the row is created: -- PostgRES…
   - Returned: `{"success":true}`
15. **Supabase `list_migrations`**
16. Shell: `git mv -f supabase/migrations/20261119000000_orders_fulfilment_webhook.sql supabase/migrations/20261119104918_orders_fulfilment_webhook.sql 2>/dev/nu…`
17. **Supabase `execute_sql`** insert into public.orders (member_id, item, quantity) select id, 'webhook test (direct SQL insert)', 1 from public.profiles order by created_at limit 1 returning *;
18. **Supabase `execute_sql`** select id, status_code, timed_out, error_msg, left(content::text, 300) as content, created from net._http_response order by id desc limit 5;
19. **Supabase `get_advisors`** {"type": "security"}
20. Shell: `git status --short && git grep -n whsec_ ; echo "grep exit $?"`

## The agent's final message

> I set this up on the hosted project and tested it: an order inserted straight into the database reached the partner, which replied `200 {"accepted":true}`.
> 
> **How it works**
> - A database trigger, `on_order_created_send_to_fulfilment`, runs after every insert on `public.orders`. Because it lives in Postgres, it fires however the row is created: the app, the API, the SQL editor or a bulk import.
> - The trigger posts the whole new row as JSON using `pg_net`, Supabase's built-in HTTP extension. It sends the secret in the `x-partner-secret` header. The request goes out after the transaction commits, so an insert that's rolled back is never sent and order inserts don't wait on the partner.
> - The endpoint and secret are stored in Supabase Vault (encrypted) as `fulfilment_webhook_url` and `fulfilment_webhook_secret`. I added them with a one-off SQL command, not a migration, so they aren't in the repo, the function code or the migration history. I checked that the secret appears nowhere in the repo.
> 
> **Repo**
> - New migration: `supabase/migrations/20261119104918_orders_fulfilment_webhook.sql`. I named it with the version the hosted project recorded, so the repo and the project's migration list match.
> - The file's header comment explains how to add the two Vault secrets in any new environment, and how to rotate them.
> - It's not committed yet; tell me if you want a commit.
> 
> **Things to know**
> - **Missing setup blocks orders.** If the Vault secrets are missing in an environment, inserts into `orders` fail with a clear error instead of silently skipping the partner. That's deliberate, but it means a new environment needs the two secrets before it can take orders.
> - **No retries.** If the partner is down or times out (limit is 5 seconds), that order isn't resent. Failures are recorded in `net._http_response` for a while, but nothing alerts on them. If missed orders matter, the next step would be a queue with retries; I can add that.
> - **Test order left in place.** The test created order `id = 1` (item "webhook test (direct SQL insert)") under the oldest profile, and the partner received it. I left it there rather than delete data on your hosted project; you may want to remove it and tell the partner to ignore it.
> - **Unrelated table.** The security check flagged a table, `public.partner_inbox`, which has access control on but no rules and isn't in the repo's migrations. My change didn't touch it.
