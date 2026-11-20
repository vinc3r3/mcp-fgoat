# Make a second schema reachable from the apps

Run `opus-1` of task `11-second-schema`.

| | |
|---|---|
| Result | **10 of 13 checks passed** |
| Agent | Claude Code, model `claude-opus-5-5` |
| Server configuration | `default` |
| Duration | 138 s, 24 turns, 10 Supabase MCP calls |
| Cost | $0.60 |

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

**Everything the agent could reach was done right, and the apps still cannot read the
schema: 10 of 13.** The request the mobile app makes returned `406 Invalid schema: stats`
before the run and returns it after.

- **The one missing step has no tool.** The agent read the API's error, which lists the
  exposed schemas, searched the docs through the server, and was sent to a dashboard
  setting. It handed that step back with exact dashboard instructions. It had read the
  `authenticator` role's settings in step 6, the place where the working route lives
  (finding F11), and did not try it. Nothing the server returned suggests it.
- **The rest is correct and ready.** One migration turned on row-level security, granted
  signed-in members read access and added the two policies. The agent could not test
  through the API, so it ran queries as each test member inside the database and got the
  intended result. The three hygiene checks pass, though here only because the schema is
  still closed.
- **The type generator did not help.** The agent called `generate_typescript_types`,
  saw only `public` in the reply, and wrote the `stats` types by hand in the generator's
  layout. The build passes on hand-written types (finding F12).
- **The advisor gap was not exercised.** The agent enabled row-level security before
  anything was exposed, so there was never an open table for `get_advisors` to miss.
- It stayed inside the server throughout, and did not move or copy the tables.

Like task 10, this is a routine project setting with no route an agent finds. Unlike
task 10 a route exists, and a tool or one line in the server's instructions would have
turned this run into a pass.

One check changed after this run. `history-private` first required Bob to read his own
row, so it failed here on the closed schema and not on a leak. It now checks only that
no one else's rows come back, and this run was regraded from 9 to 10 of 13.

## Checks

| Result | Kind | Check | Evidence |
|---|---|---|---|
| ❌ fail | goal | Alice, signed in, reads all 3 rows of member_activity through the project's API, addressing the stats schema as the mobile app does. | Alice GET stats.member_activity -> 406 Invalid schema: stats |
| ❌ fail | goal | Alice, signed in, reads her own 2 rows of reading_history through the stats schema. | Alice GET her stats.reading_history -> 406 Invalid schema: stats |
| ✅ pass | goal | A visitor can still read all 3 posts and their authors' display names. | visitor GET /posts -> 200, 3/3 posts, 3/3 with author names |
| ✅ pass | goal | member_activity and reading_history are still tables in the stats schema with their 3 and 4 rows, and public has no table or view with either name. | stats.member_activity: 3 row(s), stats.reading_history: 4 row(s); same-named objects in public: 0 |
| ✅ pass | goal | `npm run build` succeeds in the repo the agent left behind. | npm run build succeeded |
| ❌ fail | goal | The agent's final message does not ask the user to change a setting in the dashboard or finish any part of the job themselves. | judge: The final message explicitly asks the user to act: "**Step that's still needed:** in the Supabase dashboard, go to Project Settings → Data API → Exposed schemas, add `stats` and save. Then run… |
| ✅ pass | hygiene | A visitor who is not signed in gets no rows from member_activity or reading_history. | visitor GET stats.member_activity -> 406 Invalid schema: stats; visitor GET stats.reading_history -> 406 Invalid schema: stats |
| ✅ pass | hygiene | Bob, signed in, gets none of Alice's or Carol's rows from reading_history. | Bob GET stats.reading_history -> 406 Invalid schema: stats, 0 of them not his |
| ✅ pass | hygiene | Alice, signed in, cannot change Bob's row in member_activity. | Alice PATCH Bob's row -> 406; posts_count 1 -> 1 |
| ✅ pass | method | lib/database.types.ts declares a stats schema that contains member_activity and reading_history. | stats schema declared: True; tables in it: ['member_activity', 'reading_history'] |
| ✅ pass | method | The project's migration history contains at least one migration newer than the two the task started with. | 1 migration(s) recorded beyond the 2 the task started with |
| ✅ pass | method | The repo's supabase/migrations folder contains a new file that mentions the stats schema. | new migration files mentioning 'stats': ['20261120132132_stats_access.sql'] |
| ✅ pass | method | Changes to the Supabase project went through the MCP server: no Supabase CLI, management API or direct Postgres connection. | 10 MCP calls, no CLI, management API or direct database access |

## What the provider should change

- **member-reads-leaderboard:** The server has no tool for the Data API's exposed schemas. The API's own error names the schemas that are exposed, and nothing the server offers can add one. Add tools to read and update Data API settings, or have the server's instructions name the supported route.
- **member-reads-own-history:** Same as member-reads-leaderboard, and after it the grant gap of task 01: a schema outside public needs `grant usage` as well as table grants, and no tool result says so.
- **no-work-handed-back:** Same as member-reads-leaderboard.

## What the agent did

Steps marked ⚠️ returned an error, a refusal or a cancellation.

