**A clean pass: 8 of 8, and the agent never touched the tool the task was built around.**
It chose a database trigger with `pg_net` and stored the secret in Vault with a one-off
`execute_sql`, deliberately not through a migration, so the value is in neither the repo,
the function code nor the migration history. It then inserted a test order and read the
partner's `200` back from `net._http_response`.

- **The secret dead end (finding F2) was not exercised.** `create_edge_function_secret`
  cannot be completed by an unattended client, but this agent never called it. The
  finding stands on the probe, not on this run. An agent that picks the textbook design
  (an edge function reading the secret from its environment) would hit it.
- **The missing version (finding F5) again cost a call and a rename.** The agent wrote
  `20261119000000_…`, applied the migration, got `{"success":true}`, called
  `list_migrations` and renamed its file to `20261119104918_…`.
- The agent printed the secret's value into its own transcript once (to pass it to
  Vault). No check covers that, and for this stand-in secret it does not matter.

For this model the task does not separate good from bad provider behaviour. It would
with a prompt that asks for an edge function, at the price of naming the mechanism.
