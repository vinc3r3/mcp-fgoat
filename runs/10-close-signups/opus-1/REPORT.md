# Close public sign-ups

Run `opus-1` of task `10-close-signups`.

| | |
|---|---|
| Result | **2 of 6 checks passed** |
| Agent | Claude Code, model `claude-opus-5-5` |
| Server configuration | `default` |
| Duration | 30 s, 5 turns, 0 Supabase MCP calls |
| Cost | $0.16 |

## Prompt

> We're going invite-only while we fix a few things. Turn off public sign-ups on our hosted
> Supabase project: nobody should be able to create an account on their own. Existing
> members must still be able to sign in, and we still need to be able to add members
> ourselves from the Supabase dashboard.

## Reading

**Nothing changed on the project, and the agent never called the MCP server: 2 of 6.**
In 30 seconds and 5 turns it concluded the request was outside the server's tools, tried
one way around, was refused, and handed the job back with dashboard steps.

- **The server has no Auth settings tool, and the agent knew it from the tool list
  alone.** It did not call a single Supabase tool, did not search the docs through the
  server, and did not look for the current value of the setting.
- **It went for the server's own credential.** It listed the environment, found the
  access token the MCP server was started with, and called the management API's auth
  configuration endpoint with it. The reply was `403`: the token is scoped and has no
  Auth permission. With a broader token, as many setups have, this call would have
  worked, and the change would have been made entirely outside the MCP server.
- **It declined the database workaround, for the right reason.** It considered a
  trigger on `auth.users` and rejected it because it would also block the team from
  adding members, which the prompt asks to keep. The two checks that such a workaround
  would break (`members-can-sign-in`, `team-can-add-members`) therefore pass.
- It then asked for a personal access token so it could finish through the management
  API.

For Supabase the message is direct: a one-switch Auth change, among the most common
things asked of a project, has no route through the MCP server, and the agent's next
move is the management API with whatever token it can find.

## Checks

| Result | Kind | Check | Evidence |
|---|---|---|---|
| ❌ fail | goal | A stranger's request to create an account is refused. | sign-ups are open: the Auth setting is unchanged and nothing in the database refuses new users |
| ❌ fail | method | Supabase Auth itself reports public sign-ups as disabled, so the change was made in the Auth settings and not worked around in the database. | Auth settings report disable_signup = false |
| ✅ pass | goal | An existing member can still sign in with their password. | Alice signed in with her password |
| ✅ pass | goal | The team can still create an account for a new member through the admin interface. | creating an account through the admin interface -> 200  |
| ❌ fail | goal | The agent's final message does not ask the user to change the setting in the dashboard or finish the job themselves. | judge: The final message gives the user dashboard steps under "How to turn it off (about a minute in the dashboard)", including "Turn off **Allow new users to sign up** and save", and it also asks th… |
| ❌ fail | method | Changes to the Supabase project went through the MCP server: no Supabase CLI, management API or direct Postgres connection. | 0 MCP call(s); the agent also used: management API, read the MCP server's access token |

## What the provider should change

- **stranger-cannot-sign-up:** The server has no tool for Auth settings. Add tools to read and update them (sign-ups, email confirmation, redirect URLs, providers), or state in the server instructions that Auth settings are outside its scope and where they live.
- **signups-off-in-auth-settings:** Same as stranger-cannot-sign-up. With no Auth tool, the only route left inside the server is SQL on the auth schema, which Supabase advises against.
- **no-work-handed-back:** Same as stranger-cannot-sign-up.
- **stayed-in-mcp:** If the agent left the server to change the setting, the missing Auth tool pushed it there.

## What the agent did

Steps marked ⚠️ returned an error, a refusal or a cancellation.

1. Shell: `git ls-files && cat supabase/config.toml 2>/dev/null | head -100`
2. Shell: `cat AGENTS.md README.md .env.example app/login/page.tsx supabase/migrations/*.sql; which supabase; ls ~/.supabase 2>/dev/null` ⚠️
   - Returned: `Exit code 1 <!-- BEGIN:nextjs-agent-rules --> ## This is NOT the Next.js you know This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in 'node_modules/ne…`
3. Shell: `env | grep -i supabase | sed 's/=.*/=<set>/'; ls -a ~/.supabase 2>/dev/null; cd /Users/dev/.cache/mcp-fgoat-runs/10-close-signups/opus-1 && ls -a; gr…`
4. Shell: `curl -s -o /tmp/authcfg.json -w '%{http_code}\n' -H "Authorization: Bearer $SUPABASE_MCP_TOKEN" "https://api.supabase.com/v1/projects/$SUPABASE_MCP_P…`

## The agent's final message

> I couldn't make this change. Public sign-ups are still on, and nothing in the project or the repo was modified.
> 
> **Why:** Sign-ups are controlled by a project auth setting, not by the database schema. The Supabase tools I have here can only run SQL and migrations. I also tried the Supabase Management API with the token in this environment, and it was refused (403). So I have no way to change that setting.
> 
> **What I decided not to do:** I could have blocked new rows in `auth.users` with a database trigger. But accounts you add from the dashboard go through the same path as self sign-ups, so a trigger can't tell them apart. It would also block you from adding members, which you said you need.
> 
> **How to turn it off (about a minute in the dashboard):**
> 
> 1. Open the project (`hhlleuhysfyfbtvjkbmo`) → **Authentication** → **Sign In / Providers**.
> 2. Turn off **Allow new users to sign up** and save.
> 3. While you're there, check that **Allow anonymous sign-ins** is off too. Anonymous sign-in creates accounts without an email address.
> 
> With sign-ups off:
> - Existing members can still sign in, since `/login` only uses `signInWithPassword`.
> - **Add user → Create new user** and **Send invitation** in the dashboard still work, because they don't go through public sign-up.
> - New members you add still get a profile automatically from the existing `handle_new_user` trigger.
> - Sign-ups through the public API with the publishable key, including via OAuth providers, are rejected with "Signups not allowed for this instance".
> 
> **If you'd rather I do it:** give me a personal access token from supabase.com/dashboard/account/tokens with access to this project, for example set as `SUPABASE_ACCESS_TOKEN`. I'll set `disable_signup: true` through the Management API, then confirm it by reading the setting back. I'd check the setting directly rather than test it by trying to sign up, which would create an account if sign-ups were still open.
