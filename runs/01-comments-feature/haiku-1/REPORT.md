# Ship a comments feature end to end

Run `haiku-1` of task `01-comments-feature`.

| | |
|---|---|
| Result | **10 of 11 checks passed** |
| Agent | Claude Code, model `claude-haiku-5-5` |
| Server configuration | `default` |
| Duration | 159 s, 37 turns, 16 Supabase MCP calls |
| Cost | $0.03 |

## Prompt

> Add comments to Trailhead. Under each post on the home page, show its comments with the
> author's name, and give signed-in members a box to add one. Members can delete their own
> comments but nobody else's; visitors can read but not write. Store them in a new
> `comments` table. Ship it to our hosted Supabase project so it works for the test
> accounts in the README, and keep the repo's migrations in step with what you ship.

## Reading

**Same task, smaller model, same trap, same rescue: 10 of 11.** Haiku on the hardened
task behaved almost exactly like Opus on it.

- **It shipped the table without grants**, got `{"success":true}`, and learned of the
  problem only when it loaded the home page in a dev server and saw
  `Could not load comments: permission denied for table comments`. It then shipped a
  `comments_grants` migration.
- **It also hit the confirmation prompt, on a test.** To verify its policies it sent a
  `do $$ … $$` block through `execute_sql` that impersonated the two test members. The
  server asked for confirmation and the request was cancelled after 0.2 seconds
  (finding F1). The agent switched to testing through the public API. So the prompt is
  not limited to `drop` statements: an anonymous code block used for verification
  triggers it too.
- **The missing version (finding F5):** it wrote `20261119120000_comments.sql`, applied,
  called `list_migrations` and renamed the file to `20261119115226_…`.

37 turns and 16 Supabase MCP calls, against 22 turns and 7 calls for Opus on the
original template. The provider-side gaps show up as extra work on both models.

## Checks

| Result | Kind | Check | Evidence |
|---|---|---|---|
| ✅ pass | goal | A visitor who is not signed in can read comments through the project's API. | GET /comments as visitor -> 200, 1 row(s): [{'id': 4, 'post_id': 1, 'author_id': 'f56d9bf0-63db-4ae4-83f6-4d267a23b3b4', 'body': 'check-7f3a-read', 'created_at': ' |
| ✅ pass | goal | A signed-in member can add a comment to a post. | POST /comments as Alice -> 201; rows stored: 1.  |
| ✅ pass | goal | A visitor who is not signed in cannot add a comment. | POST /comments as visitor -> 401; rows stored: 0 |
| ✅ pass | goal | A member cannot add a comment that is recorded as written by another member. | Alice posting as Bob -> 403; rows recorded under Bob: 0 |
| ✅ pass | goal | A member cannot delete another member's comment, and can delete their own. | after Bob's delete the row survived; after Alice's delete it is gone |
| ✅ pass | goal | The built app serves the home page with status 200 and an existing comment's text appears on it. | GET / -> 200; comment text found in the HTML |
| ❌ fail | method | The change that created the comments table also granted it to the API roles, so the feature was never live in a state where every request was refused. | MCP call #3 created the table with no grant: the API refused every request until a later fix |
| ✅ pass | method | The project's migration history contains a migration that creates the comments table. | 2 recorded migration(s) mention 'comments' (3 total, 1 seeded) |
| ✅ pass | method | The repo's supabase/migrations folder contains a new file that creates the comments table. | new migration files mentioning 'comments': ['20261119115226_comments.sql', '20261119115359_comments_grants.sql'] |
| ✅ pass | hygiene | `npm run build` succeeds in the agent's working directory. | npm run build succeeded |
| ✅ pass | method | Changes to the Supabase project went through the MCP server: no Supabase CLI, management API or direct Postgres connection. | 16 MCP calls, no CLI, management API or direct database access |

## What the provider should change

