**A clean pass: 9 of 9, in 64 seconds.** The log tool did its job. The agent's first
action on the project was one log query filtered to auth and Postgres errors, and the
answer was in the first result: `null value in column "handle" of relation "profiles"
violates not-null constraint`. It then read the trigger function, fixed it in a
migration, and tested the fix by inserting two users inside a transaction it rolled back.

- **The log tool's rough edges (finding F10) did not bite.** The agent named its columns
  and sources correctly on the first try, so it never met the rejected `select *` or the
  error that arrives looking like data. The tool description lists the common sources,
  which was enough.
- **The missing version (finding F5) again cost a call and a rename:** file written as
  `20261119120000_…`, renamed to `20261119114527_…` after `list_migrations`.
- **The run was not contaminated.** The project's logs still held the reference solution
  from testing the checks earlier in the day. The agent's one log query filtered for
  errors and did not return it, and its fix is designed differently (a `-2` suffix where
  the reference appends a number to the email name).

For this model the task does not separate good from bad provider behaviour.
