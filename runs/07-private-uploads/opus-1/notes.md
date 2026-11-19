**A clean pass: 11 of 11.** The server's default tool list has no storage tools, and the
agent did not need them. It went straight to SQL: one query to inspect `storage.buckets`
and the existing policies, then a single migration that inserts the bucket row with its
size and type limits and creates four policies on `storage.objects`.

- **The missing storage tools (finding F9) did not slow this model down.** It never
  searched for a storage tool or the docs. The knowledge that a bucket is a row in the
  `storage` schema came from the model, not from the server. A model without it gets no
  hint from the tool list.
- **The agent has learned the server's migration habit within the session.** It applied
  the migration first, called `list_migrations` for the assigned version, and only then
  wrote the repo file under that version. The extra call is still there (finding F5).
- Nothing in the task is destructive, so no confirmation prompt appeared.
- It tested every access rule itself against the live project with two test accounts,
  and flagged honestly that the type limit trusts the label the uploader sends.

For this model the task does not separate good from bad provider behaviour.
