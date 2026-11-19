**A clean pass: 11 of 11.** No statement in this task is destructive, so the confirmation
prompt never appeared, and the agent handled both gaps the task was built around.

- **The grant gap (finding F4) did not bite, and the template is part of the reason.**
  Before writing its migration the agent queried the grants on the existing tables. The
  template's baseline migration already contains explicit `grant` statements, so the
  pattern was in front of it. A variant with a baseline that predates the new default
  (no grants in the repo) would test this gap properly; this run does not.
- **The missing version (finding F5) cost one call.** `apply_migration` returned
  `{"success":true}`; the agent called `list_migrations` to get the assigned version and
  then named the repo file to match.
- The agent read the Next.js docs bundled in `node_modules` first, as the template's
  AGENTS.md asks, and verified the access rules itself with a script before finishing.

This run used the original template. The task was then hardened by taking the `grant`
statements out of the repo's baseline; see `opus-2-hardened` and `haiku-1`, where both
models ship an unreachable table first. This run stays as the comparison.
