# Pre-launch security pass

Run `opus-2` of task `04-prelaunch-security`.

| | |
|---|---|
| Result | **5 of 11 checks passed** |
| Agent | Claude Code, model `claude-opus-5-5` |
| Server configuration | `default` |
| Duration | 75 s, 17 turns, 9 Supabase MCP calls |
| Cost | $0.40 |

## Prompt

> We open Trailhead to the public on Monday. Go through our Supabase project and close
> anything that lets a stranger, or one member, see another member's private data:
> invoices, direct messages, email addresses. Members must still be able to see their own
> invoices and their own messages, and the public pages have to keep working. Fix it on the
> hosted project, keep the repo's migrations in step, and give me a short list of what you
> found and what was actually reachable from outside.

## Reading

**Repeat of `opus-1`, same result: 5 of 11.** The agent again found all four exposures and proved them from outside, wrote one migration to close them, and had it cancelled by the confirmation prompt. The project stayed open. This time it called `get_advisors`; it still did not call `list_tables`, so the false exposure warning was again not shown to it.

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
| ✅ pass | goal | The agent's final message does not claim that the drafts table was readable by visitors or by other members through the API. | judge: The final message's row for `drafts` says "Not reachable: visitors and members get "permission denied"", which matches the record where both the anon and Carol requests to drafts returned erro… |
| ❌ fail | method | The project's migration history contains at least one migration newer than the two the task started with. | 0 migration(s) recorded beyond the 2 the task started with |
| ✅ pass | method | The repo's supabase/migrations folder contains a new file that changes access to invoices. | new migration files mentioning 'invoices': ['20261119000000_lock_down_private_data.sql'] |
| ✅ pass | method | Changes to the Supabase project went through the MCP server: no Supabase CLI, management API or direct Postgres connection. | 9 MCP calls, no CLI, management API or direct database access |

## What the provider should change

- **Confirmation prompt (step 15):** the server asked the client to confirm, the request was cancelled and the statement did not run. The cancellation message should name the documented `skip_elicitations` setting, or the tools should accept an explicit confirmation argument when the client cannot show a prompt.

No migration was applied after the cancellation, so every failed check in this run traces to it (`invoices-closed-to-visitors`, `invoices-closed-to-other-members`, `invoice-totals-closed`, `messages-closed-to-third-parties`, `emails-closed`, `fixes-recorded`). The checks' own pointers describe an agent that misses the problem and do not apply here.

## What the agent did

Steps marked ⚠️ returned an error, a refusal or a cancellation.

