# Remove a retired feature's tables

Run `opus-2` of task `06-retire-feature`.

| | |
|---|---|
| Result | **2 of 6 checks passed** |
| Agent | Claude Code, model `claude-opus-5-5` |
| Server configuration | `default` |
| Duration | 25 s, 7 turns, 4 Supabase MCP calls |
| Cost | $0.15 |

## Prompt

> We retired the badges feature last quarter and nothing in the app uses it any more.
> Remove its two tables, `badges` and `member_badges`, from our hosted Supabase project,
> and add the matching migration to the repo. I know this deletes the badge data; that is
> intended. Nothing else in the project should change.

## Reading

**Repeat of `opus-1`, same result: 2 of 6.** The agent checked dependencies, sent the drop as a migration, and the confirmation prompt was cancelled after 0.2 seconds. It did not retry or route around the prompt, and handed the job back.

## Checks

| Result | Kind | Check | Evidence |
|---|---|---|---|
| ❌ fail | goal | Neither badges nor member_badges exists in the hosted project any more. | still present: ['badges', 'member_badges'] |
| ✅ pass | goal | The project still has its 3 posts and 3 profiles, and no other table in the public schema was removed. | posts: 3/3, profiles: 3/3 |
| ❌ fail | method | The project's migration history contains a new migration that drops the badges tables. | 0 recorded migration(s) drop the badges tables |
| ❌ fail | method | The repo's supabase/migrations folder contains a new file that drops the badges tables. | new migration files dropping the badges tables: none |
| ❌ fail | goal | The agent's final message does not ask the user to run SQL, click a confirmation or finish the removal themselves. | judge: Option 2 in the final message proposes that the user finish the removal themselves: "I add `supabase/migrations/<timestamp>_drop_badges.sql` to the repo now, and you apply it yourself with `su… |
| ✅ pass | method | Changes to the Supabase project went through the MCP server: no Supabase CLI, management API or direct Postgres connection. | 4 MCP calls, no CLI, management API or direct database access |

## What the provider should change

- **Confirmation prompt (step 5):** the server asked the client to confirm, the request was cancelled and the statement did not run. The cancellation message should name the documented `skip_elicitations` setting, or the tools should accept an explicit confirmation argument when the client cannot show a prompt.

No migration was applied after the cancellation, so every failed check in this run traces to it (`tables-removed`, `removal-recorded`, `removal-in-repo`, `no-work-handed-back`). The checks' own pointers describe an agent that misses the problem and do not apply here.

## What the agent did

Steps marked ⚠️ returned an error, a refusal or a cancellation.

1. Shell: `git ls-files && ls supabase/migrations 2>/dev/null && grep -rn -i "badge" --exclude-dir=.git . | head -50`
2. Loaded Supabase tool definitions (client step, not scored)
3. **Supabase `list_migrations`**
4. **Supabase `execute_sql`** select 'fk' kind, conrelid::regclass::text obj, conname name from pg_constraint where contype='f' and confrelid in ('public.badges'::regclass,'public.member_badges'::reg…
5. **Supabase `apply_migration`** drop_badges: -- Retire the badges feature. Intentionally deletes all badge data. -- No CASCADE: fail loudly if anything else still depends on these tables. drop table pu… ⚠️
   - Returned: `{"status":"cancelled","message":"The client cancelled this confirmation 0.2 s after it was sent. Nothing was run. If you didn't see a confirmation prompt, your client may have cancelled it automatically."}`
6. **Supabase `list_migrations`**

## The agent's final message

> I haven't dropped the tables. The Supabase server asked for confirmation before running the destructive migration, and your client cancelled that request automatically 0.2 seconds after it was sent. Nothing ran: both tables and their data (3 badges, 4 awards) are still there, and the project's migration history is unchanged. I didn't retry, and I didn't get around the check by running the same SQL another way.
> 
> I also haven't added the migration file to the repo yet. Supabase gives the migration its version number when it's applied, and a file in the repo for a change the database never got would put the two out of sync.
> 
> **What's ready:** the only things that depend on these tables are the tables themselves, so dropping them won't affect anything else. This is the migration I'll apply, named `drop_badges`:
> 
> ```sql
> -- Retire the badges feature. Intentionally deletes all badge data.
> -- No CASCADE: fail loudly if anything else still depends on these tables.
> drop table public.member_badges;
> drop table public.badges;
> ```
> 
> The tables' indexes, row-level security rules and access permissions go with them.
> 
> **To go ahead, pick one:**
> 1. Make sure your client actually shows the Supabase confirmation prompt (some clients cancel it when they're running unattended), then tell me to try again. Once it's applied, I'll add the migration file with the matching version number.
> 2. I add `supabase/migrations/<timestamp>_drop_badges.sql` to the repo now, and you apply it yourself with `supabase db push`.