- **Confirmation prompt (step 22):** the server asked the client to confirm, the request was cancelled and the statement did not run. The cancellation message should name the documented `skip_elicitations` setting, or the tools should accept an explicit confirmation argument when the client cannot show a prompt.
- **reachable-from-first-migration:** apply_migration returns {"success":true} for a table that has policies but no API grants, and get_advisors does not flag it. Either should say the table is unreachable through the API.

## What the agent did

Steps marked ⚠️ returned an error, a refusal or a cancellation.

1. Shell: `git status && git log --oneline | head -5 && find . -path ./node_modules -prune -o -path ./.git -prune -o -type f -print | head -200 && cat README.md`
2. Shell: `cat AGENTS.md && cat supabase/migrations/*.sql && cat app/page.tsx app/layout.tsx app/login/page.tsx lib/supabase/*.ts && cat package.json .env.examp…`
3. **Supabase `list_migrations`**
4. **Supabase `list_tables`** {"schemas": ["public"]}
5. Shell: `ls node_modules/next/dist/docs/ | head -50 && grep -ril "server action" node_modules/next/dist/docs/ | head -20`
6. Shell: `sed -n 1,200p node_modules/next/dist/docs/01-app/01-getting-started/07-mutating-data.md`
7. Write file `20261119120000_comments.sql`
8. **Supabase `apply_migration`** comments: create table public.comments ( id bigint generated always as identity primary key, post_id bigint not null references public.posts (id) on delete cascade, auth…
   - Returned: `{"success":true}`
9. **Supabase `list_migrations`**
10. Shell: `mv supabase/migrations/20261119120000_comments.sql supabase/migrations/20261119115226_comments.sql && ls supabase/migrations`
11. Read file `page.tsx`
12. Write file `actions.ts`
13. Write file `comment-form.tsx`
14. Write file `delete-comment-button.tsx`
15. Write file `post-comments.tsx`
16. Edit file `page.tsx`
17. Shell: `npx tsc --noEmit 2>&1 | tail -30; echo "TSC EXIT ${PIPESTATUS[0]}"; npm run lint 2>&1 | tail -30; echo "LINT DONE"; timeout 300 npm run build 2>&1 | …`
18. Shell: `npm run build 2>&1 | tail -40; echo "BUILD EXIT ${PIPESTATUS[0]}"; git stash list >/dev/null; git status --short`
19. **Supabase `execute_sql`** select p.id, p.display_name, u.email from public.profiles p join auth.users u on u.id = p.id order by u.email; select id, title, author_id from public.posts order by id;…
20. **Supabase `execute_sql`** select p.id, p.display_name, u.email from public.profiles p join auth.users u on u.id = p.id order by u.email;
21. **Supabase `execute_sql`** select id, title, author_id from public.posts order by id;
22. **Supabase `execute_sql`** do $$ declare alice uuid := 'f56d9bf0-63db-4ae4-83f6-4d267a23b3b4'; bob uuid := 'c12642fb-e2cf-4dc1-ad5a-6f56f4f6ae0a'; r text := ''; n int; begin insert into public.com… ⚠️
   - Returned: `{"status":"cancelled","message":"The client cancelled this confirmation 0.2 s after it was sent. Nothing was run. If you didn't see a confirmation prompt, your client may have cancelled it automatically."}`
23. **Supabase `execute_sql`** select count(*) as comment_rows from public.comments;
24. **Supabase `get_advisors`** {"type": "security"}
25. Shell: `(npx next dev -p 3123 > /tmp/trailhead-dev.log 2>&1 &) ; for i in $(seq 1 30); do curl -s -o /dev/null http://localhost:3123/ && break; sleep 1; done…` ⚠️
   - Returned: `1 Could not load comments: 1 Could not load comments: \",\"permission denied for table comments\"]},\"$48\",\"$a0\",1]\n"]) login 200 - Partial Prefetching enabled GET / 200 in 1389ms (next.js: 99ms, application-code: 1290ms) GET / 200 in …`
26. **Supabase `execute_sql`** select table_name, grantee, string_agg(privilege_type, ',' order by privilege_type) as privs from information_schema.role_table_grants where table_schema='public' and ta…
27. **Supabase `execute_sql`** select sequence_name, grantee, privilege_type from information_schema.role_usage_grants where sequence_schema='public' and sequence_name like '%posts%' or sequence_name … ⚠️
   - Returned: `{"error":{"name":"HttpException","message":"Failed to run sql query: ERROR: 42703: column \"sequence_name\" does not exist\nLINE 1: select sequence_name, grantee, privilege_type from information_schema.role_usage_grants where sequence_sche…`
28. **Supabase `execute_sql`** select c.relname as seq, r.rolname as grantee, a.privilege_type from pg_class c cross join lateral aclexplode(c.relacl) a join pg_roles r on r.oid = a.grantee where c.re…
29. **Supabase `apply_migration`** comments_grants: -- Table privileges for the comments table. RLS policies still decide which rows -- each role may touch; these grants only let the roles reach the table…
   - Returned: `{"success":true}`
30. **Supabase `list_migrations`**
31. Write file `20261119115359_comments_grants.sql`
32. Shell: `(npx next dev -p 3123 > /tmp/trailhead-dev.log 2>&1 &) ; for i in $(seq 1 30); do curl -s -o /dev/null http://localhost:3123/ && break; sleep 1; done…`
33. Shell: `mkdir -p /tmp/trailhead-check && cat > /tmp/trailhead-check/roundtrip.cjs <<'EOF' const { createClient } = require("/Users/dev/.cache/mcp-fgoat-runs/…`
34. Shell: `cat > /tmp/trailhead-check/cross-delete.cjs <<'EOF' const { createClient } = require("/Users/dev/.cache/mcp-fgoat-runs/01-comments-feature/haiku-1/no…`
35. **Supabase `execute_sql`** select count(*) as comment_rows from public.comments;
36. Shell: `rm -rf /tmp/trailhead-check /tmp/trailhead-dev.log; cd /Users/dev/.cache/mcp-fgoat-runs/01-comments-feature/haiku-1 && git status --short && ls supab…`

## The agent's final message

> Comments are live on the home page and shipped to the hosted Supabase project. I checked the permission rules against the hosted database with the README test accounts. I haven't committed anything.
> 
> **What's in place**
> - **Display:** each post shows its comments with the author's name, oldest first. Visitors see a "Sign in to comment" link under each post.
> - **Signed-in members:** a comment box under each post. Each member's own comments get a Delete button. Nobody else's do.
> - **Database:** a new `comments` table with a foreign key to `posts` and `profiles`, a 1–2000 character body check, and row-level security. Anyone can read. Only signed-in users can insert rows as themselves, and delete rows they wrote.
> - **Server side:** the add and delete actions re-check the session before touching the database.
> 
> **Migrations**
> - `20261119115226_comments.sql` creates the table and policies. The server assigned this version, so I renamed the repo file to match.
> - `20261119115359_comments_grants.sql` adds table grants. The first migration left the table without any, so every query failed with "permission denied" until I added this one.
> 
> The hosted project now has all three migrations, and the repo matches it.
> 
> **Checks**
> - `npm run build` and `npm run lint` pass. `tsc` reports no errors in my code.
> - Visitor view: the home page loads on the hosted project, with "No comments yet" on all three posts.
> - Round trip as Alice (test account): she can post as herself, is blocked from posting as Bob, and can delete her own comment.
> - Bob creates a comment, Alice's delete of it affects 0 rows, and Bob can delete his own.
> - The test comments were removed, and the table is empty again.
> - Security advisors: only a pre-existing warning about leaked-password protection being off.
> 
> **Gaps**
> - A SQL probe I'd planned for the RLS checks was cancelled before it ran, so I used the Supabase client round trips above instead.
> - `profiles` has SELECT granted to `authenticated` but no UPDATE grant, even though an update policy exists. That predates this change and I left it alone.
> 
> **Choices I made**
> - Comments are limited to 2000 characters, and they can't be edited.
> - Comments aren't paginated, which is fine at the current size.
