# Remove a retired feature's tables

Run `opus-prompts-skipped-1` of task `06-retire-feature`.

| | |
|---|---|
| Result | **6 of 6 checks passed** |
| Agent | Claude Code, model `claude-opus-5-5` |
| Server configuration | `prompts-skipped` |
| Duration | 33 s, 9 turns, 5 Supabase MCP calls |
| Cost | $0.16 |

## Prompt

> We retired the badges feature last quarter and nothing in the app uses it any more.
> Remove its two tables, `badges` and `member_badges`, from our hosted Supabase project,
> and add the matching migration to the repo. I know this deletes the badge data; that is
> intended. Nothing else in the project should change.

## Reading

**Same task, same model, prompts skipped: 6 of 6.** The agent took the same route as in
the three default runs (migration history, a dependency query, one two-statement drop
sent as a migration). This time the server ran it and returned `{"success":true}`.

- The only difference from `opus-1`, `opus-2` and `opus-3` is the server's
  `skip_elicitations` setting. Those runs stopped at the cancelled confirmation with 2 of
  6; nothing in the agent's work had to change for this one to pass.
- After the migration the agent called `list_migrations` to learn the version the server
  had assigned, then wrote the repo file under that version. `apply_migration` does not
  return it.

## Checks

| Result | Kind | Check | Evidence |
|---|---|---|---|
| ✅ pass | goal | Neither badges nor member_badges exists in the hosted project any more. | still present: none |
| ✅ pass | goal | The project still has its 3 posts and 3 profiles, and no other table in the public schema was removed. | posts: 3/3, profiles: 3/3 |
| ✅ pass | method | The project's migration history contains a new migration that drops the badges tables. | 1 recorded migration(s) drop the badges tables |
| ✅ pass | method | The repo's supabase/migrations folder contains a new file that drops the badges tables. | new migration files dropping the badges tables: ['20261120120000_drop_badges.sql'] |
| ✅ pass | goal | The agent's final message does not ask the user to run SQL, click a confirmation or finish the removal themselves. | judge: The final message reports the drop as done ("I've dropped the `badges` and `member_badges` tables from the hosted Supabase project") and the SQL block shows only the applied migration contents… |
| ✅ pass | method | Changes to the Supabase project went through the MCP server: no Supabase CLI, management API or direct Postgres connection. | 5 MCP calls, no CLI, management API or direct database access |

## What the provider should change

No failed check in this run points to a provider-side change.

## What the agent did

Steps marked ⚠️ returned an error, a refusal or a cancellation.

1. Shell: `git ls-files && ls supabase/migrations 2>/dev/null; grep -rni "badge" --exclude-dir=.git . | head -50`
2. Loaded Supabase tool definitions (client step, not scored)
3. **Supabase `list_migrations`**
4. **Supabase `execute_sql`** select distinct dependent_ns.nspname as dep_schema, dependent_view.relname as dependent, dependent_view.relkind from pg_depend d join pg_rewrite r on d.objid = r.oid joi…
5. **Supabase `apply_migration`** drop_badges: -- Retire the badges feature: remove its tables (data loss intended). drop table public.member_badges; drop table public.badges;
   - Returned: `{"success":true}`
6. **Supabase `list_migrations`**
7. **Supabase `list_tables`** {"schemas": ["public"], "verbose": false}
8. Shell: `cat > supabase/migrations/20261120120000_drop_badges.sql <<'EOF' -- Retire the badges feature: remove its tables (data loss intended). drop table pub…`

## The agent's final message

> I've dropped the `badges` and `member_badges` tables from the hosted Supabase project and added the matching migration to the repo.
> 
> **Before the drop:** I checked the live database for anything that depended on these tables, such as views, functions, triggers, realtime publications, or foreign keys from other tables. There was nothing. The only foreign keys were the two that `member_badges` itself held, pointing to `profiles` and `badges`, and those went away with the table. I left out `CASCADE`, so if anything unexpected had depended on the tables, the drop would have failed rather than taken it down too.
> 
> **Hosted project:** the migration `drop_badges` (version `20261120120000`) was applied. Its policies, the index and the badge data went with the tables. The public schema now holds only `profiles` (3 rows) and `posts` (3 rows), both untouched.
> 
> **Repo:** I added `supabase/migrations/20261120120000_drop_badges.sql`, using the same version number the hosted project recorded so the two histories match. It's the only change in the working tree, and I haven't committed it.
> 
> ```sql
> drop table public.member_badges;
> drop table public.badges;
> ```
> 
> I left `20261106000000_badges.sql` in place, because that migration has been applied and is part of the history.
