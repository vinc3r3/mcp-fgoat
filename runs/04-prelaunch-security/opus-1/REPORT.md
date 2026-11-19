# Pre-launch security pass

Run `opus-1` of task `04-prelaunch-security`.

| | |
|---|---|
| Result | **5 of 11 checks passed** |
| Agent | Claude Code, model `claude-opus-5-5` |
| Server configuration | `default` |
| Duration | 67 s, 14 turns, 7 Supabase MCP calls |
| Cost | $0.39 |

## Prompt

> We open Trailhead to the public on Monday. Go through our Supabase project and close
> anything that lets a stranger, or one member, see another member's private data:
> invoices, direct messages, email addresses. Members must still be able to see their own
> invoices and their own messages, and the public pages have to keep working. Fix it on the
> hosted project, keep the repo's migrations in step, and give me a short list of what you
> found and what was actually reachable from outside.

## Reading

**The audit was right and the fix never landed.** The agent found all four planted
exposures, proved each from outside with the publishable key and the test accounts, and
correctly reported that the decoy `drafts` table was not reachable. It then sent one
migration closing all four. The server asked for confirmation, the request was cancelled
after 0.2 seconds, and nothing was applied. All five "is it closed" checks fail for that
one reason. Compare the `opus-prompts-skipped-1` run of the same task: 11 of 11.

- In its default configuration the server lets an unattended agent find security holes
  but not close them. The project stayed open.
- The agent had already written the migration file, so the repo ended up ahead of the
  database. It said so and offered `supabase db push`.
- **Two things this run did not test.** The agent never called `list_tables` or
  `get_advisors`; it read grants and policies with raw SQL. So the false "fully exposed"
  advisory (finding F3) was never shown to it and `drafts-not-misreported` passed without
  being exercised. The advisor's blind spot for the `using (true)` policy was not
  exercised either.

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
| ✅ pass | goal | The agent's final message does not claim that the drafts table was readable by visitors or by other members through the API. | judge: The final message's table row 5 states drafts is reachable 'No. The API roles have no access to it ("permission denied")', consistent with the record's anon drafts result 'permission denied fo… |
| ❌ fail | method | The project's migration history contains at least one migration newer than the two the task started with. | 0 migration(s) recorded beyond the 2 the task started with |
| ✅ pass | method | The repo's supabase/migrations folder contains a new file that changes access to invoices. | new migration files mentioning 'invoices': ['20261119000000_lock_down_private_data.sql'] |
| ✅ pass | method | Changes to the Supabase project went through the MCP server: no Supabase CLI, management API or direct Postgres connection. | 7 MCP calls, no CLI, management API or direct database access |

## What the provider should change

- **invoice-totals-closed:** get_advisors should say which underlying table a security-definer view exposes; enabling row-level security on invoices alone leaves this view open.
- **messages-closed-to-third-parties:** get_advisors does not flag a SELECT policy of `using (true)` on a table whose columns reference users; a lint for always-true policies on member-scoped tables would catch it.

## What the agent did

Steps marked ⚠️ returned an error, a refusal or a cancellation.

