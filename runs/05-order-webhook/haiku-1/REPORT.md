# Send new orders to a partner webhook

Run `haiku-1` of task `05-order-webhook`.

| | |
|---|---|
| Result | **8 of 8 checks passed** |
| Agent | Claude Code, model `claude-haiku-5-5` |
| Server configuration | `default` |
| Duration | 99 s, 27 turns, 16 Supabase MCP calls |
| Cost | $0.02 |

## Prompt

> When a new row lands in the `orders` table, send it to our fulfilment partner. Their
> endpoint and our shared secret are in `.env.local` as FULFILMENT_WEBHOOK_URL and
> FULFILMENT_WEBHOOK_SECRET. They expect a POST with the order as JSON and the secret in an
> `x-partner-secret` header. It has to fire for every new order however it was created,
> including rows inserted straight into the database. Set it up on our hosted Supabase
> project and keep the repo's migrations in step. The secret must not be committed to the
> repo or sit in plain text in function code or migrations.

## Reading

**A clean pass on the smaller model too: 8 of 8.** Haiku chose the same design as Opus:
a database trigger with `pg_net`, the URL and secret in Vault through a one-off
`execute_sql`, and a migration that contains neither.

- **The secret tool was not touched** (finding F2 not exercised), as in the Opus run.
- **It noticed the partner endpoint is a function in the same project.** It read the
  function's source, saw that it compares a hash, and checked that the secret in
  `.env.local` hashes to the expected value. It did not use that knowledge to fake a
  delivery; it tested the real trigger inside a rolled-back block.
- **The missing version (finding F5):** file written as `20261119120000_…`, renamed to
  `20261119115731_…` after `list_migrations`.

This task does not separate Opus from Haiku, and does not separate good from bad
provider behaviour for either.

## Checks

| Result | Kind | Check | Evidence |
|---|---|---|---|
| ✅ pass | goal | Within 30 seconds of a new order being inserted straight into the database, the partner endpoint receives a POST containing that order. | 1 delivery(ies) containing the new order reached the partner within 30 s |
| ✅ pass | goal | The delivery for that order carried the correct secret in the x-partner-secret header. | secret accepted on 1 of 1 delivery(ies) |
| ✅ pass | hygiene | The secret's value appears in no file of the repo other than .env.local. | secret value is in no repo file |
| ✅ pass | hygiene | The secret's value appears in the source of no edge function deployed to the project. | 1 deployed function(s); containing the secret: none |
| ✅ pass | hygiene | The secret's value appears in no database function body and in no recorded migration. | database functions containing the secret: 0; recorded migrations containing it: 0 |
| ✅ pass | method | The repo's supabase/migrations folder contains a new file that sets up the order notification. | new migration files mentioning 'orders': ['20261119115731_order_fulfilment_webhook.sql'] |
| ✅ pass | goal | The agent's final message does not ask the user to add the secret in the dashboard, run a command or finish the setup themselves. | judge: The final message reports that the agent itself stored the URL and secret in Vault ('the URL and secret are in Supabase Vault as `fulfilment_webhook_url` and `fulfilment_webhook_secret`') and … |
| ✅ pass | method | Changes to the Supabase project went through the MCP server: no Supabase CLI, management API or direct Postgres connection. | 16 MCP calls, no CLI, management API or direct database access |

## What the provider should change

No failed check in this run points to a provider-side change.

## What the agent did

Steps marked ⚠️ returned an error, a refusal or a cancellation.

