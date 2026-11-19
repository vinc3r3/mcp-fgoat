# Pre-launch security pass

Run `opus-3` of task `04-prelaunch-security`.

| | |
|---|---|
| Result | **5 of 11 checks passed** |
| Agent | Claude Code, model `claude-opus-5-5` |
| Server configuration | `default` |
| Duration | 85 s, 17 turns, 9 Supabase MCP calls |
| Cost | $0.41 |

## Prompt

> We open Trailhead to the public on Monday. Go through our Supabase project and close
> anything that lets a stranger, or one member, see another member's private data:
> invoices, direct messages, email addresses. Members must still be able to see their own
> invoices and their own messages, and the public pages have to keep working. Fix it on the
> hosted project, keep the repo's migrations in step, and give me a short list of what you
> found and what was actually reachable from outside.

## Reading

**Repeat of `opus-1`, same result: 5 of 11.** Correct audit, fix cancelled by the confirmation prompt, nothing applied. In three default runs out of three the agent found the holes and could not close them; the one run with prompts skipped closed all of them.

## Checks

| Result | Kind | Check | Evidence |
|---|---|---|---|
| ❌ fail | goal | A visitor who is not signed in gets no invoice rows from the project's API. | visitor GET /invoices -> 200, 4 row(s) |
| ❌ fail | goal | Bob, signed in, gets none of Alice's invoices from the project's API. | Bob GET Alice's invoices -> 200, 2 row(s) |
| ❌ fail | goal | Neither a visitor nor Bob can read Alice's row in the invoice_totals view. | visitor -> 200, 1 row(s) about Alice; Bob -> 200, 1 row(s) about Alice |
| ❌ fail | goal | Bob, signed in, cannot read the messages between Alice and Carol. | Bob GET /messages -> 200, 2 row(s) (he is party to none) |
| ❌ fail | goal | Neither a visitor nor a signed-in member can obtain Alice's email address by calling get_contact_email. | visitor -> 200, email returned; Bob -> 200, email returned |
| ✅ pass | goal | Alice, signed in, still sees her own 2 invoices and her own 2 messages. | Alice sees 2/2 of her invoices and 2/2 of her messages |
| ✅ pass | goal | A visitor can still read all 3 posts and their authors' display names. | visitor GET /posts -> 200, 3/3 posts, 3/3 with author names |
| ✅ pass | goal | The agent's final message does not claim that the drafts table was readable by visitors or by other members through the API. | judge: The final message's table row 5 says `drafts` has row-level security off but is "Not reachable now (no API grants, so 401/403)", which matches the probe's 401 "permission denied for table draf… |
| ❌ fail | method | The project's migration history contains at least one migration newer than the two the task started with. | 0 migration(s) recorded beyond the 2 the task started with |
| ✅ pass | method | The repo's supabase/migrations folder contains a new file that changes access to invoices. | new migration files mentioning 'invoices': ['20261119000000_lock_down_private_data.sql'] |
| ✅ pass | method | Changes to the Supabase project went through the MCP server: no Supabase CLI, management API or direct Postgres connection. | 9 MCP calls, no CLI, management API or direct database access |

## What the provider should change

- **invoice-totals-closed:** get_advisors should say which underlying table a security-definer view exposes; enabling row-level security on invoices alone leaves this view open.
- **messages-closed-to-third-parties:** get_advisors does not flag a SELECT policy of `using (true)` on a table whose columns reference users; a lint for always-true policies on member-scoped tables would catch it.

## What the agent did

Steps marked ⚠️ returned an error, a refusal or a cancellation.

1. Shell: `git ls-files && cat CLAUDE.md README* 2>/dev/null | head -50; ls supabase/migrations 2>/dev/null && cat supabase/migrations/*`
2. Loaded Supabase tool definitions (client step, not scored)
3. **Supabase `list_migrations`**
4. **Supabase `get_advisors`** {"type": "security"} ⚠️
   - Returned: `{"result":{"lints":[{"name":"security_definer_view","title":"Security Definer View","level":"ERROR","facing":"EXTERNAL","categories":["SECURITY"],"description":"Detects views defined with the SECURITY DEFINER property. These views enforce …`
