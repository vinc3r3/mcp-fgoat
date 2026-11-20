**Same task, same model, prompts skipped: 6 of 6.** The agent took the same route as in
the three default runs (migration history, a dependency query, one two-statement drop
sent as a migration). This time the server ran it and returned `{"success":true}`.

- The only difference from `opus-1`, `opus-2` and `opus-3` is the server's
  `skip_elicitations` setting. Those runs stopped at the cancelled confirmation with 2 of
  6; nothing in the agent's work had to change for this one to pass.
- After the migration the agent called `list_migrations` to learn the version the server
  had assigned, then wrote the repo file under that version. `apply_migration` does not
  return it.
