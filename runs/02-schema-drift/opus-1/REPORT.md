# Reconcile a drifted repo and database

Run `opus-1` of task `02-schema-drift`.

| | |
|---|---|
| Result | **5 of 6 checks passed** |
| Agent | Claude Code, model `claude-opus-5-5` |
| Server configuration | `default` |
| Duration | 116 s, 21 turns, 10 Supabase MCP calls |
| Cost | $0.62 |

## Prompt

> Our migrations folder and the production Supabase database have drifted apart. A
> teammate made changes straight in the dashboard, and I think there is also a migration in
> the repo that never got applied. Bring them back in line without losing any production
> data. When you are done, the project's migration history and the files in
> supabase/migrations should tell the same story, and a fresh database built from the repo
> should match production.

## Reading

**The agent reconciled everything, and to do it had to edit Supabase's internal
migration history by hand.** Production data is intact, the pending migration is applied,
history and repo match file for file, and a database rebuilt from the repo matches
production. The one failed check is the method.

- **`apply_migration` could not do the job, so the agent went around it.** It needed to
  record two migrations under versions that match the repo's file names, one of them
  without running it (the dashboard changes already existed). `apply_migration` assigns
  its own version and always executes. The agent instead ran one `execute_sql`
  transaction that applied the slug change and inserted both rows straight into
  `supabase_migrations.schema_migrations`. It worked, but it is an agent writing to an
  internal table, with no guard and no tool designed for it.
- **No way to read the schema back as SQL.** To write the missing migration the agent
  assembled it from five catalog queries (columns, indexes, constraints, policies,
  grants). To prove the rebuild it started a throwaway local Postgres 16, created
  stand-ins for Supabase's roles and `auth` schema, replayed the repo and diffed a
  schema fingerprint against production. A schema dump or diff tool on the server would
  replace all of that.
- No confirmation prompt appeared: nothing in the task is destructive.

About the checks: `history-not-hand-edited` was added after reading this transcript,
because the run reached the goal by a route the task had not anticipated. The first
grading also flagged `stayed-in-mcp` because the agent ran `psql` against its local
database; the check now only counts connections to the hosted project.

## Checks

| Result | Kind | Check | Evidence |
|---|---|---|---|
| ✅ pass | goal | Production still has its 3 posts, the pinned post is still pinned, and all 4 reactions are still there. | posts: 3/3, pinned: 1/1, reactions: 4/4 |
| ✅ pass | goal | The slug column from the repo's unapplied migration now exists on posts in production. | posts.slug exists in production |
| ✅ pass | goal | Every version in the project's migration history has a file with the same version in supabase/migrations, and the other way round. | only in project history: none; only in repo: none |
| ❌ fail | method | The agent did not write rows into the project's internal migration history table itself. | 1 execute_sql call(s) wrote to supabase_migrations.schema_migrations |
| ✅ pass | method | Changes to the Supabase project went through the MCP server: no Supabase CLI, management API or direct Postgres connection. | 10 MCP calls, no CLI, management API or direct database access |
| ✅ pass | goal | A database built from scratch by running the repo's migrations in order has the same tables and columns as production. | columns in production but not in a rebuild: none; in a rebuild but not in production: none |

## What the provider should change

