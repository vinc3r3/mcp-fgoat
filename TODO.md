# TODO

Working notes. Remove or fold into the README before submitting.

## Stretch goals (only after tasks and reports are done)

- **Run tasks in a container.** A Dockerfile would make the dataset reproducible on a
  reviewer's machine and match the Harbor format the brief mentions. Today `harness/run.sh`
  runs the agent on the host with permission prompts skipped. A container needs separate
  Claude auth (a token from `claude setup-token` or an API key), since the host login lives
  in the macOS keychain. Estimated 30-60 minutes.
  - Until then: say in the write-up that a production version would sandbox each run.
  - Until then: keep the planted text in the prompt-injection task aimed at the database
    only, never at files or shell commands, and do not leave runs unattended.

## For the write-up

- **Logs survive the reset.** `harness/reset.py` empties the database, but the project's
  logs keep the last 24 hours, including the harness's own seed statements, earlier runs
  and reference solutions applied by `harness/selftest.py`. An agent that reads logs can
  see them. A production harness needs a fresh project per run. Until then: do not run
  `selftest.py --solved` for a task shortly before running that task for real, and check
  the transcript of any run that queried logs.
