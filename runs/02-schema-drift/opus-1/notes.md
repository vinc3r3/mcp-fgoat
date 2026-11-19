**The agent reconciled everything, and to do it had to edit Supabase's internal
migration history by hand.** Production data is intact, the pending migration is applied,
history and repo match file for file, and a database rebuilt from the repo matches
production. The one failed check is the method.

- **`apply_migration` could not do the job, so the agent went around it.** It needed to
  record two migrations under versions that match the repo's file names, one of them
  without running it (the dashboard changes already existed). `apply_migration` assigns
  its own version and always executes. The agent instead ran one `execute_sql`
  transaction that applied the slug change and inserted both rows straight into
  `supabase_migrations.schema_migrations`. It worked, but it is an agent writing to an
  internal table, with no guard and no tool designed for it.
- **No way to read the schema back as SQL.** To write the missing migration the agent
  assembled it from five catalog queries (columns, indexes, constraints, policies,
  grants). To prove the rebuild it started a throwaway local Postgres 16, created
  stand-ins for Supabase's roles and `auth` schema, replayed the repo and diffed a
  schema fingerprint against production. A schema dump or diff tool on the server would
  replace all of that.
- No confirmation prompt appeared: nothing in the task is destructive.

About the checks: `history-not-hand-edited` was added after reading this transcript,
because the run reached the goal by a route the task had not anticipated. The first
grading also flagged `stayed-in-mcp` because the agent ran `psql` against its local
database; the check now only counts connections to the hosted project.