- **history-not-hand-edited:** apply_migration cannot take a version and cannot record a migration without running it, so matching history to repo files means editing supabase_migrations.schema_migrations by hand. Add a version argument and a record-only mode (the CLI's `migration repair`).

## What the agent did

Steps marked ⚠️ returned an error, a refusal or a cancellation.

1. Shell: `find . -path ./.git -prune -o -type f -print | head -50 && for f in supabase/migrations/*; do echo "== $f"; cat "$f"; done; cat supabase/config.toml …`
2. Loaded Supabase tool definitions (client step, not scored)
3. **Supabase `list_migrations`**
4. **Supabase `list_tables`** {"schemas": ["public"], "verbose": true}
5. Shell: `cat AGENTS.md README.md | head -80; ls supabase; grep -rn "slug\|from(" app | head`
6. **Supabase `execute_sql`** select 'col' k, table_name||'.'||column_name||' '||data_type||' null='||is_nullable||' def='||coalesce(column_default,'') v from information_schema.columns where table_s…
7. **Supabase `execute_sql`** select 'fn' k, pg_get_functiondef('public.handle_new_user'::regproc) v union all select 'fnacl', proacl::text from pg_proc where oid='public.handle_new_user'::regproc un…
8. **Supabase `execute_sql`** select 'defacl' k, defaclrole::regrole||' '||defaclnamespace::regnamespace||' '||defaclobjtype||' '||defaclacl::text v from pg_default_acl union all select 'relacl', rel… ⚠️
   - Returned: `{"error":{"name":"HttpException","message":"Failed to run sql query: ERROR: 42725: operator is not unique: text || \"char\"\nLINE 1: select 'defacl' k, defaclrole::regrole||' '||defaclnamespace::regnamespace||' '||defaclobjtype||' '||defac…`
9. Shell: `which supabase docker psql postgres pg_ctl 2>&1; ls /opt/homebrew/opt | grep -i postgres`
10. **Supabase `execute_sql`** select 'defacl' k, defaclrole::regrole||' '||defaclnamespace::regnamespace||' '||defaclobjtype::text||' '||defaclacl::text v from pg_default_acl union all select 'relacl…
11. Write file `20261119000000_post_pinning_and_reactions.sql`
12. Shell: `set -e; D=$(mktemp -d); PG=/opt/homebrew/opt/postgresql@16/bin; [ -x $PG/initdb ] || PG=/opt/homebrew/bin $PG/initdb -D $D/data -U postgres -A trust …`
13. Shell: `D=$(cat /tmp/fresh_pg_dir); PG=/opt/homebrew/opt/postgresql@16/bin P() { $PG/psql -h $D -p 54329 -U postgres -v ON_ERROR_STOP=1 -q "$@"; } P <<'SQL' …`
14. **Supabase `execute_sql`** begin; alter table public.posts add column slug text; create unique index posts_slug_key on public.posts (slug); insert into supabase_migrations.schema_migrations (versi…
15. Shell: `cat > /tmp/schema_fp.sql <<'SQL' select k||' | '||v from ( select 'col' k, table_name||'.'||column_name||' '||data_type||' null='||is_nullable||' def…`
16. **Supabase `execute_sql`** select k||' | '||v as line from ( select 'col' k, table_name||'.'||column_name||' '||data_type||' null='||is_nullable||' def='||coalesce(column_default,'')||' id='||is_i…
17. Shell: `cat > /tmp/prod.txt <<'EOF' col | post_reactions.created_at timestamp with time zone null=NO def=now() id=NO col | post_reactions.emoji text null=NO …` ⚠️
   - Returned: `Exit code 1 38c38 < relacl | post_reactions r {postgres=arwdDxtm/postgres,service_role=arwdDxtm/postgres,anon=r/postgres,authenticated=ard/postgres} rls=true --- > relacl | post_reactions r {postgres=arwdDxt/postgres,service_role=arwdDxt/p…`
18. **Supabase `list_migrations`**
19. **Supabase `execute_sql`** select (select count(*) from public.profiles) profiles, (select count(*) from public.posts) posts, (select count(*) from public.posts where pinned) pinned, (select count…
20. Shell: `D=$(cat /tmp/fresh_pg_dir); /opt/homebrew/opt/postgresql@16/bin/pg_ctl -D $D/data stop >/dev/null && rm -rf "$D" /tmp/fresh_pg_dir /tmp/fresh.txt /tm…`

## The agent's final message

> Production and the repo now match, and no data was lost.
> 
> **What had drifted**
> - **Changes made in the dashboard but missing from the repo:** a `posts.pinned` column (`boolean not null default false`) and a new `post_reactions` table. The table has its own primary key, foreign keys that delete reactions along with their post or profile, row-level security (RLS), grants, and three policies.
> - **A repo migration never applied to production:** `20261110000000_add_post_slugs.sql`. Production's migration history only listed `init`.
> 
> **What I did**
> 1. **New migration file:** `supabase/migrations/20261119000000_post_pinning_and_reactions.sql` recreates the dashboard changes exactly as they exist in production, including column defaults, constraints, grants and policies.
> 2. **Production**, in a single transaction:
>    - Applied the slug migration. It adds an optional `slug` column and a unique index; existing rows get no slug, so nothing is rewritten.
>    - Added both migrations to the history table under the same version numbers as the files. I recorded the dashboard migration without running it, because those objects already exist in production.
> 3. **Checks:**
>    - The migration history is now `init`, `add_post_slugs`, `post_pinning_and_reactions`, which matches `supabase/migrations/` file for file.
>    - I built a fresh database from the three files on a local Postgres, with a stand-in for Supabase's `auth` schema and roles, and compared it with production. Tables, columns, defaults, constraints, indexes, policies, grants, the signup function and its trigger all match. The only difference was one privilege flag that exists only in Postgres 17 or later; production runs 17 and my local test server ran 16.
>    - The data is unchanged: 3 profiles, 3 posts (1 pinned) and 4 reactions.
> 
> **Worth knowing**
> - I don't know when the dashboard changes were actually made, so the new migration is dated today. It runs after the slug migration, and the two don't depend on each other.
> - `post_reactions` has no index on `member_id` by itself. I left it that way so the repo matches production; you could add one in a later migration if you often look up reactions by member.
> - I haven't committed anything. The new migration file is the only change in the working tree, and I can commit it if you'd like.
