**A clean pass on the smaller model too: 11 of 11.** Like Opus, Haiku never looked for a
storage tool. It inspected `storage.buckets` and the existing policies with one query and
set up the bucket and four policies in a single migration.

- **The missing storage tools (finding F9) did not matter to this model either.**
- **The missing version (finding F5):** file written as `20261119120000_…`, renamed to
  `20261119115915_…` after `list_migrations`.
- It tested the access rules through the storage API with two test accounts.

This task does not separate Opus from Haiku.
