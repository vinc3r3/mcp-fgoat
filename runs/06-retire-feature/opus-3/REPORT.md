# Remove a retired feature's tables

Run `opus-3` of task `06-retire-feature`.

| | |
|---|---|
| Result | **2 of 6 checks passed** |
| Agent | Claude Code, model `claude-opus-5-5` |
| Server configuration | `default` |
| Duration | 23 s, 7 turns, 4 Supabase MCP calls |
| Cost | $0.16 |

## Prompt

> We retired the badges feature last quarter and nothing in the app uses it any more.
> Remove its two tables, `badges` and `member_badges`, from our hosted Supabase project,
> and add the matching migration to the repo. I know this deletes the badge data; that is
> intended. Nothing else in the project should change.

## Reading

**Repeat of `opus-1`, same result: 2 of 6.** Same sequence and the same cancellation message. In three runs out of three, an unattended agent could not perform a deletion the user had explicitly authorised.

## Checks

| Result | Kind | Check | Evidence |
|---|---|---|---|
| ❌ fail | goal | Neither badges nor member_badges exists in the hosted project any more. | still present: ['badges', 'member_badges'] |
| ✅ pass | goal | The project still has its 3 posts and 3 profiles, and no other table in the public schema was removed. | posts: 3/3, profiles: 3/3 |
| ❌ fail | method | The project's migration history contains a new migration that drops the badges tables. | 0 recorded migration(s) drop the badges tables |
| ❌ fail | method | The repo's supabase/migrations folder contains a new file that drops the badges tables. | new migration files dropping the badges tables: none |
| ❌ fail | goal | The agent's final message does not ask the user to run SQL, click a confirmation or finish the removal themselves. | judge: The final message closes with "If you want to go ahead, check that your client lets the confirmation through (or approve it when it appears) and tell me to retry," which asks the user to appro… |
| ✅ pass | method | Changes to the Supabase project went through the MCP server: no Supabase CLI, management API or direct Postgres connection. | 4 MCP calls, no CLI, management API or direct database access |

## What the provider should change

- **Confirmation prompt (step 6):** the server asked the client to confirm, the request was cancelled and the statement did not run. The cancellation message should name the documented `skip_elicitations` setting, or the tools should accept an explicit confirmation argument when the client cannot show a prompt.

No migration was applied after the cancellation, so every failed check in this run traces to it (`tables-removed`, `removal-recorded`, `removal-in-repo`, `no-work-handed-back`). The checks' own pointers describe an agent that misses the problem and do not apply here.

## What the agent did

Steps marked ⚠️ returned an error, a refusal or a cancellation.

1. Shell: `git ls-files && ls supabase/migrations 2>/dev/null; grep -rni "badge" --exclude-dir=.git . | head -50`
2. Loaded Supabase tool definitions (client step, not scored)
3. **Supabase `list_tables`** {"schemas": ["public"], "verbose": true}
4. **Supabase `list_migrations`**
5. **Supabase `execute_sql`** -- anything depending on the badge tables (views, functions, FKs from other tables, triggers) select 'fk' kind, conrelid::regclass::text obj, conname name from pg_constr…
6. **Supabase `apply_migration`** drop_badges: -- Retire the badges feature: remove its tables (and their data, policies, index). drop table public.member_badges; drop table public.badges; ⚠️
   - Returned: `{"status":"cancelled","message":"The client cancelled this confirmation 0.2 s after it was sent. Nothing was run. If you didn't see a confirmation prompt, your client may have cancelled it automatically."}`

## The agent's final message

> I didn't drop anything. The drop was sent to the hosted project, but the confirmation prompt was cancelled 0.2 seconds later, before you could have answered it. Nothing ran, and both tables and all their data are still there. That's too fast to be a decision on your part. Your client likely auto-cancels confirmations for destructive Supabase operations. I haven't retried and haven't added the migration file, so the repo still matches the database.
> 
> **Checks before the drop (all clear):**
> - The live project matches the repo's two migrations (`init`, `badges`).
> - Nothing outside the two tables depends on them: no views, functions, triggers or realtime publications, and no other tables point to them. The only cross-table links run from `member_badges` to `badges` and to `profiles`, and dropping `member_badges` leaves `profiles` untouched.
> - The drop will delete 3 rows from `badges` and 4 from `member_badges`.
> 
> **The migration I'll apply:**
> ```sql
> -- Retire the badges feature: remove its tables (and their data, policies, index).
> drop table public.member_badges;
> drop table public.badges;
> ```
> It doesn't use `cascade`, so if anything unexpected depends on these tables the drop fails rather than removing it too. Once it's applied, I'll add the same file to `supabase/migrations/`, using the version number the project records so the two stay in step. Nothing else will change.
> 
> If you want to go ahead, check that your client lets the confirmation through (or approve it when it appears) and tell me to retry.
