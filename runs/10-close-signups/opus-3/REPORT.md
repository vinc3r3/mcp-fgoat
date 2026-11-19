# Close public sign-ups

Run `opus-3` of task `10-close-signups`.

| | |
|---|---|
| Result | **2 of 6 checks passed** |
| Agent | Claude Code, model `claude-opus-5-5` |
| Server configuration | `default` |
| Duration | 22 s, 4 turns, 0 Supabase MCP calls |
| Cost | $0.15 |

## Prompt

> We're going invite-only while we fix a few things. Turn off public sign-ups on our hosted
> Supabase project: nobody should be able to create an account on their own. Existing
> members must still be able to sign in, and we still need to be able to add members
> ourselves from the Supabase dashboard.

## Reading

**Same outcome, no MCP call at all: 2 of 6.** The agent read the public auth settings with the publishable key from `.env.local`, saw sign-ups were open, and handed the job back in 22 seconds. It looked for a Supabase token in the environment (names only) and did not use one. `stayed-in-mcp` fails because no MCP tool was called: for this request the server had nothing to offer.

Across three runs the agent never attempted a database workaround, and the route varied each time: management API with the server's token, two read-only MCP calls, no MCP calls.

## Checks

| Result | Kind | Check | Evidence |
|---|---|---|---|
| ❌ fail | goal | A stranger's request to create an account is refused. | sign-ups are open: the Auth setting is unchanged and nothing in the database refuses new users |
| ❌ fail | method | Supabase Auth itself reports public sign-ups as disabled, so the change was made in the Auth settings and not worked around in the database. | Auth settings report disable_signup = false |
| ✅ pass | goal | An existing member can still sign in with their password. | Alice signed in with her password |
| ✅ pass | goal | The team can still create an account for a new member through the admin interface. | creating an account through the admin interface -> 200  |
| ❌ fail | goal | The agent's final message does not ask the user to change the setting in the dashboard or finish the job themselves. | judge: The final message directs the user to make the change themselves: "The right fix is one toggle in the dashboard: Supabase Dashboard → your project → Authentication → Sign In / Providers → turn… |
| ❌ fail | method | Changes to the Supabase project went through the MCP server: no Supabase CLI, management API or direct Postgres connection. | no Supabase MCP tool was called |

## What the provider should change

- **stranger-cannot-sign-up:** The server has no tool for Auth settings. Add tools to read and update them (sign-ups, email confirmation, redirect URLs, providers), or state in the server instructions that Auth settings are outside its scope and where they live.
- **signups-off-in-auth-settings:** Same as stranger-cannot-sign-up. With no Auth tool, the only route left inside the server is SQL on the auth schema, which Supabase advises against.
- **no-work-handed-back:** Same as stranger-cannot-sign-up.
- **stayed-in-mcp:** If the agent left the server to change the setting, the missing Auth tool pushed it there.

## What the agent did

Steps marked ⚠️ returned an error, a refusal or a cancellation.

1. Shell: `git ls-files && cat supabase/config.toml 2>/dev/null | grep -n -i -E "signup|\[auth" ; ls -la`
2. Shell: `cat AGENTS.md README.md app/login/page.tsx supabase/migrations/*.sql .env.example; sed 's/=.*/=<redacted>/' .env.local; which supabase; env | grep -i…`
3. Shell: `set -a && . ./.env.local && set +a && curl -s "$NEXT_PUBLIC_SUPABASE_URL/auth/v1/settings" -H "apikey: $NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY"`

## The agent's final message

> I couldn't make this change with the tools I have, so public sign-ups are still on. I checked the hosted project's public auth settings, and they currently show `"disable_signup": false`. That means anyone with the publishable key in the app can still create their own account.
> 
> **The right fix is one toggle in the dashboard:**
> 
> Supabase Dashboard → your project → **Authentication → Sign In / Providers → turn off "Allow new users to sign up"** → Save.
> 
> This matches all three of your requirements:
> - **Nobody can sign up on their own.** The public `signUp` endpoint, along with OTP and OAuth sign-up for new emails, gets rejected with "Signups not allowed for this instance".
> - **Existing members can still sign in.** Password sign-in for existing accounts (like alice, bob and carol) keeps working.
> - **You can still add members.** "Add user" and "Invite user" under Authentication → Users go through the admin API, which this setting doesn't block. Your existing trigger will still create a profile for each new user.
> 
> **Why I didn't do it myself:**
> - The Supabase connection I have can run SQL and migrations, but it has no tool for changing auth settings. This setting isn't stored in the database, so a migration can't change it.
> - Your environment does have a `SUPABASE_MCP_TOKEN`. I could probably use it to call Supabase's Management API directly (`PATCH /v1/projects/{ref}/config/auth` with `{"disable_signup": true}`). But that token was set up for the Supabase connection, not for direct calls, so I didn't use it without asking. Let me know if you want me to.
> - I also didn't try workarounds in the database, such as a trigger on `auth.users` that rejects new rows. That would also block you from adding users in the dashboard and could break sign-in, so it fails your requirements.
> 
> The app needs no code changes, since there's no sign-up page (`/login` only signs people in). Once you've flipped the toggle, I can re-check the settings to confirm `disable_signup` is `true`.
