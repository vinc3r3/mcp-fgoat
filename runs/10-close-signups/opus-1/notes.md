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
