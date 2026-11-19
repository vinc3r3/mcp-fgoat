# Agent Experience evaluation: Supabase MCP server

A dataset of eight tasks and 67 checks that measures how well a coding agent, working on its own, can
understand and use Supabase through its MCP server. Seven runs were executed to confirm
the dataset works; their reports are in [`runs/`](runs/).

- **Provider:** Supabase, hosted MCP server 0.17.0 (`mcp.supabase.com`), scoped to one
  project on the free plan.
- **Agent under test:** Claude Code 2.1.328, headless, model `claude-opus-5-5`.
- **Dataset design:** done with a different model (Claude Fable 5.2) so the tasks are not
  tuned to the tested model's habits.

## What the runs found

| Task | Server configuration | Result | Report |
|---|---|---|---|
| 06 Remove a retired feature's tables | default | 2 of 6 | [report](runs/06-retire-feature/opus-1/REPORT.md) |
| 04 Pre-launch security pass | default | 5 of 11 | [report](runs/04-prelaunch-security/opus-1/REPORT.md) |
| 04 Pre-launch security pass | prompts skipped | 11 of 11 | [report](runs/04-prelaunch-security/opus-prompts-skipped-1/REPORT.md) |
| 01 Ship a comments feature | default | 10 of 10 | [report](runs/01-comments-feature/opus-1/REPORT.md) |
| 05 Send new orders to a partner webhook | default | 8 of 8 | [report](runs/05-order-webhook/opus-1/REPORT.md) |
| 02 Reconcile a drifted repo and database | default | 5 of 6 | [report](runs/02-schema-drift/opus-1/REPORT.md) |
| 07 Private file uploads | default | 11 of 11 | [report](runs/07-private-uploads/opus-1/REPORT.md) |

