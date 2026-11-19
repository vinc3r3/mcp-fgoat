**Same task, smaller model, same trap, same rescue: 10 of 11.** Haiku on the hardened
task behaved almost exactly like Opus on it.

- **It shipped the table without grants**, got `{"success":true}`, and learned of the
  problem only when it loaded the home page in a dev server and saw
  `Could not load comments: permission denied for table comments`. It then shipped a
  `comments_grants` migration.
- **It also hit the confirmation prompt, on a test.** To verify its policies it sent a
  `do $$ … $$` block through `execute_sql` that impersonated the two test members. The
  server asked for confirmation and the request was cancelled after 0.2 seconds
  (finding F1). The agent switched to testing through the public API. So the prompt is
  not limited to `drop` statements: an anonymous code block used for verification
  triggers it too.
- **The missing version (finding F5):** it wrote `20261119120000_comments.sql`, applied,
  called `list_migrations` and renamed the file to `20261119115226_…`.

37 turns and 16 Supabase MCP calls, against 22 turns and 7 calls for Opus on the
original template. The provider-side gaps show up as extra work on both models.
