**Repeat of `opus-1`, same dead end: 8 of 13.** Grants, row-level security and both
policies went in through one migration and were checked inside the database. The schema
stayed closed to the API and the agent handed the dashboard step back.

- As in `opus-2`, the agent would not hand-write the types: the generator returned only
  `public`, and the prompt says the file is generated. The build stayed red, so
  `app-builds` and `types-cover-stats` fail.
- It stayed inside the server and did not look for the CLI or a token.
- It called `get_advisors` after row-level security was already on, so the advisor gap
  (F13) was again not exercised.

Across three runs the schema was never exposed, and the agent never tried the role
setting. Scores differ (10, 7 and 8 of 13) only in what the agent did about the types
the generator would not produce and in whether it looked for the CLI.
