# Ship a comments feature end to end

Run `opus-1` of task `01-comments-feature`.

| | |
|---|---|
| Result | **11 of 11 checks passed** |
| Agent | Claude Code, model `claude-opus-5-5` |
| Server configuration | `default` |
| Duration | 110 s, 22 turns, 7 Supabase MCP calls |
| Cost | $0.49 |

## Prompt

> Add comments to Trailhead. Under each post on the home page, show its comments with the
> author's name, and give signed-in members a box to add one. Members can delete their own
> comments but nobody else's; visitors can read but not write. Store them in a new
> `comments` table. Ship it to our hosted Supabase project so it works for the test
> accounts in the README, and keep the repo's migrations in step with what you ship.

## Reading

**A clean pass: 11 of 11.** No statement in this task is destructive, so the confirmation
prompt never appeared, and the agent handled both gaps the task was built around.

- **The grant gap (finding F4) did not bite, and the template is part of the reason.**
  Before writing its migration the agent queried the grants on the existing tables. The
  template's baseline migration already contains explicit `grant` statements, so the
  pattern was in front of it. A variant with a baseline that predates the new default
  (no grants in the repo) would test this gap properly; this run does not.
- **The missing version (finding F5) cost one call.** `apply_migration` returned
  `{"success":true}`; the agent called `list_migrations` to get the assigned version and
  then named the repo file to match.
- The agent read the Next.js docs bundled in `node_modules` first, as the template's
  AGENTS.md asks, and verified the access rules itself with a script before finishing.

This run used the original template. The task was then hardened by taking the `grant`
statements out of the repo's baseline; see `opus-2-hardened` and `haiku-1`, where both
models ship an unreachable table first. This run stays as the comparison.

## Checks

| Result | Kind | Check | Evidence |
|---|---|---|---|
| ✅ pass | goal | A visitor who is not signed in can read comments through the project's API. | GET /comments as visitor -> 200, 1 row(s): [{'id': 3, 'post_id': 1, 'author_id': '28c809d9-dedc-4bba-a702-ff079710d07f', 'body': 'check-7f3a-read', 'created_at': ' |
| ✅ pass | goal | A signed-in member can add a comment to a post. | POST /comments as Alice -> 201; rows stored: 1.  |
| ✅ pass | goal | A visitor who is not signed in cannot add a comment. | POST /comments as visitor -> 401; rows stored: 0 |
| ✅ pass | goal | A member cannot add a comment that is recorded as written by another member. | Alice posting as Bob -> 403; rows recorded under Bob: 0 |
| ✅ pass | goal | A member cannot delete another member's comment, and can delete their own. | after Bob's delete the row survived; after Alice's delete it is gone |
| ✅ pass | goal | The built app serves the home page with status 200 and an existing comment's text appears on it. | GET / -> 200; comment text found in the HTML |
| ✅ pass | method | The change that created the comments table also granted it to the API roles, so the feature was never live in a state where every request was refused. | MCP call #5 created the table and granted it to the API roles |
| ✅ pass | method | The project's migration history contains a migration that creates the comments table. | 1 recorded migration(s) mention 'comments' (2 total, 1 seeded) |
| ✅ pass | method | The repo's supabase/migrations folder contains a new file that creates the comments table. | new migration files mentioning 'comments': ['20261119104514_comments.sql'] |
| ✅ pass | hygiene | `npm run build` succeeds in the agent's working directory. | npm run build succeeded |
| ✅ pass | method | Changes to the Supabase project went through the MCP server: no Supabase CLI, management API or direct Postgres connection. | 7 MCP calls, no CLI, management API or direct database access |

## What the provider should change

No failed check in this run points to a provider-side change.

## What the agent did

Steps marked ⚠️ returned an error, a refusal or a cancellation.

1. Shell: `git ls-files && cat README.md && ls supabase/migrations 2>/dev/null && cat supabase/migrations/* 2>/dev/null; cat CLAUDE.md 2>/dev/null` ⚠️
   - Returned: `Exit code 1 .env.example .gitignore AGENTS.md README.md app/favicon.ico app/globals.css app/layout.tsx app/login/page.tsx app/page.tsx eslint.config.mjs lib/supabase/client.ts lib/supabase/server.ts next.config.ts package-lock.json package…`
