# Make a second schema reachable from the apps

Run `opus-3` of task `11-second-schema`.

| | |
|---|---|
| Result | **8 of 13 checks passed** |
| Agent | Claude Code, model `claude-opus-5-5` |
| Server configuration | `default` |
| Duration | 95 s, 18 turns, 11 Supabase MCP calls |
| Cost | $0.41 |

## Prompt

> Tobias moved our member stats into their own `stats` schema last week (his migration is
> in the repo and applied), and since then nothing can read them. The mobile app is already
> in the stores and calls `supabase.schema('stats')`, and it gets an error on every
> request. The web build is red on the new `/stats` page too. Get both working against the
> hosted project without moving the tables back into `public`. Signed-in members should
> see the whole activity leaderboard and their own reading history, nobody should see
> anyone else's history, and visitors should get nothing. Keep the repo's migrations and
> `lib/database.types.ts` in step with the database; we generate that file from it.

## Reading

**Repeat of `opus-1`, same dead end: 8 of 13.** Grants, row-level security and both
policies went in through one migration and were checked inside the database. The schema
stayed closed to the API and the agent handed the dashboard step back.

- As in `opus-2`, the agent would not hand-write the types: the generator returned only
  `public`, and the prompt says the file is generated. The build stayed red, so
  `app-builds` and `types-cover-stats` fail.
- It stayed inside the server and did not look for the CLI or a token.
- It called `get_advisors` after row-level security was already on, so the advisor gap
  (F13) was again not exercised.

Across three runs the schema was never exposed, and the agent never tried the role
setting. Scores differ (10, 7 and 8 of 13) only in what the agent did about the types
the generator would not produce and in whether it looked for the CLI.

## Checks

| Result | Kind | Check | Evidence |
|---|---|---|---|
| ❌ fail | goal | Alice, signed in, reads all 3 rows of member_activity through the project's API, addressing the stats schema as the mobile app does. | Alice GET stats.member_activity -> 406 Invalid schema: stats |
| ❌ fail | goal | Alice, signed in, reads her own 2 rows of reading_history through the stats schema. | Alice GET her stats.reading_history -> 406 Invalid schema: stats |
| ✅ pass | goal | A visitor can still read all 3 posts and their authors' display names. | visitor GET /posts -> 200, 3/3 posts, 3/3 with author names |
| ✅ pass | goal | member_activity and reading_history are still tables in the stats schema with their 3 and 4 rows, and public has no table or view with either name. | stats.member_activity: 3 row(s), stats.reading_history: 4 row(s); same-named objects in public: 0 |
| ❌ fail | goal | `npm run build` succeeds in the repo the agent left behind. | er_id' does not exist on 'profiles'."> / SelectQueryError<"column 'member_id' does not exist on 'posts'.">'. Property 'display_name' does not exist on type 'SelectQueryError<"column 'member_id' does … |
| ❌ fail | goal | The agent's final message does not ask the user to change a setting in the dashboard or finish any part of the job themselves. | judge: The final message explicitly asks the user to change a dashboard setting: "To fix it: **Dashboard → Project Settings → Data API → Exposed schemas → add `stats` → Save.**" and says "that's a st… |
| ✅ pass | hygiene | A visitor who is not signed in gets no rows from member_activity or reading_history. | visitor GET stats.member_activity -> 406 Invalid schema: stats; visitor GET stats.reading_history -> 406 Invalid schema: stats |
| ✅ pass | hygiene | Bob, signed in, gets none of Alice's or Carol's rows from reading_history. | Bob GET stats.reading_history -> 406 Invalid schema: stats, 0 of them not his |
| ✅ pass | hygiene | Alice, signed in, cannot change Bob's row in member_activity. | Alice PATCH Bob's row -> 406; posts_count 1 -> 1 |
| ❌ fail | method | lib/database.types.ts declares a stats schema that contains member_activity and reading_history. | stats schema declared: False; tables in it: none |
| ✅ pass | method | The project's migration history contains at least one migration newer than the two the task started with. | 1 migration(s) recorded beyond the 2 the task started with |
| ✅ pass | method | The repo's supabase/migrations folder contains a new file that mentions the stats schema. | new migration files mentioning 'stats': ['20261120133428_stats_api_access.sql'] |
| ✅ pass | method | Changes to the Supabase project went through the MCP server: no Supabase CLI, management API or direct Postgres connection. | 11 MCP calls, no CLI, management API or direct database access |

## What the provider should change

- **member-reads-leaderboard:** The server has no tool for the Data API's exposed schemas. The API's own error names the schemas that are exposed, and nothing the server offers can add one. Add tools to read and update Data API settings, or have the server's instructions name the supported route.
- **member-reads-own-history:** Same as member-reads-leaderboard, and after it the grant gap of task 01: a schema outside public needs `grant usage` as well as table grants, and no tool result says so.
- **app-builds:** generate_typescript_types takes no arguments and, in the probe, returned only the public schema. The /stats page compiles only when the types include stats, so the agent has to write them by hand. Accept a list of schemas, as the CLI's `gen types --schema` does.
- **no-work-handed-back:** Same as member-reads-leaderboard.
- **types-cover-stats:** Same as app-builds.

## What the agent did

Steps marked ⚠️ returned an error, a refusal or a cancellation.