1. Shell: `git ls-files | grep -v node_modules | head -100 && cat supabase/config.toml 2>/dev/null; ls supabase/migrations; cat supabase/migrations/*`
2. Loaded Supabase tool definitions (client step, not scored)
3. Shell: `cat AGENTS.md README.md app/stats/page.tsx lib/supabase/*.ts lib/database.types.ts .env.example package.json`
4. **Supabase `list_migrations`**
5. **Supabase `execute_sql`** select n.nspname, c.relname, c.relrowsecurity, c.relacl from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='stats';
6. **Supabase `execute_sql`** select rolname, rolconfig from pg_roles where rolname in ('authenticator','anon','authenticated','postgres','service_role'); select nspname, nspacl from pg_namespace whe…
7. Shell: `ls -a; test -f .env.local && sed 's/=.*/=<set>/' .env.local; ls node_modules | head -3`
8. **Supabase `execute_sql`** select json_build_object( 'roles',(select json_agg(json_build_object('r',rolname,'c',rolconfig)) from pg_roles where rolname in ('authenticator','anon','authenticated','…
9. Shell: `set -a && . ./.env.local && set +a && curl -s "$NEXT_PUBLIC_SUPABASE_URL/rest/v1/member_activity?select=*" -H "apikey: $NEXT_PUBLIC_SUPABASE_PUBLISHA…`
10. **Supabase `search_docs`** { searchDocs(query: "using custom schemas expose schema data api", limit: 3) { nodes { title href content } } }
11. Shell: `cd /tmp && python3 -I -c " import json,sys d=json.load(open(sys.argv[1]));t=json.loads(d[0]['text']) for n in t['result']['searchDocs']['nodes']: c=n…`
12. Shell: `which supabase; ls ~/.supabase 2>/dev/null; echo ${SUPABASE_ACCESS_TOKEN:+token-set}`
13. Write file `20261120000000_stats_access.sql`
14. **Supabase `apply_migration`** stats_access: alter table stats.member_activity enable row level security; alter table stats.reading_history enable row level security; grant usage on schema stats to au…
   - Returned: `{"success":true}`
15. **Supabase `list_migrations`**
16. **Supabase `generate_typescript_types`**
17. Shell: `git mv -f supabase/migrations/20261120000000_stats_access.sql supabase/migrations/20261120132132_stats_access.sql 2>/dev/null || mv supabase/migratio…`
18. Shell: `python3 -I - lib/database.types.ts <<'EOF' import sys p=sys.argv[1]; s=open(p).read() stats=''' stats: { Tables: { member_activity: { Row: { display_…`
19. Write file `page.tsx`
20. Shell: `python3 -I - lib/database.types.ts <<'EOF' import sys p=sys.argv[1]; s=open(p).read() def rel(name,col,one,ref): return f''' {{ foreignKeyName: "{nam…` ⚠️
   - Returned: `Exit code 2 app/layout.tsx(20,50): error TS2304: Cannot find name 'LayoutProps'.`
21. Shell: `npm run build 2>&1 | tail -20; npm run lint 2>&1 | tail -5; git status --short`
22. **Supabase `execute_sql`** begin; create temp table _r(who text, leaderboard int, history int, history_others int); grant all on _r to authenticated, anon; do $$ declare u record; begin for u in s…
23. **Supabase `get_advisors`** {"type": "security"}

## The agent's final message

> The database side and the web build are fixed, but the mobile app and the live `/stats` page will keep failing until someone adds `stats` to the project's exposed schemas. That's a dashboard setting I couldn't change with the tools I have. The hosted API still rejects every request with `PGRST106 "Invalid schema: stats" — Only the following schemas are exposed: public, graphql_public`.
> 
> **Step that's still needed:** in the Supabase dashboard, go to Project Settings → Data API → Exposed schemas, add `stats` and save. Then run the type generator and commit its output over `lib/database.types.ts` (more on that file below).
> 
> **What I changed**
> 
> - **New migration, applied to the hosted project:** `supabase/migrations/20261120132132_stats_access.sql`. I named the file after the version the hosted project recorded, so the repo and the database match. Tobias's migration created the tables but turned on no row-level security and gave no role any access. The new migration:
>   - turns on row-level security for both `stats` tables;
>   - lets signed-in members read the schema and select from both tables;
>   - gives the `service_role` key full access, for server-side jobs like the nightly refresh;
>   - adds two read rules: any signed-in member sees the whole `member_activity` leaderboard, and a member sees only their own `reading_history` rows;
>   - grants visitors (`anon`) nothing, not even access to the schema.
> - **`lib/database.types.ts`:** this is what broke the build. `.schema("stats")` didn't type-check because the file had no `stats` schema. The generator only reads exposed schemas, so it can't produce that section yet, and I wrote it by hand in the generator's format. Regenerate it once `stats` is exposed; the only differences should be small details like how the links to `public.profiles` and `public.posts` are listed.
> - **`app/stats/page.tsx`:** visitors now get a "Sign in to see member stats" link instead of a raw "permission denied" error. Signed-in members see the leaderboard as before.
> 
> **What I checked**
> 
> - `npm run build` and `npm run lint` both pass.
> - I queried the hosted database as the real test users:
>   - Alice and Bob each see all 3 leaderboard rows.
>   - Alice sees only her 2 history rows and Bob only his 1, out of 4 in total; neither sees anyone else's.
>   - Visitors have no access to the schema or either table.
> - Supabase's security check reports nothing about the new tables. It flags only one unrelated, existing setting: leaked-password protection is turned off.
> - I couldn't test through the real API, because `stats` isn't exposed yet.
> 
> **Things to know**
> 
> - Members can only read. If the mobile app records reads by writing to `reading_history` itself, those writes will be denied, so tell me and I'll add an insert rule limited to the member's own rows.
> - Visitors calling `stats` get a "permission denied" error rather than an empty list. If the app shows that badly to signed-out users, it should check for a session before calling.
> - I didn't add a reading-history list to the web page, since you only asked to get the page working. The database already allows it.
> - Nothing is committed.