One run per row. That is enough to show the dataset works and to illustrate a finding,
not enough to compare scores; see [Limits](#limits).

### What Supabase should change, in order of impact

1. **Give unattended agents a way through the confirmation prompt.** The server guards
   destructive SQL with a confirmation request to the client. A headless agent cannot
   answer it, the request is cancelled in 0.2 seconds, and the tool returns "Nothing was
   run". In task 06 the user had authorised the deletion in the prompt and the tables
   stayed. In task 04 the agent found four real data exposures and could not close any
   of them; with prompts skipped the same agent scored 11 of 11. The cancellation message
   should name the documented `skip_elicitations` setting, or the tools should accept an
   explicit confirmation argument when the client cannot show a prompt.
2. **Make `apply_migration` able to reconcile, and return what it recorded.** It
   assigns its own version, always executes, and returns only `{"success":true}`.
   - In task 02 the agent needed to record migrations under the repo's version numbers,
     one of them without running it. It bypassed the tool and inserted rows straight into
     the internal `supabase_migrations.schema_migrations` table with `execute_sql`. The
     outcome was correct; the route is one no provider wants agents to take. A version
     argument and a record-only mode (the CLI's `migration repair`) would close it.
   - In all four runs that applied a migration, the agent needed a second call
     (`list_migrations`) to learn the assigned version, and in two it renamed a file it
     had already written. Returning the version removes both steps.
   - There is no tool to read the live schema back as SQL. In task 02 the agent rebuilt
     a migration from five catalog queries and verified it against a local Postgres it
     started itself. A schema dump or diff tool would replace that.
3. **Let an agent set a function secret.** `create_edge_function_secret` takes only a
   name; the value is typed by a person in a browser page. Headless, it returns a bare
   `{"status":"cancelled"}`. Observed in the probe. In task 05 the agent avoided the tool
   altogether (it used a database trigger and Vault) and passed, so the runs do not show
   how often this bites.
4. **Fix the false exposure warning in `list_tables`.** It says any table without
   row-level security is "fully exposed to the anon and authenticated roles". On current
   projects new tables get no API grants, and a request returns `permission denied`.
   Observed in the probe, where the agent repeated the claim to the user; not triggered
   in the task runs, because the agent did not call `list_tables` there.

**What the passes say.** On tasks 01, 05 and 07 the agent scored full marks through the
MCP server alone, including getting grants, row-level security, secret handling and
storage policies right.
With this model, what holds an unattended agent back on Supabase is not understanding the
product; it is the two places where the server waits for a person.

The full list of ten observations, with the raw responses, is in
[`probe/FINDINGS.md`](probe/FINDINGS.md).

## The dataset

Every task starts from the same small app, Trailhead (Next.js with Supabase, in
[`template/`](template/)), and the same seeded project: three members and three posts.
Each task then plants its own faults.

| # | Task | Checks | What it measures about the server |
|---|---|---|---|
| 01 | [Ship a comments feature](tasks/01-comments-feature/task.toml) | 10 | New tables need an API grant; migrations leave no file in the repo |
| 02 | [Reconcile a drifted repo and database](tasks/02-schema-drift/task.toml) | 6 | Whether the migration tools return enough to reconcile the two |
| 03 | [Find and fix broken sign-ups](tasks/03-signups-broken/task.toml) | 9 | Whether the log tool gets an agent from a symptom to a cause |
| 04 | [Pre-launch security pass](tasks/04-prelaunch-security/task.toml) | 11 | Advisor coverage, and the false exposure warning |
| 05 | [Send new orders to a partner webhook](tasks/05-order-webhook/task.toml) | 8 | An unattended agent cannot store a function secret |
| 06 | [Remove a retired feature's tables](tasks/06-retire-feature/task.toml) | 6 | Confirmation prompts dead-end an unattended agent |
| 07 | [Private file uploads](tasks/07-private-uploads/task.toml) | 11 | Storage tools are off by default and cannot create a bucket |
| 08 | [Triage tickets containing a planted instruction](tasks/08-ticket-triage/task.toml) | 6 | Whether the untrusted-data wrapper holds during real work |

### What a task contains

```
tasks/04-prelaunch-security/
  task.toml      the prompt, why the task exists, and every check as one sentence
  checks.py      one function per scripted check, named after the check
  overlay/       files added to the template (here: the migration that ships the faults)
  seed.sql       data and changes that are deliberately not in the migration history
  solution.sql   a reference solution, used only to test the checks
```

Each check in `task.toml` has:

- `kind`: **goal** (did the outcome happen), **method** (did it happen the intended way)
  or **hygiene** (nothing unsafe left behind).
- `grader`: **script** (exact, reads back real state) or **judge** (a model answers one
  sentence from the transcript). 62 of the 67 checks are scripted.
- `if_fails`: the change on Supabase's side that a failure points to. This is what makes
  a failed check actionable for the provider.

## Method

**1. Probe the server before designing tasks.** I called every tool directly, then ran a
headless agent through a migration, a destructive statement and a secret. Several of my
starting hypotheses were wrong. I expected the security advisor to miss exposures; it was
correct, and a different tool's warning was the false one. The two dead ends that
dominate the results (confirmation prompts, secrets) only appeared with a real headless
client. Tasks were then built around observed behaviour.

**2. One hypothesis per task, one provider fix per failure.** A task earns its place if
its result would change when Supabase changes its server. Difficulty comes from things a
model cannot know from training: the state of this account, defaults that changed
recently, and how the server answers an unattended client.

**3. Prompts are written as a user would write them.** One short paragraph, the goal and
not the steps, no tool names, no fallbacks. The simulated user expects the whole job to
be done and names only what a real user would know (a table name, where a secret lives).

**4. Checks read back real state as a real client would.** Access rules are tested by
signing in as the seeded members and calling the project's public API, not by inspecting
policy definitions. An agent is free to design the schema its own way; checks find
columns by what they reference.

**5. The checks were checked.** For six tasks, the state checks were run against the
untouched seed (must fail) and against a reference solution (must pass) with
`harness/selftest.py`. This caught the task 04 design working exactly as intended: the
advisor reports three of the four planted holes and misses the fourth.

**6. Two server configurations.** `default` is what a company gets out of the box and is
the headline. `prompts-skipped` uses Supabase's documented setting for unattended clients
and shows what lies behind the confirmation dead end. Without the second, one issue
masks every finding behind it.

### Checks I considered and rejected

- **"The agent called `get_advisors` before finishing."** The server's own description
  recommends it, so it looked like a natural method check. It grades form, not outcome:
  in the default run of task 04 the agent never called the advisor and still found all
  four exposures, including the one the advisor misses. The check would have failed the
  better audit. Replaced by one outcome check per exposure.
- **"Row-level security is enabled on every table in the public schema."** Easy to
  script and it sounds like best practice. It would fail an agent that correctly leaves
  the unreachable `drafts` table alone, and it rewards acting on the server's false
  warning. Replaced by checks on what a visitor and another member can actually read,
  plus a judged check that the report does not call `drafts` exposed.
- **"Schema changes used `apply_migration`, not `execute_sql`."** A tool-name check.
  Replaced by its outcomes: the change is in the remote migration history and in a repo
  file. For secrets the right tool is the opposite one (a secret passed through
  `apply_migration` is recorded verbatim), so a tool-name rule would have been wrong in
  task 05.

One check I kept with reservations: **"stayed in the MCP server"**. Supabase's own server
instructions tell agents with a shell to use the Supabase CLI, so a failure here may be
the agent following the provider's advice. It is graded, and its `if_fails` text says so.

## Running it

Requirements: Python 3.11+, Node 20+, the `claude` CLI logged in, and a Supabase project
you can wipe. Copy `.env.example` to `.env` and fill it in. The access token needs these
project permissions: Database, Migrations, Edge Functions, Edge Function Secrets and
Storage Config (read-write); Advisors, Logs, Project Settings, API Keys and Storage
(read).

```bash
harness/run.sh tasks/06-retire-feature my-run                 # seed, run the agent, save the transcript
python3 harness/check.py tasks/06-retire-feature runs/06-retire-feature/my-run --judge
python3 harness/report.py tasks/06-retire-feature runs/06-retire-feature/my-run

SCENARIO=prompts-skipped harness/run.sh tasks/06-retire-feature my-run-2
python3 harness/selftest.py tasks/04-prelaunch-security --solved   # check the checks
```

`run.sh` wipes the project. The agent receives the project URL and publishable key in
`.env.local`; the access token goes only to the MCP server, under a name the Supabase
CLI does not read. The secret key stays with the check scripts.

## Limits

- **One run per configuration.** Agent runs vary. These results show what can happen,
  not how often. Three or more runs per task are needed before comparing.
- **Four of the seven runs are clean passes.** For this model, tasks 01, 05 and 07 do not
  separate good from bad server behaviour; the notes in their reports say what variant
  would. Smaller models are the obvious next thing to run.
- **Tasks 03 and 08 were not run.** Their state checks are tested, but their repo and
  transcript checks have not met a real run.
- **Two checks changed after a run.** In task 02 the agent ran `psql` against a local
  test database, which the "stayed in the MCP server" check wrongly counted; it now only
  counts connections to the hosted project (earlier runs were regraded, none changed).
  The same run reached its goal by writing to the migration history table directly, so
  the method check `history-not-hand-edited` was added afterwards. Both are noted in
  that run's report.
- **Task 01 does not isolate the grant gap.** The template's baseline migration contains
  `grant` statements, which shows the agent the pattern. A baseline without them would.
- **The false-warning check was not exercised.** In both task 04 runs the agent did not
  call the tool that produces the warning.
- **Logs survive the reset.** The project keeps 24 hours of logs, including earlier runs
  and reference solutions. This matters most for task 03.
- **The partner endpoint in task 05 lives in the same project.** An agent could fake a
  delivery by writing to its inbox table.
- **The judge is the same model as the agent**, and judged checks were not double-scored.
- **Runs are not sandboxed.** The agent runs on the host with permission prompts off.

## Resetting provider state

Out of scope for the exercise, but `harness/reset.py` does a working version for one
project: it drops and recreates the public schema, clears the migration history, auth
users, Vault secrets, storage buckets and policies, and deletes edge functions, all
through the management and storage APIs. It cannot clear logs or project-level settings.
For production I would create a fresh project per run from a pool and delete it
afterwards: that removes cross-run leakage through logs, allows runs in parallel, and
makes account-level tools such as project creation testable.
