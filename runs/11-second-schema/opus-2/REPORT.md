# Make a second schema reachable from the apps

Run `opus-2` of task `11-second-schema`.

| | |
|---|---|
| Result | **7 of 13 checks passed** |
| Agent | Claude Code, model `claude-opus-5-5` |
| Server configuration | `default` |
| Duration | 116 s, 23 turns, 11 Supabase MCP calls |
| Cost | $0.62 |

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

**Repeat of `opus-1`, same dead end, lower score: 7 of 13.** The database side was done
correctly again (grants, row-level security, both policies, checked by running queries
as the test members). The schema stayed closed to the API and the last step went back to
the user with dashboard instructions.

- **The build stayed red this time.** The agent called `generate_typescript_types`, saw
  that `stats` was missing from the reply, and declined to write by hand a file the
  prompt says is generated. `app-builds` and `types-cover-stats` fail for that reason,
  not because the agent misread the error.
- **It looked for the Supabase CLI.** It ran `supabase projects list`, found no CLI and
  no token, and said so. `stayed-in-mcp` fails on the attempt; nothing was changed
  outside the server.
- It offered to change the setting through the management API if given a personal access
  token, the same move as in task 10.

## Checks

| Result | Kind | Check | Evidence |
|---|---|---|---|
| ❌ fail | goal | Alice, signed in, reads all 3 rows of member_activity through the project's API, addressing the stats schema as the mobile app does. | Alice GET stats.member_activity -> 406 Invalid schema: stats |
| ❌ fail | goal | Alice, signed in, reads her own 2 rows of reading_history through the stats schema. | Alice GET her stats.reading_history -> 406 Invalid schema: stats |
| ✅ pass | goal | A visitor can still read all 3 posts and their authors' display names. | visitor GET /posts -> 200, 3/3 posts, 3/3 with author names |
| ✅ pass | goal | member_activity and reading_history are still tables in the stats schema with their 3 and 4 rows, and public has no table or view with either name. | stats.member_activity: 3 row(s), stats.reading_history: 4 row(s); same-named objects in public: 0 |
| ❌ fail | goal | `npm run build` succeeds in the repo the agent left behind. | tQueryError<"column 'post_id' does not exist on 'profiles'."> / SelectQueryError<"column 'post_id' does not exist on 'posts'.">'. Property 'post_id' does not exist on type 'SelectQueryError<"column '… |
| ❌ fail | goal | The agent's final message does not ask the user to change a setting in the dashboard or finish any part of the job themselves. | judge: The final message explicitly asks the user to change a dashboard setting: "What I need from you, in the dashboard under Project Settings → Data API → Exposed schemas: 1. Add `stats` and save." |
| ✅ pass | hygiene | A visitor who is not signed in gets no rows from member_activity or reading_history. | visitor GET stats.member_activity -> 406 Invalid schema: stats; visitor GET stats.reading_history -> 406 Invalid schema: stats |
| ✅ pass | hygiene | Bob, signed in, gets none of Alice's or Carol's rows from reading_history. | Bob GET stats.reading_history -> 406 Invalid schema: stats, 0 of them not his |
| ✅ pass | hygiene | Alice, signed in, cannot change Bob's row in member_activity. | Alice PATCH Bob's row -> 406; posts_count 1 -> 1 |
| ❌ fail | method | lib/database.types.ts declares a stats schema that contains member_activity and reading_history. | stats schema declared: False; tables in it: none |
| ✅ pass | method | The project's migration history contains at least one migration newer than the two the task started with. | 1 migration(s) recorded beyond the 2 the task started with |
| ✅ pass | method | The repo's supabase/migrations folder contains a new file that mentions the stats schema. | new migration files mentioning 'stats': ['20261120133127_stats_access.sql'] |
| ❌ fail | method | Changes to the Supabase project went through the MCP server: no Supabase CLI, management API or direct Postgres connection. | 11 MCP call(s); the agent also used: Supabase CLI |

## What the provider should change

- **member-reads-leaderboard:** The server has no tool for the Data API's exposed schemas. The API's own error names the schemas that are exposed, and nothing the server offers can add one. Add tools to read and update Data API settings, or have the server's instructions name the supported route.
- **member-reads-own-history:** Same as member-reads-leaderboard, and after it the grant gap of task 01: a schema outside public needs `grant usage` as well as table grants, and no tool result says so.
- **app-builds:** generate_typescript_types takes no arguments and, in the probe, returned only the public schema. The /stats page compiles only when the types include stats, so the agent has to write them by hand. Accept a list of schemas, as the CLI's `gen types --schema` does.
- **no-work-handed-back:** Same as member-reads-leaderboard.
- **types-cover-stats:** Same as app-builds.
- **stayed-in-mcp:** If the agent left the server to expose the schema, the missing Data API settings tool pushed it there.

## What the agent did

Steps marked ⚠️ returned an error, a refusal or a cancellation.

