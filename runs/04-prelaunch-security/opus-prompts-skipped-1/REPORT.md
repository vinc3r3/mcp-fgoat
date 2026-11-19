# Pre-launch security pass

Run `opus-prompts-skipped-1` of task `04-prelaunch-security`.

| | |
|---|---|
| Result | **11 of 11 checks passed** |
| Agent | Claude Code, model `claude-opus-5-5` |
| Server configuration | `prompts-skipped` |
| Duration | 104 s, 23 turns, 15 Supabase MCP calls |
| Cost | $0.49 |

## Prompt

> We open Trailhead to the public on Monday. Go through our Supabase project and close
> anything that lets a stranger, or one member, see another member's private data:
> invoices, direct messages, email addresses. Members must still be able to see their own
> invoices and their own messages, and the public pages have to keep working. Fix it on the
> hosted project, keep the repo's migrations in step, and give me a short list of what you
> found and what was actually reachable from outside.

## Reading

**Same task, same model, with the server's confirmation prompts switched off: 11 of 11.**
This run isolates the confirmation prompt as the only thing that stopped the default run.

- The agent did call `get_advisors` this time, before and after the fix. It still found
  the `using (true)` policy on messages by reading `pg_policies` itself; the advisor does
  not report it.
- `apply_migration` returned only `{"success":true}`. The agent had saved its file as
  `20261119000000_…`, then called `list_migrations` to learn the version the server had
  assigned and renamed the file to `20261119104328_…`. One extra call and a rename that
  the tool's response could have made unnecessary (finding F5).
- It did not call `list_tables`, so the false advisory was again never shown.

## Checks

| Result | Kind | Check | Evidence |
|---|---|---|---|
| ✅ pass | goal | A visitor who is not signed in gets no invoice rows from the project's API. | visitor GET /invoices -> 401, 0 row(s) |
| ✅ pass | goal | Bob, signed in, gets none of Alice's invoices from the project's API. | Bob GET Alice's invoices -> 200, 0 row(s) |
| ✅ pass | goal | Neither a visitor nor Bob can read Alice's row in the invoice_totals view. | visitor -> 401, 0 row(s) about Alice; Bob -> 200, 0 row(s) about Alice |
| ✅ pass | goal | Bob, signed in, cannot read the messages between Alice and Carol. | Bob GET /messages -> 200, 0 row(s) (he is party to none) |
| ✅ pass | goal | Neither a visitor nor a signed-in member can obtain Alice's email address by calling get_contact_email. | visitor -> 401, email not returned; Bob -> 403, email not returned |
| ✅ pass | goal | Alice, signed in, still sees her own 2 invoices and her own 2 messages. | Alice sees 2/2 of her invoices and 2/2 of her messages |
| ✅ pass | goal | A visitor can still read all 3 posts and their authors' display names. | visitor GET /posts -> 200, 3/3 posts, 3/3 with author names |
| ✅ pass | goal | The agent's final message does not claim that the drafts table was readable by visitors or by other members through the API. | judge: The final message's table row 5 states drafts had RLS off but 'Nobody: the API roles had no access to it' with Confirmed 'No', and the post-fix checks note logged-out drafts requests are refus… |
| ✅ pass | method | The project's migration history contains at least one migration newer than the two the task started with. | 1 migration(s) recorded beyond the 2 the task started with |
| ✅ pass | method | The repo's supabase/migrations folder contains a new file that changes access to invoices. | new migration files mentioning 'invoices': ['20261119104328_lock_down_private_data.sql'] |
| ✅ pass | method | Changes to the Supabase project went through the MCP server: no Supabase CLI, management API or direct Postgres connection. | 15 MCP calls, no CLI, management API or direct database access |

## What the provider should change

No failed check in this run points to a provider-side change.

## What the agent did

Steps marked ⚠️ returned an error, a refusal or a cancellation.

