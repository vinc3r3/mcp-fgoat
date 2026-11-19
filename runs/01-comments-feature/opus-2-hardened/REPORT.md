# Ship a comments feature end to end

Run `opus-2-hardened` of task `01-comments-feature`.

| | |
|---|---|
| Result | **10 of 11 checks passed** |
| Agent | Claude Code, model `claude-opus-5-5` |
| Server configuration | `default` |
| Duration | 159 s, 32 turns, 12 Supabase MCP calls |
| Cost | $0.66 |

## Prompt

> Add comments to Trailhead. Under each post on the home page, show its comments with the
> author's name, and give signed-in members a box to add one. Members can delete their own
> comments but nobody else's; visitors can read but not write. Store them in a new
> `comments` table. Ship it to our hosted Supabase project so it works for the test
> accounts in the README, and keep the repo's migrations in step with what you ship.

## Reading

**The grant trap sprang, and the agent's own testing rescued it: 10 of 11.** This is the
hardened version of the task: the repo's baseline migration no longer shows any `grant`
statement. Compare `opus-1`, same model on the original template, 11 of 11.

- **The agent shipped a table nobody could reach.** Its first migration created
  `comments` with row-level security and three policies and no grants.
  `apply_migration` returned `{"success":true}`. It then called `get_advisors`, which
  reported nothing about the new table.
- **It found out only because it tested from outside.** A script signed in with the test
  accounts and got `permission denied for table comments`. The agent then compared
  grants across tables, understood the project does not grant new tables automatically,
  and shipped a second migration, `comments_grants`. Production was broken for the
  minutes in between.
- **What it cost:** 32 turns, 159 seconds and $0.66, against 22 turns, 110 seconds and
  $0.49 for the same model when the repo showed the pattern. Two migrations where one
  would do.

Two places in the server could have said "this table is not reachable through the API":
the migration result and the advisor. Neither did. An agent that does not test from
outside would have finished with a broken feature and a success message.

The check `reachable-from-first-migration` was added after reading this transcript and
the Haiku run of the same task; earlier results for this task were regraded with it.

## Checks

| Result | Kind | Check | Evidence |
|---|---|---|---|
| ✅ pass | goal | A visitor who is not signed in can read comments through the project's API. | GET /comments as visitor -> 200, 1 row(s): [{'id': 4, 'post_id': 1, 'author_id': '1db0f497-7d3f-43bd-83e4-ae6241bd2907', 'body': 'check-7f3a-read', 'created_at': ' |
| ✅ pass | goal | A signed-in member can add a comment to a post. | POST /comments as Alice -> 201; rows stored: 1.  |
| ✅ pass | goal | A visitor who is not signed in cannot add a comment. | POST /comments as visitor -> 401; rows stored: 0 |
| ✅ pass | goal | A member cannot add a comment that is recorded as written by another member. | Alice posting as Bob -> 403; rows recorded under Bob: 0 |
| ✅ pass | goal | A member cannot delete another member's comment, and can delete their own. | after Bob's delete the row survived; after Alice's delete it is gone |
| ✅ pass | goal | The built app serves the home page with status 200 and an existing comment's text appears on it. | GET / -> 200; comment text found in the HTML |
| ❌ fail | method | The change that created the comments table also granted it to the API roles, so the feature was never live in a state where every request was refused. | MCP call #4 created the table with no grant: the API refused every request until a later fix |
| ✅ pass | method | The project's migration history contains a migration that creates the comments table. | 2 recorded migration(s) mention 'comments' (3 total, 1 seeded) |
| ✅ pass | method | The repo's supabase/migrations folder contains a new file that creates the comments table. | new migration files mentioning 'comments': ['20261119114806_comments.sql', '20261119114943_comments_grants.sql'] |
| ✅ pass | hygiene | `npm run build` succeeds in the agent's working directory. | npm run build succeeded |
| ✅ pass | method | Changes to the Supabase project went through the MCP server: no Supabase CLI, management API or direct Postgres connection. | 12 MCP calls, no CLI, management API or direct database access |

## What the provider should change

- **reachable-from-first-migration:** apply_migration returns {"success":true} for a table that has policies but no API grants, and get_advisors does not flag it. Either should say the table is unreachable through the API.

## What the agent did

Steps marked ⚠️ returned an error, a refusal or a cancellation.

1. Shell: `git ls-files && cat README.md && ls supabase/migrations 2>/dev/null && cat supabase/migrations/* 2>/dev/null; cat CLAUDE.md 2>/dev/null` ⚠️
   - Returned: `Exit code 1 .env.example .gitignore AGENTS.md README.md app/favicon.ico app/globals.css app/layout.tsx app/login/page.tsx app/page.tsx eslint.config.mjs lib/supabase/client.ts lib/supabase/server.ts next.config.ts package-lock.json package…`