1. Shell: `cd /Users/dev/.cache/mcp-fgoat-runs/11-second-schema/opus-2; git log --stat | head -50; find . -path ./node_modules -prune -o -path ./.git -prune -o …`
2. Shell: `cd /Users/dev/.cache/mcp-fgoat-runs/11-second-schema/opus-2; cat AGENTS.md README.md supabase/migrations/*.sql app/stats/page.tsx lib/supabase/*.ts l…`
3. Loaded Supabase tool definitions (client step, not scored)
4. **Supabase `list_migrations`**
5. **Supabase `execute_sql`** select n.nspname, c.relname, c.relrowsecurity, c.relforcerowsecurity, (select json_agg(json_build_object('name',polname,'cmd',polcmd,'roles',polroles::regrole[]::text,'q…
6. **Supabase `execute_sql`** select json_agg(x) from ( select n.nspname, c.relname, c.relrowsecurity, c.relforcerowsecurity, c.relacl::text acl, (select json_agg(json_build_object('name',polname,'cm…
7. **Supabase `query_logs`** select timestamp, event_message, log_attributes from logs where source='edge_logs' and event_message ilike '%stats%' order by timestamp desc limit 10
8. Shell: `cd /Users/dev/.cache/mcp-fgoat-runs/11-second-schema/opus-2; cat .env.example; set -a; . ./.env.local; set +a; echo $NEXT_PUBLIC_SUPABASE_URL; curl -…`
9. Shell: `which supabase; supabase projects list 2>&1 | head; ls ~/.supabase 2>/dev/null; echo ${SUPABASE_ACCESS_TOKEN:+token-set}`
10. Write file `20261120000000_stats_access.sql`
11. **Supabase `apply_migration`** stats_access: grant usage on schema stats to authenticated, service_role; grant select on stats.member_activity to authenticated; grant select on stats.reading_history t…
   - Returned: `{"success":true}`
12. **Supabase `list_migrations`**
13. Shell: `cd /Users/dev/.cache/mcp-fgoat-runs/11-second-schema/opus-2; git mv -f supabase/migrations/20261120000000_stats_access.sql supabase/migrations/202611…`
14. **Supabase `execute_sql`** select json_build_object( 'users', (select json_agg(json_build_object('id',id,'email',email)) from auth.users), 'hist', (select json_agg(json_build_object('m',member_id,…
15. **Supabase `execute_sql`** begin; set local role authenticated; select set_config('request.jwt.claims', '{"sub":"bda6df80-9c5e-417b-b325-5f64826aeaa2","role":"authenticated"}', true); create temp …
16. **Supabase `execute_sql`** begin; set local role anon; select has_schema_privilege('stats','usage') usage, has_table_privilege('stats.member_activity','select') lb, has_table_privilege('stats.read… ⚠️
   - Returned: `{"error":{"name":"HttpException","message":"Failed to run sql query: ERROR: 42501: permission denied for schema stats\n"}}`
17. **Supabase `generate_typescript_types`**
18. **Supabase `search_docs`** { searchDocs(query: "expose custom schema Data API", limit: 3) { nodes { title href content } } }
19. Shell: `cd /Users/dev/.claude/projects/-Users-dev--cache-mcp-fgoat-runs-11-second-schema-opus-2/100017cf-6346-488b-a616-c24fd0d31673/tool-results/; python3 -…`
20. Shell: `cd /Users/dev/.cache/mcp-fgoat-runs/11-second-schema/opus-2; cat app/page.tsx app/login/page.tsx app/layout.tsx; ls node_modules | head -3; ls node_m…`
21. Shell: `cd /Users/dev/.cache/mcp-fgoat-runs/11-second-schema/opus-2; npx tsc --noEmit 2>&1 | head -20`
22. Write file `page.tsx`

## The agent's final message

> I've set up access in the database, but the app and the web build are still broken. One step is left that I can't do from here: the `stats` schema has to be exposed in the hosted project's Data API settings. Neither the SQL tools nor the migrations can change that setting, and there's no Supabase CLI or access token on this machine.
> 
> **What's wrong.** The hosted API rejects every request with:
> ```
> PGRST106  Invalid schema: stats
> hint: Only the following schemas are exposed: public, graphql_public
> ```
> Tobias's migration also left the tables with no grants and no row-level security (RLS). So even once the schema is exposed, every request would still fail with "permission denied", and without RLS it would have been all or nothing.
> 
> **What I've done:**
> - **New migration `supabase/migrations/20261120133127_stats_access.sql`, applied to the hosted project.** The file name matches the version the database recorded, so the repo and the database agree.
>   - Signed-in members can read the whole leaderboard (`stats.member_activity`).
>   - Signed-in members can read only rows of `stats.reading_history` where `member_id = auth.uid()`.
>   - Visitors aren't granted anything on the schema, so they're refused before reaching any table.
>   - `service_role` keeps full access for the nightly refresh job.
>   - Supabase's guide on custom schemas says to grant everything to `anon`. I didn't, because you want visitors to get nothing.
> - **Checked against the database:** signed in as Alice, I saw all 3 leaderboard rows, 2 history rows and none of anyone else's. As a visitor I got `permission denied for schema stats`.
> - **`app/stats/page.tsx`:** visitors now get a sign-in link. Members see the leaderboard plus a new "Your reading history" list that shows post titles.
> 
> **What I need from you**, in the dashboard under Project Settings → Data API → Exposed schemas:
> 1. Add `stats` and save. This alone should fix the mobile app; no new release is needed.
> 2. Tell me once it's done. Then I'll:
>    - regenerate `lib/database.types.ts`. The generator skips schemas that aren't exposed, so right now it would leave out `stats`, and I didn't want to hand-write a file you generate.
>    - run the web build. It's still red because those types are missing.
>    - test as Alice, Bob and a visitor through the real API.
> 
> If you'd rather I make that setting change myself, I can do it through the Supabase Management API with a personal access token.
> 
> Two other things to know:
> - Members can only read. Nothing lets them write to `reading_history`. If the mobile app records reads itself, it will need an insert rule, and I can add one that only lets members write their own rows.
> - Nothing is committed yet.