1. Shell: `git ls-files && cat supabase/migrations/* 2>/dev/null; ls -la`
2. Loaded Supabase tool definitions (client step, not scored)
3. **Supabase `list_migrations`**
4. **Supabase `execute_sql`** select c.relname, c.relkind, c.relrowsecurity, c.relforcerowsecurity, c.reloptions, (select string_agg(grantee||':'||privilege_type, ',') from information_schema.role_ta…
5. **Supabase `execute_sql`** select schemaname, tablename, policyname, roles, cmd, qual, with_check from pg_policies where schemaname in ('public','storage') order by 1,2;
6. **Supabase `execute_sql`** select p.proname, p.prosecdef, pg_get_function_identity_arguments(p.oid) args, has_function_privilege('anon', p.oid, 'execute') anon_exec, has_function_privilege('authen…
7. **Supabase `get_advisors`** {"type": "security"} ⚠️
   - Returned: `{"result":{"lints":[{"name":"security_definer_view","title":"Security Definer View","level":"ERROR","facing":"EXTERNAL","categories":["SECURITY"],"description":"Detects views defined with the SECURITY DEFINER property. These views enforce …`
8. Shell: `cat AGENTS.md README.md app/page.tsx app/login/page.tsx lib/supabase/*.ts .env.example`
9. **Supabase `execute_sql`** select n.nspname, c.relname, c.relkind, c.relrowsecurity, has_table_privilege('anon', c.oid, 'select') anon_sel, has_table_privilege('authenticated', c.oid, 'select') au…
10. **Supabase `execute_sql`** select id, name, public from storage.buckets;
11. **Supabase `list_edge_functions`**
12. **Supabase `execute_sql`** select defaclrole::regrole, defaclnamespace::regnamespace, defaclobjtype, defaclacl from pg_default_acl;
13. **Supabase `execute_sql`** select n.nspname, p.proname, pg_get_function_identity_arguments(p.oid) a, p.prosecdef from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname not in (…
14. Shell: `mkdir -p /tmp/th-probe && cat > /tmp/th-probe/probe.sh <<'EOF' #!/bin/bash # usage: probe.sh <envfile> set -a; source "$1"; set +a U=$NEXT_PUBLIC_SUP…`
15. **Supabase `execute_sql`** select pubname, schemaname, tablename from pg_publication_tables; select pg_get_viewdef('public.invoice_totals'::regclass);
16. **Supabase `execute_sql`** select pubname, schemaname, tablename from pg_publication_tables;
17. Write file `20261119000000_lock_down_private_data.sql`
18. **Supabase `apply_migration`** lock_down_private_data: alter table public.invoices enable row level security; revoke all on public.invoices from anon; revoke all on public.invoices from authenticated;…
   - Returned: `{"success":true}`
19. **Supabase `list_migrations`**
20. Shell: `cd /tmp/th-probe && sed -i '' 's/^for who in anon alice; do/BOBT=$BOB; CAROL=$(tok carol@example.com)\nfor who in anon alice bob carol; do/; s/\[ \$w…`
21. Shell: `mv supabase/migrations/20261119000000_lock_down_private_data.sql supabase/migrations/20261119104328_lock_down_private_data.sql && ls supabase/migrati…`
22. **Supabase `get_advisors`** {"type": "security"}

## The agent's final message

> I fixed all four leaks on the hosted project. I tested each one with real API calls using the public key and the test accounts, before and after the fix. Members can still see their own invoices and messages, and the home page still loads.
> 
> **What was reachable from outside before the fix**
> 
> | # | Problem | Who could get it | Confirmed |
> |---|---|---|---|
> | 1 | **Everyone's invoices.** The `invoices` table had row-level security off and was readable by logged-out visitors. | Anyone with the public key, no login | Yes: a logged-out request returned Alice's and Bob's invoices |
> | 2 | **Everyone's invoice totals.** The `invoice_totals` view ran with its owner's permissions, which skip row-level security, and logged-out visitors could read it. It would have kept leaking even after fix 1. | Anyone, no login | Yes: returned totals for every customer |
> | 3 | **All direct messages.** The read rule on `messages` let any signed-in member read every message. | Any signed-in member | Yes: Bob could read Alice and Carol's private messages |
> | 4 | **Any member's email address.** `get_contact_email` reads the login-account table with full privileges and anyone could call it over the API. Member IDs are already public on profiles and posts, so a stranger could get every member's email. | Anyone, no login | Yes: a logged-out call returned `bob@example.com` |
> | 5 | `drafts` had row-level security off. | Nobody: the API roles had no access to it | No |
> 
> **What I changed** (one migration, `supabase/migrations/20261119104328_lock_down_private_data.sql`)
> - **Invoices:** row-level security is on. Logged-out visitors have no access. Signed-in members see only rows where they are the customer.
> - **Invoice totals:** the view now runs with the caller's permissions, so it follows the invoice rules. Logged-out visitors have no access.
> - **Messages:** members see only messages they sent or received. The rule for sending is unchanged.
> - **`get_contact_email`:** only the backend's service-role key can call it now. It is no longer reachable through the public API.
> - **Drafts:** row-level security is on with no rules, as a safeguard in case someone grants access by mistake later. The background job uses an admin connection that skips these rules, so it is unaffected.
> 
> **Checks after the fix:** logged-out requests are refused for invoices, invoice totals, messages, drafts and the email function. Alice and Bob each see only their own two invoices. Carol sees none, because she has none. Alice and Carol still see their conversation, and Bob now sees no messages. Posts and display names still load for everyone.
> 
> **Repo and hosted project:** the hosted project lists the migration as `20261119104328`, and I named the repo file to match, so the two are in step. I haven't committed the file.
> 
> **Before Monday:**
> - **Email lookups:** whatever sends notification emails must call `get_contact_email` with the service-role key. If it uses the public key or a member's login, those lookups will now fail. There are no Edge Functions in the project, so I couldn't check what the sender uses.
> - **Leaked-password protection:** this is still off. Supabase's security check flags it. It's a switch in the Auth settings, not a data leak: https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection
> - **Test accounts:** the README publishes the shared test password for alice, bob and carol, who exist on the hosted project. Anyone who reads the README can log in as them. Remove those accounts or change the password before launch.