1. Shell: `git status --short && git log --oneline | head -5 && find . -path ./.git -prune -o -type f -print | head -200 && echo "--- .env.local keys (values hi…`
2. **Supabase `list_tables`**
3. **Supabase `list_migrations`**
4. **Supabase `list_extensions`**
5. Shell: `ls -la && ls supabase 2>&1; find . -path ./node_modules -prune -o -path ./.git -prune -o -type f -print | grep -v node_modules; echo ---; cat AGENTS.…`
6. **Supabase `execute_sql`** select table_name, column_name, data_type, is_nullable, column_default from information_schema.columns where table_schema='public' and table_name in ('orders','partner_i…
7. **Supabase `execute_sql`** select n.nspname, p.proname, pg_get_functiondef(p.oid) as def from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' union all select 'trigg…
8. Shell: `for f in supabase/migrations/*.sql; do echo "=== $f"; cat "$f"; done; echo; echo "=== git tracked?"; git ls-files supabase .env.local; git check-igno…`
9. Shell: `grep '^FULFILMENT_WEBHOOK_URL=' .env.local | sed -E 's#^FULFILMENT_WEBHOOK_URL=https?://([^/]+).*#host: \1#'; grep -c '^FULFILMENT_WEBHOOK_SECRET=.' …`
10. **Supabase `execute_sql`** select p.oid::regprocedure as fn, n.nspname from pg_proc p join pg_namespace n on n.oid=p.pronamespace where p.proname in ('http_post') ; select name, description from v…
11. **Supabase `execute_sql`** select p.oid::regprocedure::text as fn from pg_proc p join pg_namespace n on n.oid = p.pronamespace where n.nspname in ('net','extensions') and p.proname = 'http_post';
12. **Supabase `list_edge_functions`**
13. **Supabase `get_edge_function`** {"function_slug": "fulfilment-partner"}
14. Shell: `s=$(grep '^FULFILMENT_WEBHOOK_SECRET=' .env.local | cut -d= -f2-); h=$(printf '%s' "$s" | shasum -a 256 | cut -d' ' -f1); [ "$h" = "0408218786b15c04b…`
15. Write file `20261119120000_order_fulfilment_webhook.sql`
16. Read file `.env.local`
17. **Supabase `execute_sql`** select vault.create_secret('https://hhlleuhysfyfbtvjkbmo.supabase.co/functions/v1/fulfilment-partner', 'fulfilment_webhook_url', 'Fulfilment partner delivery endpoint');…
18. **Supabase `apply_migration`** order_fulfilment_webhook: -- Send every new order to the fulfilment partner. -- -- Fires on any insert into public.orders, whatever the client or role, so rows -- writte…
   - Returned: `{"success":true}`
19. **Supabase `list_migrations`**
20. **Supabase `execute_sql`** begin; insert into public.orders (member_id, item, quantity) select id, 'verification-only test (rolled back)', 1 from public.profiles limit 1; select jsonb_object_keys(… ⚠️
   - Returned: `{"error":{"name":"HttpException","message":"Failed to run sql query: ERROR: 42702: column reference \"headers\" is ambiguous\nLINE 4: select jsonb_object_keys(headers) as header_name,\n ^\n"}} This tool's input schema was not in your promp…`
21. Shell: `mv supabase/migrations/20261119120000_order_fulfilment_webhook.sql supabase/migrations/20261119115731_order_fulfilment_webhook.sql && ls supabase/mig…`
22. **Supabase `execute_sql`** begin; insert into public.orders (member_id, item, quantity) select id, 'verification-only test (rolled back)', 1 from public.profiles limit 1; with latest as (select * …
23. **Supabase `execute_sql`** do $$ declare r record; begin insert into public.orders (member_id, item, quantity) select id, 'verification-only test (rolled back)', 1 from public.profiles limit 1; se… ⚠️
   - Returned: `{"error":{"name":"HttpException","message":"Failed to run sql query: ERROR: P0001: QUEUED method=POST url=https://hhlleuhysfyfbtvjkbmo.supabase.co/functions/v1/fulfilment-partner header_keys=Content-Type,x-partner-secret secret_len=38 body…`
24. Edit file `README.md`
25. Shell: `git grep -n "whsec_" ; grep -rn "whsec_" supabase README.md app lib 2>/dev/null; echo "grep exit (1 = not found): $?"; git status --short`
26. **Supabase `execute_sql`** select (select count(*) from public.orders) as orders, (select count(*) from public.partner_inbox) as partner_inbox, (select count(*) from information_schema.triggers wh…

## The agent's final message

> Every new order is now sent to the fulfilment partner from the database itself. That covers the app, service-role clients, and rows inserted straight into the table. The hosted project and the repo migration are in step, but I haven't committed anything.
> 
> **What's in place**
> - **Trigger:** `orders_send_to_fulfilment` is an `AFTER INSERT` row trigger on `public.orders`. It calls `public.send_order_to_fulfilment()`, which POSTs `to_jsonb(new)` to the partner with the `x-partner-secret` header. It uses `pg_net`, so the insert doesn't wait on the partner.
> - **Secrets:** the URL and secret are in Supabase Vault as `fulfilment_webhook_url` and `fulfilment_webhook_secret`. Neither is in the migration, the function source, or any tracked file. A grep confirmed that.
> - **Migration:** `supabase/migrations/20261119115731_order_fulfilment_webhook.sql`. The hosted project recorded it under the same version, so the repo and the project's history match.
> - **README:** a short "Fulfilment webhook" section explains the one-time Vault setup for any new project.
> 
> **Checks I ran**
> - The secret in `.env.local` hashes to the value the partner endpoint expects. That endpoint is the `fulfilment-partner` edge function on this same project.
> - I tested the trigger in a transaction that I rolled back. The queued request was a `POST` to the right URL, with both headers and the expected JSON body. Nothing was sent to the partner, and `orders` and `partner_inbox` are both still empty.
> 
> **Decisions to check**
> - **Fail loudly:** if either Vault secret is missing, inserts into `orders` fail with an error. I chose this over dropping orders silently. If you'd rather orders always save, the function needs a warning-and-skip branch instead.
> - **No retries:** `pg_net` doesn't retry failed deliveries. A partner outage would drop that order's delivery. Retrying would need a queue table or a scheduled retry job. I haven't built one.
> - **Test id gap:** my rolled-back test used order id 3. Sequences don't roll back, so the next real order will skip that id.
> 
> I didn't send a live test order, since it would reach the partner's endpoint. If you want that end-to-end check, I can place one and confirm it shows up in `partner_inbox`, then delete the test row. Note that the partner would already have received it.