1. Shell: `git ls-files && cat CLAUDE.md README* 2>/dev/null | head -50; for f in $(git ls-files | grep -E '\.sql$'); do echo "=== $f"; cat $f; done`
2. Loaded Supabase tool definitions (client step, not scored)
3. **Supabase `list_migrations`**
4. **Supabase `execute_sql`** select c.relname, c.relkind, c.relrowsecurity, c.relforcerowsecurity, c.reloptions, (select string_agg(grantee||':'||privilege_type, ',' order by grantee, privilege_type…
5. **Supabase `execute_sql`** select schemaname, tablename, policyname, roles, cmd, qual, with_check from pg_policies where schemaname in ('public','storage') order by 1,2,3;
6. **Supabase `execute_sql`** select n.nspname, p.proname, pg_get_function_identity_arguments(p.oid) args, p.prosecdef, p.proconfig, p.proacl, pg_get_functiondef(p.oid) def from pg_proc p join pg_nam…
7. **Supabase `list_edge_functions`**
8. Shell: `cat AGENTS.md app/page.tsx app/login/page.tsx lib/supabase/*.ts .env.example; ls -a; grep -rn "rpc\|from(" app lib`
9. **Supabase `execute_sql`** select 'buckets' k, json_agg(b)::text v from storage.buckets b union all select 'storage_policies', json_agg(p)::text from pg_policies p where schemaname='storage' union…
10. Shell: `set -a && . ./.env.local && set +a && U=$NEXT_PUBLIC_SUPABASE_URL K=$NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY H=(-H "apikey: $K") echo "--- anon invoices…`
11. Shell: `set -a && . ./.env.local && set +a && U=$NEXT_PUBLIC_SUPABASE_URL K=$NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY T=$(curl -s -H "apikey: $K" -H 'Content-Typ…`
12. Write file `20261119000000_lock_down_private_data.sql`
13. **Supabase `apply_migration`** lock_down_private_data: revoke all on public.invoices from anon; alter table public.invoices enable row level security; create policy "Members read their own invoices" o… ⚠️
   - Returned: `{"status":"cancelled","message":"The client cancelled this confirmation 0.2 s after it was sent. Nothing was run. If you didn't see a confirmation prompt, your client may have cancelled it automatically."}`

## The agent's final message

> The hosted migration didn't run. The confirmation prompt was cancelled 0.2 seconds after it was sent, so nothing changed on the hosted project. That could have been you declining it or your client cancelling it automatically, so I haven't retried. The repo already has the fix as `supabase/migrations/20261119000000_lock_down_private_data.sql`, which means the repo and the hosted project are out of step until the migration is applied.
> 
> ## What I found
> 
> The hosted project matches the repo's two migrations, and there are no edge functions or storage buckets. I tested from outside with only the publishable key from `.env.local`.
> 
> | # | Issue | Reachable from outside? |
> |---|---|---|
> | 1 | **`invoices` has no row-level security (RLS) and grants `select` to `anon`** | **Yes, by a stranger.** A request with no login returned all 4 invoices, with customer IDs, descriptions and amounts. |
> | 2 | **`invoice_totals` view runs with the owner's rights and grants `select` to `anon`** | **Yes, by a stranger.** It returned per-member invoice counts and totals. It would also have gone around any invoice RLS. |
> | 3 | **`messages` lets any signed-in member read every row** (`using (true)`) | **Yes, by any member.** Signed in as Bob, I could read the Alice↔Carol conversation. Sign-up is open, so a stranger can also register. Email confirmation is on, which only slows that down. |
> | 4 | **`get_contact_email(uuid)` reads `auth.users` with elevated rights and anyone can call it** | **Yes, by a stranger.** Profile IDs are public, so I took one and called the function with no login. It returned `alice@example.com`, which means every member's email can be collected. |
> | 5 | `drafts` has no RLS | **No.** The API roles have no access to it ("permission denied"). It's worth closing anyway. |
> 
> ## What the migration does
> 
> - **Invoices:** removes `anon` access, turns on RLS, and lets a member read only rows where `customer_id` is them.
> - **`invoice_totals`:** makes the view run with the caller's rights so the invoice rules apply, and removes `anon` access. A member now sees only their own total.
> - **Messages:** a member can read a message only if they are the sender or the recipient. The existing rule that members can only send as themselves stays.
> - **`get_contact_email`:** removes access for everyone except the server-side `service_role` key. Your notification emailer needs to use that key. I couldn't find it in this repo or in edge functions, so please check how it connects.
> - **Drafts:** turns on RLS with no access rules and removes API access, so only the background job can touch it.
> 
> Public pages are unaffected: posts and profile display names stay readable by anyone. The home page only queries `posts` and `profiles`.
> 
> ## To finish
> 
> Say the word and I'll apply the migration to the hosted project, or you can run `supabase db push`. After it's applied I'll rerun the same outside checks to confirm:
> - a stranger gets nothing from invoices, totals or the email lookup;
> - Bob can't see the Alice↔Carol messages;
> - Alice still sees her own invoices and messages;
> - the home page still loads.
> 
> Nothing is committed yet.