2. Shell: `cat AGENTS.md app/page.tsx app/login/page.tsx lib/supabase/*.ts package.json .env.example; ls -a; ls node_modules/next/dist/docs 2>/dev/null | head`
3. Loaded Supabase tool definitions (client step, not scored)
4. **Supabase `list_migrations`**
5. **Supabase `list_tables`** {"schemas": ["public"], "verbose": true}
6. **Supabase `get_project_url`**
7. Shell: `grep -o 'https://[a-z0-9]*\.supabase\.co' .env.local`
8. Write file `comments.sql.tmp`
9. Shell: `cat /Users/didar/.cache/mcp-fgoat-runs/01-comments-feature/opus-2-hardened/supabase/migrations/comments.sql.tmp > /dev/null && echo ok`
10. **Supabase `apply_migration`** comments: -- Comments: members comment on posts; anyone can read them. create table public.comments ( id bigint generated always as identity primary key, post_id bigint …
   - Returned: `{"success":true}`
11. **Supabase `list_migrations`**
12. Shell: `cd /Users/didar/.cache/mcp-fgoat-runs/01-comments-feature/opus-2-hardened/supabase/migrations && mv comments.sql.tmp 20261119114806_comments.sql && ls`
13. **Supabase `get_advisors`** {"type": "security"}
14. Shell: `cd /Users/didar/.cache/mcp-fgoat-runs/01-comments-feature/opus-2-hardened && ls -R node_modules/next/dist/docs/01-app | grep -i -E 'mutat|form|action…`
15. Shell: `cd node_modules/next/dist/docs/01-app && f=$(find . -name 07-mutating-data.md); sed -n 1,400p $f | grep -v '^$' | head -220; cat $(find . -name refre…`
16. Write file `actions.ts`
17. Write file `comment-form.tsx`
18. Shell: `cd /Users/didar/.cache/mcp-fgoat-runs/01-comments-feature/opus-2-hardened && python3 - <<'EOF' import re p='app/actions.ts'; s=open(p).read() s=s.rep…`
19. Write file `comment-form.tsx`
20. Shell: `python3 - <<'EOF' p='app/page.tsx'; s=open(p).read() old_start=s.index('async function Posts()') old_end=s.index('export default function Home()') ne…` ⚠️
   - Returned: `Exit code 2 app/layout.tsx(20,50): error TS2304: Cannot find name 'LayoutProps'. app/page.tsx(42,32): error TS2339: Property 'comments' does not exist on type 'GenericStringError'. app/page.tsx(44,30): error TS2339: Property 'id' does not …`
21. Shell: `python3 - <<'EOF' p='app/page.tsx'; s=open(p).read() s=s.replace(''' "id, title, body, created_at, profiles!posts_author_id_fkey(display_name), " + "…`
22. Shell: `mkdir -p /tmp/trailhead-check && cat > /tmp/trailhead-check/rls.mjs <<'EOF' import { createClient } from "@supabase/supabase-js"; const url = process…`
23. **Supabase `execute_sql`** select grantee, string_agg(privilege_type, ',' order by privilege_type) from information_schema.role_table_grants where table_schema='public' and table_name in ('comment…
24. **Supabase `execute_sql`** select table_name, grantee, string_agg(privilege_type, ',' order by privilege_type) privs from information_schema.role_table_grants where table_schema='public' and table…
25. **Supabase `apply_migration`** comments_grants: -- This project does not grant new tables to the API roles automatically. -- Visitors read; members read, add and delete (RLS limits deletes to their ow…
   - Returned: `{"success":true}`
26. **Supabase `list_migrations`**
27. Shell: `cat > supabase/migrations/20261119114943_comments_grants.sql <<'EOF' -- This project does not grant new tables to the API roles automatically. -- Vis…`
28. **Supabase `execute_sql`** select count(*) from public.comments;
29. Shell: `npm run build >/dev/null 2>&1 && (npx next start -p 3457 >/tmp/trailhead-check/server.log 2>&1 &) ; for i in $(seq 1 30); do curl -s localhost:3457 >…`
30. **Supabase `get_advisors`** {"type": "security"}
31. Shell: `rm -rf /tmp/trailhead-check && git status --short`

## The agent's final message

> Comments are live on the hosted Supabase project, and the repo's migrations match what's deployed there (same versions and names). I checked the permission rules against the live project using the README test accounts. I haven't committed anything.
> 
> **Database**
> - `supabase/migrations/20261119114806_comments.sql` creates the `comments` table. Each comment belongs to a post and an author, and is deleted if either one is. A comment's text must be 1–2,000 characters and can't be blank. Database rules let anyone read comments, let a signed-in member add comments only under their own name, and let members delete only their own. There's no rule for editing, so comments can't be changed.
> - `supabase/migrations/20261119114943_comments_grants.sql` was a fix. My first test showed that nobody could read or add comments at all. This project doesn't give the website's visitor and member roles access to new tables automatically. The second migration grants that access: visitors can read, members can read, add and delete. I added it as a new migration rather than editing the one already applied, so the repo still matches the live project.
> 
> **App**
> - `app/page.tsx`: under each post you now see its comments, oldest first, with the author's name and date. Signed-in members see a Delete button on their own comments and a box to add one; visitors see a "Sign in to comment" link.
> - `app/actions.ts`: adding and deleting comments happens on the server. Both check that the user is signed in, and adding also checks the text before saving.
> - `app/comment-form.tsx`: the comment box shows any error message and keeps what you typed if posting fails.
> 
> **Checked**
> - Build, TypeScript and lint all pass.
> - On the live project with alice and bob:
>   - A visitor can read comments but can't add or delete any.
>   - Alice can't post under Bob's name, and a blank comment is refused.
>   - Alice can add a comment, but nobody can edit it.
>   - Bob can't delete Alice's comment; Alice can delete it.
>   - The author's name shows up next to the comment.
> - The test removed its own comments, so the table is empty again.
> - The running app shows the comments section and the sign-in prompt under all three posts.
> - Supabase's security check found nothing new from this change.
> - I didn't click through the add/delete buttons in a browser while signed in. The permission tests cover what happens in the database, but not that last step in the browser.
> 
> **One gap I found, not fixed:**
> - **Missing permissions in the original migration:** the existing `posts` and `profiles` tables have access permissions on the live project that `20261101000000_init.sql` never sets. The README says production is built from the migrations, so a project rebuilt from them would probably have `posts` and `profiles` unreadable from the app. That's how `comments` behaved before my fix. I'd add a small migration that records those permissions; say if you want it.
