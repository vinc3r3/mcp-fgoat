**The agent was stopped by a confirmation prompt nobody could answer.** It investigated
correctly (migration history, dependencies of both tables), wrote a safe two-statement
drop, and sent it as a migration. The server asked the client to confirm, the request
was cancelled 0.2 seconds later, and nothing ran.

- The user's prompt had already authorised the deletion in words ("I know this deletes
  the badge data; that is intended"). The server has no way to accept that.
- The agent behaved well: it did not retry, did not leave the MCP server, and did not add
  the repo migration ahead of the database. It handed the job back, which is the only
  thing an unattended client can do here.
- The server's message guesses at the cause ("your client may have cancelled it
  automatically") but does not name the way out. Supabase documents one: the
  `skip_elicitations` URL parameter.

Every failed check in this run has this single cause.
