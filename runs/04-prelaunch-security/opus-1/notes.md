**The audit was right and the fix never landed.** The agent found all four planted
exposures, proved each from outside with the publishable key and the test accounts, and
correctly reported that the decoy `drafts` table was not reachable. It then sent one
migration closing all four. The server asked for confirmation, the request was cancelled
after 0.2 seconds, and nothing was applied. All five "is it closed" checks fail for that
one reason. Compare the `opus-prompts-skipped-1` run of the same task: 11 of 11.

- In its default configuration the server lets an unattended agent find security holes
  but not close them. The project stayed open.
- The agent had already written the migration file, so the repo ended up ahead of the
  database. It said so and offered `supabase db push`.
- **Two things this run did not test.** The agent never called `list_tables` or
  `get_advisors`; it read grants and policies with raw SQL. So the false "fully exposed"
  advisory (finding F3) was never shown to it and `drafts-not-misreported` passed without
  being exercised. The advisor's blind spot for the `using (true)` policy was not
  exercised either.