1. Shell: `git ls-files | grep -v node_modules | head -50 && cat supabase/config.toml 2>/dev/null | head -40; ls supabase/migrations; cat supabase/migrations/*`
2. Shell: `cat AGENTS.md README.md app/stats/page.tsx lib/supabase/*.ts lib/database.types.ts package.json .env.example`
3. Loaded Supabase tool definitions (client step, not scored)
4. **Supabase `list_migrations`**
5. **Supabase `execute_sql`** select n.nspname, c.relname, c.relrowsecurity, c.relforcerowsecurity, c.relacl from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='stats';
6. **Supabase `execute_sql`** select nspname, nspacl from pg_namespace where nspname in ('stats','public'); select rolname, rolconfig from pg_roles where rolname in ('authenticator','anon','authentic…
7. Shell: `ls -a; set -a; . ./.env.local; set +a; curl -s "$NEXT_PUBLIC_SUPABASE_URL/rest/v1/member_activity?select=*" -H "apikey: $NEXT_PUBLIC_SUPABASE_PUBLISH…` ⚠️
   - Returned: `Exit code 1 . .. .env.example .env.local .git .gitignore AGENTS.md app eslint.config.mjs lib next-env.d.ts next.config.ts node_modules package-lock.json package.json public README.md supabase tsconfig.json {"code":"PGRST106","details":null…`
8. **Supabase `apply_migration`** stats_api_access: -- Make the stats schema readable through the Data API for signed-in members only. -- Visitors (anon) get no access to the schema at all. grant usage o…
   - Returned: `{"success":true}`
9. **Supabase `list_migrations`**
10. Shell: `cat > supabase/migrations/20261120133428_stats_api_access.sql <<'EOF' -- Make the stats schema readable through the Data API for signed-in members on…`
11. **Supabase `generate_typescript_types`**
12. **Supabase `execute_sql`** select u.email, (select count(*) from stats.reading_history r where r.member_id=u.id) n from auth.users u where email in ('alice@example.com','bob@example.com','carol@ex… ⚠️
   - Returned: `{"error":{"name":"HttpException","message":"Failed to run sql query: ERROR: 42501: permission denied for table users\nHINT: Grant the required privileges to the current role with: GRANT SELECT ON auth.users TO authenticated;\n"}}`
13. **Supabase `execute_sql`** select set_config('my.alice', (select id::text from auth.users where email='alice@example.com'), false) is not null; begin; select set_config('request.jwt.claims', json_…
14. **Supabase `execute_sql`** select (select count(*) from stats.member_activity) total_lb, (select count(distinct member_id) from stats.reading_history) total_owners; begin; set local role anon; sel… ⚠️
   - Returned: `{"error":{"name":"HttpException","message":"Failed to run sql query: ERROR: 42501: permission denied for schema stats\n"}}`
15. **Supabase `execute_sql`** select current_user, has_schema_privilege('anon','stats','usage') anon_usage, has_table_privilege('anon','stats.member_activity','select') anon_lb, has_table_privilege('…
16. **Supabase `get_advisors`** {"type": "security"}
17. Shell: `python3 - <<'EOF' p='app/stats/page.tsx' s=open(p).read() s=s.replace(''' const supabase = await createClient(); const { data: members''',''' const s…`

## The agent's final message

> Signed-in members now have the right database access to the stats tables, and visitors have none. But the app and the web build still won't work until one dashboard setting is changed, and that's a step for you.
> 
> **The remaining blocker.** The hosted project's API only serves the `public` and `graphql_public` schemas. A request to `stats` with the project's key still returns `PGRST106 Invalid schema: stats`, which is the error the mobile app gets. Which schemas the API serves is a project setting, not something a migration controls, so I can't change it through the database tools I have. To fix it: **Dashboard → Project Settings → Data API → Exposed schemas → add `stats` → Save.** The mobile app should start working as soon as that's saved; it doesn't need a new release.
> 
> **What I changed on the hosted database.** The `stats` tables had no grants and row-level security was off, so even with the schema exposed every read would have failed. I applied a new migration, `20261120133428_stats_api_access`, and saved the same SQL to `supabase/migrations/20261120133428_stats_api_access.sql`, so the repo's migrations match the database. It:
> - lets signed-in members use the `stats` schema; visitors get no access to it at all.
> - turns on row-level security for both tables.
> - lets any signed-in member read the whole `member_activity` leaderboard.
> - lets a member read only the `reading_history` rows that belong to them.
> 
> I checked it directly in the database: signed in as alice, all 3 leaderboard rows are visible and only alice's own 2 history rows come back. The visitor role has no access to the schema or either table. Supabase's security check found nothing new; its only warning is the existing one that leaked-password protection is turned off.
> 
> **Web app.** `app/stats/page.tsx` now shows "Sign in to see member stats." to visitors instead of a permission error. The build is still red: `lib/database.types.ts` doesn't describe `stats` yet, because the type generator only includes schemas the API serves. I didn't write those types by hand, since that file is generated from the database. Once `stats` is exposed, regenerate the types (I can do it, or run `supabase gen types typescript`) and the `/stats` type errors should go away. Separately, `npx tsc` also reports a `LayoutProps` error in `app/layout.tsx`; I haven't looked into that, so it may need its own fix.
> 
> **Decision for you:** members can only *read* the stats tables, as you asked. If the mobile app also writes reading history (logging a post as opened), those writes will still be rejected. That would need an insert rule limited to the member's own rows. Tell me if it does and I'll add it.
> 
> Nothing is committed yet. Once you've exposed the schema, say so and I'll regenerate the types, run the build and commit.
