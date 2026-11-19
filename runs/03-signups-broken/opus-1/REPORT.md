# Find and fix broken sign-ups

Run `opus-1` of task `03-signups-broken`.

| | |
|---|---|
| Result | **9 of 9 checks passed** |
| Agent | Claude Code, model `claude-opus-5-5` |
| Server configuration | `default` |
| Duration | 64 s, 16 turns, 8 Supabase MCP calls |
| Cost | $0.35 |

## Prompt

> Since yesterday's release nobody new can sign up to Trailhead: creating an account fails
> with a 500 from Supabase Auth. Existing members can still sign in. Find the cause and fix
> it on the hosted project, keep the repo's migrations in step with the fix, and tell me
> what the cause was.

## Reading

**A clean pass: 9 of 9, in 64 seconds.** The log tool did its job. The agent's first
action on the project was one log query filtered to auth and Postgres errors, and the
answer was in the first result: `null value in column "handle" of relation "profiles"
violates not-null constraint`. It then read the trigger function, fixed it in a
migration, and tested the fix by inserting two users inside a transaction it rolled back.

- **The log tool's rough edges (finding F10) did not bite.** The agent named its columns
  and sources correctly on the first try, so it never met the rejected `select *` or the
  error that arrives looking like data. The tool description lists the common sources,
  which was enough.
- **The missing version (finding F5) again cost a call and a rename:** file written as
  `20261119120000_…`, renamed to `20261119114527_…` after `list_migrations`.
- **The run was not contaminated.** The project's logs still held the reference solution
  from testing the checks earlier in the day. The agent's one log query filtered for
  errors and did not return it, and its fix is designed differently (a `-2` suffix where
  the reference appends a number to the email name).

For this model the task does not separate good from bad provider behaviour.

## Checks

| Result | Kind | Check | Evidence |
|---|---|---|---|
| ✅ pass | goal | Creating a new account through Supabase Auth succeeds. | creating dana.check@example.com -> 200  |
| ✅ pass | goal | The newly created account automatically gets a profiles row with a non-empty handle. | profile row: present, handle: 'dana' |
| ✅ pass | goal | Alice, Bob and Carol still have their profiles with their original handles. | found {'Alice': 'alice', 'Bob': 'bob', 'Carol': 'carol'} |
| ✅ pass | goal | The handle column on profiles is still required and still unique: the fix did not remove yesterday's release. | handle column is required and unique |
| ✅ pass | goal | The agent's final message tells the user that sign-up failed because the trigger that creates a profile did not set the new required handle column. | judge: The final message states the sign-up trigger `public.handle_new_user()` "was never updated: it still only inserts `id` and `display_name`. So every new account tried to create a profile with n… |
| ✅ pass | method | The agent queried the project's logs before it made its first change to the database. | first log query was MCP call #2; first write was #6 |
| ✅ pass | method | The project's migration history contains a new migration that changes the sign-up trigger function. | 1 migration(s) after the baseline change handle_new_user |
| ✅ pass | method | The repo's supabase/migrations folder contains a new file that changes the sign-up trigger function. | new migration files mentioning 'handle_new_user': ['20261119114527_handle_new_user_sets_handle.sql'] |
| ✅ pass | method | Changes to the Supabase project went through the MCP server: no Supabase CLI, management API or direct Postgres connection. | 8 MCP calls, no CLI, management API or direct database access |

## What the provider should change

No failed check in this run points to a provider-side change.

## What the agent did

Steps marked ⚠️ returned an error, a refusal or a cancellation.

1. Shell: `git log --stat | head -30 && find . -path ./.git -prune -o -type f -print | head -50`
2. Loaded Supabase tool definitions (client step, not scored)
3. Shell: `cat AGENTS.md supabase/migrations/*.sql`
4. **Supabase `list_migrations`**
5. **Supabase `query_logs`** select timestamp, source, event_message from logs where source in ('auth_logs','postgres_logs') and (event_message ilike '%error%' or event_message ilike '%500%') order …
6. **Supabase `execute_sql`** select pg_get_functiondef('public.handle_new_user'::regproc) as fn;
7. **Supabase `execute_sql`** select id, display_name, handle from public.profiles order by created_at;
8. **Supabase `execute_sql`** select column_name, is_nullable, column_default from information_schema.columns where table_schema='public' and table_name='profiles';
9. Shell: `grep -rn "handle\|signUp\|display_name" app lib README.md`
10. Shell: `cat > supabase/migrations/20261119120000_handle_new_user_sets_handle.sql <<'EOF' -- Fix signups (broken since 20261118000000_add_profile_handles): --…`
11. Shell: `cat supabase/migrations/20261119120000_handle_new_user_sets_handle.sql | wc -c`
12. **Supabase `apply_migration`** handle_new_user_sets_handle: -- Fix signups (broken since 20261118000000_add_profile_handles): -- profiles.handle became NOT NULL + unique, but handle_new_user() still o…
   - Returned: `{"success":true}`
13. **Supabase `execute_sql`** do $$ declare r record; begin insert into auth.users (id, instance_id, aud, role, email, raw_user_meta_data, created_at, updated_at) values (gen_random_uuid(), '00000000… ⚠️
   - Returned: `{"error":{"name":"HttpException","message":"Failed to run sql query: ERROR: P0001: ROLLBACK_OK: newbie=newbie, Alice=alice-2\nCONTEXT: PL/pgSQL function inline_code_block line 10 at RAISE\n"}}`
14. **Supabase `list_migrations`**
15. Shell: `git mv -f supabase/migrations/20261119120000_handle_new_user_sets_handle.sql supabase/migrations/20261119114527_handle_new_user_sets_handle.sql 2>/de…`

## The agent's final message

> Sign-ups work again on the hosted project, and the repo has a matching migration.
> 
> ## Cause
> Yesterday's migration `20261118000000_add_profile_handles.sql` added `profiles.handle`, filled it in for existing members, then made it `NOT NULL` and unique. The sign-up trigger `public.handle_new_user()` (from `init.sql`) was never updated: it still only inserts `id` and `display_name`. So every new account tried to create a profile with no handle, Postgres rejected it, and Supabase Auth returned a 500. The auth logs show exactly this on every failed `POST /admin/users`:
> 
> > `null value in column "handle" of relation "profiles" violates not-null constraint (SQLSTATE 23502)`
> 
> Existing members weren't affected because signing in never creates a profile row.
> 
> ## Fix
> I replaced `handle_new_user()` on the hosted database using a migration, so it now sets a handle:
> - It uses a `handle` passed in at sign-up if there is one. Otherwise it uses `lower(display_name)`, the same rule that filled in handles for existing members.
> - If that handle is already taken, it adds `-2`, `-3` and so on. Without this, a second "Alice" would still get a 500, just from the unique index instead.
> - Small extra change: a blank `display_name` at sign-up now falls back to the start of the email address, as a missing one already did.
> 
> **Check:** inside a transaction that was rolled back (no test rows were kept), I inserted two users into `auth.users`. They got the profiles `newbie → newbie` and `Alice → alice-2` (because `alice` exists). Existing profiles are unchanged.
> 
> ## Repo
> I added `supabase/migrations/20261119114527_handle_new_user_sets_handle.sql`. The filename uses the version the hosted project recorded, so `list_migrations` and the repo match. It isn't committed yet; tell me if you want me to commit it.
> 
> The app doesn't collect or show handles yet, so new members' handles come from their display name or email. If you add a handle field to sign-up, pass it as `options.data.handle` and the trigger will use it.
