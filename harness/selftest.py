#!/usr/bin/env python3
"""Check the checks: grade a task's seeded state, with or without its reference solution.

  harness/selftest.py <task-dir> [--solved] [--only id,id]

Seeds the project, optionally applies the task's solution.sql, then runs the script checks
against a stand-in run (the task's starting files and an empty transcript). Database checks
should fail on the bare seed and pass with --solved. Checks that read the agent's repo or
transcript cannot pass here.
"""
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
task = pathlib.Path(sys.argv[1]).resolve()
run = REPO / "runs" / "_selftest" / task.name
run.mkdir(parents=True, exist_ok=True)
work = run / "work"
for src in (REPO / "template", task / "overlay"):
    if src.exists():
        subprocess.run(["rsync", "-a", "--exclude", "node_modules", "--exclude", ".next", f"{src}/", f"{work}/"], check=True)
(run / "workdir.txt").write_text(str(work))
(run / "transcript.jsonl").write_text("")

subprocess.run([sys.executable, REPO / "harness/seed.py", task], check=True, stdout=subprocess.DEVNULL)
if "--solved" in sys.argv:
    sys.path.insert(0, str(REPO / "harness"))
    from reset import sql
    from mcp_call import env
    solution = (task / "solution.sql").read_text().replace("{{SUPABASE_URL}}", env()["SUPABASE_URL"])
    sql(solution + "\nnotify pgrst, 'reload schema';")
    import time
    time.sleep(2)
extra = sys.argv[sys.argv.index("--only"):][:2] if "--only" in sys.argv else []
subprocess.run([sys.executable, REPO / "harness/check.py", task, run, *extra])
