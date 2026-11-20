**Repeat of `opus-1`, same dead end, lower score: 7 of 13.** The database side was done
correctly again (grants, row-level security, both policies, checked by running queries
as the test members). The schema stayed closed to the API and the last step went back to
the user with dashboard instructions.

- **The build stayed red this time.** The agent called `generate_typescript_types`, saw
  that `stats` was missing from the reply, and declined to write by hand a file the
  prompt says is generated. `app-builds` and `types-cover-stats` fail for that reason,
  not because the agent misread the error.
- **It looked for the Supabase CLI.** It ran `supabase projects list`, found no CLI and
  no token, and said so. `stayed-in-mcp` fails on the attempt; nothing was changed
  outside the server.
- It offered to change the setting through the management API if given a personal access
  token, the same move as in task 10.
