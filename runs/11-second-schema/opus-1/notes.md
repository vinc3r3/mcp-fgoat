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