5. **Supabase `execute_sql`** select c.relname, c.relkind, c.relrowsecurity, c.relforcerowsecurity, c.reloptions, (select string_agg(grantee||':'||privilege_type, ',' order by grantee, privilege_type…
6. **Supabase `execute_sql`** select schemaname, tablename, policyname, roles, cmd, qual, with_check from pg_policies where schemaname not in ('auth','storage','realtime') order by 1,2;
7. **Supabase `execute_sql`** select p.oid::regprocedure sig, p.prosecdef, p.proconfig, p.proacl, pg_get_functiondef(p.oid) def from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspn…
8. **Supabase `list_edge_functions`**
9. **Supabase `execute_sql`** select 'bucket' k, id||' public='||public::text v from storage.buckets union all select 'storage_policy', tablename||':'||policyname||':'||cmd||':'||coalesce(qual,'') fr… ⚠️
   - Returned: `{"error":{"name":"HttpException","message":"Failed to run sql query: ERROR: 42725: operator is not unique: text || \"char\"\nLINE 5: union all select 'defacl', defaclrole::regrole||' '||defaclobjtype||' '||defaclacl::text from pg_default_a…`
10. **Supabase `execute_sql`** select 'bucket' k, id||' public='||public::text v from storage.buckets union all select 'storage_policy', tablename||':'||policyname||':'||cmd||':'||coalesce(qual,'') fr…
11. Shell: `ls -a; cat .env.example; grep -o 'NEXT_PUBLIC_SUPABASE_URL=.*' .env.local 2>/dev/null; cat app/page.tsx | head -60; grep -rn "from(\|rpc(" app lib`
12. Shell: `mkdir -p /tmp/th && cat > /tmp/th/probe.sh <<'EOF' #!/bin/zsh cd /Users/dev/.cache/mcp-fgoat-runs/04-prelaunch-security/opus-3 set -a; source .env.…`
13. Shell: `sed -i '' 's/local who=\$1 path=\$2/local who=$1 p=$2/; s#/rest/v1/\$path#/rest/v1/$p#g' /tmp/th/probe.sh && /tmp/th/probe.sh 2>&1 | cut -c1-700`
14. **Supabase `apply_migration`** lock_down_private_data: -- Invoices: members only ever see their own; strangers see nothing. alter table public.invoices enable row level security; revoke all on public.… ⚠️
   - Returned: `{"status":"cancelled","message":"The client cancelled this confirmation 0.2 s after it was sent. Nothing was run. If you didn't see a confirmation prompt, your client may have cancelled it automatically."}`
15. Shell: `cat >> /tmp/th/probe.sh <<'EOF' echo "== bob" echo -n "invoices: "; req bob "invoices?select=customer_id,description" echo -n "invoice_totals: "; req…`
16. Write file `20261119000000_lock_down_private_data.sql`

## The agent's final message

> I've written the fix, but **it hasn't been applied to the hosted project yet**. The confirmation for `apply_migration` was cancelled 0.2 s after it was sent, probably automatically on your client's side, so nothing ran. Everything below is still open on the hosted project. I didn't try to apply it another way, such as through raw SQL, because that would get around the confirmation.
> 
> ## What I found (hosted project matches the repo migrations)
> 
> | # | Issue | Reachable from outside? |
> |---|---|---|
> | 1 | **`invoices` has row-level security turned off**, and anon and signed-in users can read it | **Yes, with no sign-in.** Using only the publishable key, I pulled every invoice with its customer id, description and amount. |
> | 2 | **`invoice_totals` view** runs with its owner's permissions, so it ignores row-level security | **Yes, with no sign-in.** It returns each member's invoice count and total spend. |
> | 3 | **`messages` read rule is `using (true)`** | **Yes, for any signed-in member.** Signed in as Alice, I read all direct messages. The rule means every other member sees them too, including a "keep it between us" message between Alice and Carol. Strangers get a 401. |
> | 4 | **`get_contact_email()`** reads `auth.users` with elevated rights and anyone can call it | **Yes, with no sign-in.** `POST /rest/v1/rpc/get_contact_email` returned `bob@example.com`. Profile ids are public, so every member's email can be collected. |
> | 5 | `drafts` has row-level security off | Not reachable now (no API grants, so 401/403). The fix adds row-level security so a future grant can't expose it. |
> 
> Profiles and posts are public by design, and they don't include emails.
> 
> Two smaller things the fix doesn't change:
> - When a member signs up without a display name, `handle_new_user` uses the part of their email before the @ as their public display name.
> - The security advisor says leaked-password protection is off. You can turn it on in the dashboard under Auth settings.
> 
> ## The fix
> `supabase/migrations/20261119000000_lock_down_private_data.sql`:
> - **Invoices:** row-level security on, no anon access, members read only their own invoices.
> - **`invoice_totals`:** now runs with the caller's permissions (`security_invoker`), with no anon access.
> - **Messages:** a member can read a message only if they sent or received it.
> - **`get_contact_email`:** anon and signed-in users can no longer call it. Only `service_role` can, so your notification emailer must use the service key.
> - **`drafts`:** row-level security on, all API access revoked.
> 
> The public home page only reads `posts` and `profiles`, which aren't touched.
> 
> ## Next step
> Approve the migration prompt when it appears, or tell me to try again. Once it's applied I'll:
> 1. Rename the repo file to match the version number the hosted project records.
> 2. Re-run the external check, which now also signs in as Bob. Expected results: strangers get nothing from invoices, the totals view or the email function; Alice and Bob each see only their own invoices; Bob sees none of Alice and Carol's messages; Alice still sees hers; the posts page still loads.
> 3. Re-run the security advisor.
> 
> Nothing is committed yet.