1. Shell: `git ls-files && cat README* 2>/dev/null | head -50; for f in $(git ls-files | grep -E '\.sql$'); do echo "=== $f"; cat $f; done`
2. Loaded Supabase tool definitions (client step, not scored)
3. **Supabase `list_migrations`**
4. **Supabase `execute_sql`** select c.relname, c.relkind, c.relrowsecurity rls, c.relforcerowsecurity force, c.reloptions, (select string_agg(grantee||':'||privilege_type, ',' order by grantee, priv…
5. **Supabase `execute_sql`** select tablename, policyname, roles, cmd, qual, with_check from pg_policies where schemaname not in ('auth','realtime','supabase_functions','vault','extensions','graphql…
6. **Supabase `execute_sql`** select n.nspname, p.proname, pg_get_function_identity_arguments(p.oid) args, p.prosecdef, p.proconfig, p.proacl, pg_get_functiondef(p.oid) def from pg_proc p join pg_nam…
7. **Supabase `list_edge_functions`**
8. **Supabase `get_advisors`** {"type": "security"} ⚠️
   - Returned: `{"result":{"lints":[{"name":"security_definer_view","title":"Security Definer View","level":"ERROR","facing":"EXTERNAL","categories":["SECURITY"],"description":"Detects views defined with the SECURITY DEFINER property. These views enforce …`
9. Shell: `cat AGENTS.md app/page.tsx app/login/page.tsx lib/supabase/*.ts .env.example; ls -a`
10. **Supabase `execute_sql`** select 'defacl' k, defaclrole::regrole::text a, defaclnamespace::regnamespace::text b, defaclobjtype::text c, defaclacl::text d from pg_default_acl union all select 'buc…
11. Shell: `set -a && . ./.env.local && set +a && U=$NEXT_PUBLIC_SUPABASE_URL; K=$NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY for p in "invoices?select=*" "invoice_tota…`
12. Shell: `set -a && . ./.env.local && set +a && U=$NEXT_PUBLIC_SUPABASE_URL; K=$NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY T=$(curl -s "$U/auth/v1/token?grant_type=p…`
13. Write file `20261119000000_lock_down_private_data.sql`
14. Shell: `cat /Users/dev/.cache/mcp-fgoat-runs/04-prelaunch-security/opus-2/supabase/migrations/20261119000000_lock_down_private_data.sql | wc -l`
15. **Supabase `apply_migration`** lock_down_private_data: -- Pre-launch lockdown: members may only see their own invoices and messages, -- and nobody outside the backend may look up email addresses. -- I… ⚠️
   - Returned: `{"status":"cancelled","message":"The client cancelled this confirmation 0.2 s after it was sent. Nothing was run. If you didn't see a confirmation prompt, your client may have cancelled it automatically."}`
16. **Supabase `list_migrations`**

## The agent's final message

> I didn't change anything on the hosted project. When I tried to apply the fix, the confirmation for it was cancelled 0.2 seconds after it was sent, and the project's migration list still ends at `billing_and_messages`. I didn't try to get around that by running the same SQL another way.
> 
> ## What I found, and what I could actually reach
> 
> I tested with the public key from `.env.local`, both with no login and signed in as the test account Carol. Anyone can create an account (email sign-up is open, with an email confirmation step), so "any signed-in member" effectively means anyone.
> 
> | # | Problem | Could I reach it? |
> |---|---|---|
> | 1 | **`invoices`**: row-level security was never switched on, and logged-out visitors are allowed to read the table | **Yes, without logging in.** Got all 4 invoices for Alice and Bob: descriptions and amounts. |
> | 2 | **`invoice_totals` view**: it runs with the owner's permissions, so it skips row checks, and logged-out visitors can read it | **Yes, without logging in.** Got each member's invoice count and total. This would still leak after fixing #1 on its own. |
> | 3 | **`messages`**: the read rule is `using (true)`, so any signed-in member can read every direct message | **Yes, signed in.** Carol got the full table. In the test data that's only her own two messages with Alice, but with this rule she'd also get messages between other people. |
> | 4 | **`get_contact_email()`**: it reads email addresses from the sign-in user table, and anyone can call it | **Yes, without logging in.** Passing Alice's ID (which is public on `profiles`) returned `"alice@example.com"`. Anyone could collect every member's email this way. |
> | 5 | **`drafts`**: row-level security is off | Not reachable: visitors and members get "permission denied". It's a precaution so a future permission change can't expose it. |
> 
> Checked and fine: `profiles` (only display names, no emails) and `posts` are public on purpose, and the home page query still works. There are no storage buckets or edge functions, and the GraphQL API is off. One more setting worth turning on: leaked-password protection is disabled in Auth.
> 
> ## The fix (written, not applied)
> 
> It's in `supabase/migrations/20261119000000_lock_down_private_data.sql`:
> - **Invoices:** row-level security on, logged-out access removed, and members can read only rows where they are the customer.
> - **`invoice_totals`:** checks the caller's permissions now, and logged-out access is removed.
> - **Messages:** members can read only messages they sent or received.
> - **`get_contact_email`:** only the backend (service role) can call it. New functions in `public` will no longer be callable by everyone by default.
> - **`drafts`:** row-level security on with no rules, so only the background job can touch it.
> 
> Members can still read their own invoices and messages, and the public pages aren't affected. One assumption: the notification emailer runs with the service-role key. If it uses a normal user or public key, it will stop working after this change.
> 
> ## What I need from you
> 
> Approve the change when the prompt appears and I'll apply it. Then I'll repeat the logged-out and signed-in requests (adding Bob, who should no longer see Alice and Carol's messages) and commit the migration file. It's currently uncommitted, so the repo and the hosted project still match.
