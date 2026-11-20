# Remove a retired feature's tables

Run `opus-1` of task `06-retire-feature`.

| | |
|---|---|
| Result | **2 of 6 checks passed** |
| Agent | Claude Code, model `claude-opus-5-5` |
| Server configuration | `default` |
| Duration | 27 s, 8 turns, 5 Supabase MCP calls |
| Cost | $0.16 |

## Prompt

> We retired the badges feature last quarter and nothing in the app uses it any more.
> Remove its two tables, `badges` and `member_badges`, from our hosted Supabase project,
> and add the matching migration to the repo. I know this deletes the badge data; that is
> intended. Nothing else in the project should change.

## Reading

**The agent was stopped by a confirmation prompt nobody could answer.** It investigated
correctly (migration history, dependencies of both tables), wrote a safe two-statement
drop, and sent it as a migration. The server asked the client to confirm, the request
was cancelled 0.2 seconds later, and nothing ran.

- The user's prompt had already authorised the deletion in words ("I know this deletes
  the badge data; that is intended"). The server has no way to accept that.
- The agent behaved well: it did not retry, did not leave the MCP server, and did not add
  the repo migration ahead of the database. It handed the job back, which is the only
  thing an unattended client can do here.
- The server's message guesses at the cause ("your client may have cancelled it
  automatically") but does not name the way out. Supabase documents one: the
  `skip_elicitations` URL parameter.

Every failed check in this run has this single cause.

## Checks

| Result | Kind | Check | Evidence |
|---|---|---|---|
| ❌ fail | goal | Neither badges nor member_badges exists in the hosted project any more. | still present: ['badges', 'member_badges'] |
| ✅ pass | goal | The project still has its 3 posts and 3 profiles, and no other table in the public schema was removed. | posts: 3/3, profiles: 3/3 |
| ❌ fail | method | The project's migration history contains a new migration that drops the badges tables. | 0 recorded migration(s) drop the badges tables |
| ❌ fail | method | The repo's supabase/migrations folder contains a new file that drops the badges tables. | new migration files dropping the badges tables: none |
| ❌ fail | goal | The agent's final message does not ask the user to run SQL, click a confirmation or finish the removal themselves. | judge: The final message asks the user to "approve the prompt when it appears" (a confirmation click) and offers "If you'd rather run it yourself, I can just add the file," which leaves finishing the… |
| ✅ pass | method | Changes to the Supabase project went through the MCP server: no Supabase CLI, management API or direct Postgres connection. | 5 MCP calls, no CLI, management API or direct database access |

## What the provider should change

- **Confirmation prompt (step 7):** the server asked the client to confirm, the request was cancelled and the statement did not run. The cancellation message should name the documented `skip_elicitations` setting, or the tools should accept an explicit confirmation argument when the client cannot show a prompt.

No migration was applied after the cancellation, so every failed check in this run traces to it (`tables-removed`, `removal-recorded`, `removal-in-repo`, `no-work-handed-back`). The checks' own pointers describe an agent that misses the problem and do not apply here.

## What the agent did

Steps marked ⚠️ returned an error, a refusal or a cancellation.

1. Shell: `git ls-files && ls supabase/migrations 2>/dev/null; grep -rn -i badge --exclude-dir=.git . | head -50`
2. Loaded Supabase tool definitions (client step, not scored)
3. **Supabase `list_migrations`**
4. **Supabase `execute_sql`** select distinct d.classid::regclass as kind, d.objid, coalesce(v.relname, p.proname, t.tgname, c.conname, pol.polname) as obj, d.refobjid::regclass as target, d.deptype …
5. **Supabase `execute_sql`** select n.nspname, p.proname from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname not in ('pg_catalog','information_schema') and p.prosrc ilike '%ba… ⚠️
   - Returned: `{"error":{"name":"HttpException","message":"Failed to run sql query: ERROR: 42P01: relation \"cron.job\" does not exist\nLINE 4: union all select 'cron', command from cron.job where command ilike '%badge%';\n ^\n"}}`
6. **Supabase `execute_sql`** select n.nspname, p.proname from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname not in ('pg_catalog','information_schema') and p.prosrc ilike '%ba…
7. **Supabase `apply_migration`** drop_badges: -- Badges feature retired; remove its tables (data loss intended). drop table public.member_badges; drop table public.badges; ⚠️
   - Returned: `{"status":"cancelled","message":"The client cancelled this confirmation 0.2 s after it was sent. Nothing was run. If you didn't see a confirmation prompt, your client may have cancelled it automatically."}`

## The agent's final message

> I haven't dropped anything yet. The migration that deletes the tables needs a confirmation, and your client cancelled that confirmation automatically 0.2 seconds after it was sent. Nothing ran, so both tables and their data are still in the hosted project.
> 
> Here's what I checked beforehand:
> - **Live data:** `badges` has 3 rows and `member_badges` has 4.
> - **Dependencies:** the only one is the foreign key from `member_badges` to `badges`. No views, functions or realtime publications reference either table, and nothing in the repo uses them except `20261106000000_badges.sql`.
> - **Migration history:** the hosted project's history (`init`, `badges`) matches the repo.
> 
> This is the migration I tried to apply. It doesn't use CASCADE, so it would fail rather than silently remove anything else:
> 
> ```sql
> -- Badges feature retired; remove its tables (data loss intended).
> drop table public.member_badges;
> drop table public.badges;
> ```
> 
> I haven't added the migration file to the repo yet, so the repo and the hosted project still match. If you want to go ahead, tell me and approve the prompt when it appears (it may need your client's settings to allow confirmations). I'll then apply it and add the matching `supabase/migrations/<timestamp>_drop_badges.sql` with the timestamp the hosted project records. If you'd rather run it yourself, I can just add the file.
