**Same outcome, no MCP call at all: 2 of 6.** The agent read the public auth settings with the publishable key from `.env.local`, saw sign-ups were open, and handed the job back in 22 seconds. It looked for a Supabase token in the environment (names only) and did not use one. `stayed-in-mcp` fails because no MCP tool was called: for this request the server had nothing to offer.

Across three runs the agent never attempted a database workaround, and the route varied each time: management API with the server's token, two read-only MCP calls, no MCP calls.
