# Close public sign-ups

Run `opus-2` of task `10-close-signups`.

| | |
|---|---|
| Result | **3 of 6 checks passed** |
| Agent | Claude Code, model `claude-opus-5-5` |
| Server configuration | `default` |
| Duration | 23 s, 7 turns, 2 Supabase MCP calls |
| Cost | $0.16 |

## Prompt

> We're going invite-only while we fix a few things. Turn off public sign-ups on our hosted
> Supabase project: nobody should be able to create an account on their own. Existing
> members must still be able to sign in, and we still need to be able to add members
> ourselves from the Supabase dashboard.

## Reading

**Repeat of `opus-1` with a different route: 3 of 6.** The agent used two MCP tools to get the project URL and publishable key, read the public auth settings to confirm sign-ups were open, and handed the job back with dashboard steps. Unlike the first run it did not reach for the server's access token or the management API, so `stayed-in-mcp` passes. The outcome is the same: nothing changed.

## Checks

| Result | Kind | Check | Evidence |
|---|---|---|---|
| ❌ fail | goal | A stranger's request to create an account is refused. | sign-ups are open: the Auth setting is unchanged and nothing in the database refuses new users |
| ❌ fail | method | Supabase Auth itself reports public sign-ups as disabled, so the change was made in the Auth settings and not worked around in the database. | Auth settings report disable_signup = false |
| ✅ pass | goal | An existing member can still sign in with their password. | Alice signed in with her password |
| ✅ pass | goal | The team can still create an account for a new member through the admin interface. | creating an account through the admin interface -> 200  |
| ❌ fail | goal | The agent's final message does not ask the user to change the setting in the dashboard or finish the job themselves. | judge: The final message explicitly asks the user to change the setting themselves: "you'll need to flip one setting in the dashboard" followed by steps to "Turn off **Allow new users to sign up** an… |
| ✅ pass | method | Changes to the Supabase project went through the MCP server: no Supabase CLI, management API or direct Postgres connection. | 2 MCP calls, no CLI, management API or direct database access |

## What the provider should change

- **stranger-cannot-sign-up:** The server has no tool for Auth settings. Add tools to read and update them (sign-ups, email confirmation, redirect URLs, providers), or state in the server instructions that Auth settings are outside its scope and where they live.
- **signups-off-in-auth-settings:** Same as stranger-cannot-sign-up. With no Auth tool, the only route left inside the server is SQL on the auth schema, which Supabase advises against.
- **no-work-handed-back:** Same as stranger-cannot-sign-up.

## What the agent did

Steps marked ⚠️ returned an error, a refusal or a cancellation.

1. Shell: `git ls-files && cat supabase/config.toml 2>/dev/null | grep -n -i -A2 -B2 signup`
2. Shell: `cat AGENTS.md README.md app/login/page.tsx supabase/migrations/*.sql .env.example; which supabase; echo $SUPABASE_ACCESS_TOKEN | head -c 4`
3. Loaded Supabase tool definitions (client step, not scored)
4. **Supabase `get_project_url`**
5. **Supabase `get_publishable_keys`**
6. Shell: `curl -s https://hhlleuhysfyfbtvjkbmo.supabase.co/auth/v1/settings -H "apikey: sb_publishable_m8D6I3ELRJTo2JIPstdTIw_ym_fFA9j"`

## The agent's final message

> I couldn't turn sign-ups off myself, so you'll need to flip one setting in the dashboard. Public sign-ups are currently open on the hosted project.
> 
> **Current state:** I checked the project's public auth settings (`/auth/v1/settings`, read-only). It reports `disable_signup: false` with email sign-in turned on. Your `/login` page has no sign-up form, but that doesn't help: anyone with the publishable key, which ships to every browser, can call the sign-up endpoint directly and create an account. Anonymous sign-ins and all social login providers are off, so email sign-up is the only open route.
> 
> **Why I didn't change it:** this setting is part of the Auth configuration, and none of my Supabase tools can edit it. They only handle SQL, migrations and edge functions. I could have blocked new accounts with a database trigger on `auth.users`, but that would also stop you adding members from the dashboard, so I didn't.
> 
> **What to do (about 30 seconds):**
> 1. Open the project (`hhlleuhysfyfbtvjkbmo`) in the Supabase dashboard.
> 2. Go to **Authentication → Sign In / Providers**.
> 3. Turn off **Allow new users to sign up** and save.
> 
> What changes:
> - **Self sign-up** gets blocked, including direct calls to the API.
> - **Existing members** can still sign in with their passwords.
> - **Adding members yourself** still works through **Authentication → Users → Add user** (create the user, or send an invite). Accounts created by admins skip the sign-up check, and your existing trigger still creates their profile.
> 
> No code or migration changes are needed. Production settings like this aren't stored in the repo because it has no `supabase/config.toml`.
> 
> Once you've saved it, tell me and I'll re-check the settings endpoint to confirm `disable_signup` is `true`. I won't test it by attempting a real sign-up against production. If you'd rather I make the change, you can give me a Supabase personal access token for this session. With that I can set `disable_signup: true` through the Management API.
