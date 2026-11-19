**The grant trap sprang, and the agent's own testing rescued it: 10 of 11.** This is the
hardened version of the task: the repo's baseline migration no longer shows any `grant`
statement. Compare `opus-1`, same model on the original template, 11 of 11.

- **The agent shipped a table nobody could reach.** Its first migration created
  `comments` with row-level security and three policies and no grants.
  `apply_migration` returned `{"success":true}`. It then called `get_advisors`, which
  reported nothing about the new table.
- **It found out only because it tested from outside.** A script signed in with the test
  accounts and got `permission denied for table comments`. The agent then compared
  grants across tables, understood the project does not grant new tables automatically,
  and shipped a second migration, `comments_grants`. Production was broken for the
  minutes in between.
- **What it cost:** 32 turns, 159 seconds and $0.66, against 22 turns, 110 seconds and
  $0.49 for the same model when the repo showed the pattern. Two migrations where one
  would do.

Two places in the server could have said "this table is not reachable through the API":
the migration result and the advisor. Neither did. An agent that does not test from
outside would have finished with a broken feature and a success message.

The check `reachable-from-first-migration` was added after reading this transcript and
the Haiku run of the same task; earlier results for this task were regraded with it.