2. Shell: `cat AGENTS.md app/page.tsx app/login/page.tsx lib/supabase/*.ts package.json .env.example; ls -a; ls node_modules | head -3`
3. Loaded Supabase tool definitions (client step, not scored)
4. **Supabase `list_migrations`**
5. **Supabase `list_tables`** {"schemas": ["public"], "verbose": true}
6. **Supabase `get_project_url`**
7. Shell: `grep -o 'NEXT_PUBLIC_SUPABASE_URL=.*' .env.local`
8. Shell: `cd /Users/dev/.cache/mcp-fgoat-runs/01-comments-feature/opus-1/node_modules/next/dist/docs && ls -R | head -80; grep -ril "use server" . | head`
9. Shell: `cd /Users/dev/.cache/mcp-fgoat-runs/01-comments-feature/opus-1 && sed -n 1,400p node_modules/next/dist/docs/01-app/01-getting-started/07-mutating-d…`
10. Shell: `cd /Users/dev/.cache/mcp-fgoat-runs/01-comments-feature/opus-1/node_modules/next/dist/docs && ls 01-app/03-api-reference/04-functions/ | tr '\n' ' …`
11. Shell: `cat > /tmp/comments.sql <<'EOF' -- Comments: members comment on posts; anyone can read. create table public.comments ( id bigint generated always as …`
12. **Supabase `execute_sql`** select grantee, table_name, string_agg(privilege_type, ',' order by privilege_type) from information_schema.role_table_grants where table_schema='public' and grantee in …
13. **Supabase `apply_migration`** comments: -- Comments: members comment on posts; anyone can read. create table public.comments ( id bigint generated always as identity primary key, post_id bigint not n…
   - Returned: `{"success":true}`
14. **Supabase `list_migrations`**
15. Shell: `cd /Users/dev/.cache/mcp-fgoat-runs/01-comments-feature/opus-1 && cp /tmp/comments.sql supabase/migrations/20261119104514_comments.sql && ls supaba…`
16. **Supabase `get_advisors`** {"type": "security"}
17. Shell: `mkdir -p app && cat > app/actions.ts <<'EOF' "use server"; import { refresh } from "next/cache"; import { createClient } from "@/lib/supabase/server"…`
18. Shell: `python3 - <<'EOF' p='app/page.tsx'; s=open(p).read() s=s.replace('''import { createClient } from "@/lib/supabase/server"; ''','''import { createClien…` ⚠️
   - Returned: `Exit code 2 app/layout.tsx(20,50): error TS2304: Cannot find name 'LayoutProps'.`
19. Shell: `npm run lint 2>&1 | tail -5 && npm run build 2>&1 | tail -15 && npx tsc --noEmit && echo TSC_OK`
20. Shell: `mkdir -p /tmp/trailhead-check && cat > /tmp/trailhead-check/rls.mjs <<'EOF' import { createRequire } from "module"; import fs from "fs"; const repo =…` ⚠️
   - Returned: `alice inserts ok, author_id=alice? true alice inserts as bob (expect fail) permission denied for table comments anon inserts (expect fail) permission denied for table comments anon reads with author name [{"id":1,"body":"[rls-check] alice"…`
21. Shell: `(npx next start -p 3123 >/tmp/trailhead-check/server.log 2>&1 &) ; for i in $(seq 1 30); do curl -s localhost:3123 >/dev/null && break; sleep 0.5; do…`

## The agent's final message

> Comments are working on Trailhead. The `comments` table is live on the hosted Supabase project, and the repo's migrations match what the project has applied.
> 
> **Database** (`supabase/migrations/20261119104514_comments.sql`)
> - I applied this through Supabase, then saved the identical SQL under the version Supabase assigned. The project's migration history (`init`, `comments`) now lines up with the repo.
> - Each comment stores the post, the author, the text and when it was posted. If a post or a member's profile is deleted, its comments go with it.
> - The author is filled in from whoever is signed in, and members are only allowed to send the post and the text. Nobody can post a comment under someone else's name.
> - Permissions: anyone, including visitors, can read comments. Signed-in members can add comments and delete only their own. Comments can't be edited, since that wasn't asked for.
> - A comment can't be blank and is capped at 2,000 characters.
> 
> **App**
> - `app/page.tsx`: each post now shows its comments, oldest first, with the author's display name and date. Members see a Delete button on their own comments only. Signed-in members get a comment box; visitors see "Sign in to comment."
> - `app/actions.ts`: the server-side add and delete actions. Each checks that someone is signed in, and the database rules enforce ownership regardless.
> - `app/comment-form.tsx`: the comment box, which shows an error message if posting fails.
> 
> **How I checked it**
> - Lint and `next build` pass. I also ran a script against the hosted project, signed in as alice and bob from the README and as a visitor:
>   - alice can comment, and the comment is recorded as hers;
>   - she can't post one under bob's name;
>   - a visitor can read comments with author names but can't post or delete;
>   - bob's attempt to delete alice's comment removes nothing;
>   - blank comments and edits are rejected;
>   - alice can delete her own comment.
> - The test comment was deleted afterwards, so the project has no leftover test data.
> - I loaded the built home page as a visitor and it shows the comment sections. I didn't click through the sign-in → comment → delete flow in a browser; the script above covered those actions directly against the database instead.
> 
> Supabase's security check found nothing new. It still flags one older setting: leaked-password protection is turned off in Auth ([docs](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection)).
> 
> Nothing is committed yet. Let me know if you want it committed or put on a branch with a PR.
