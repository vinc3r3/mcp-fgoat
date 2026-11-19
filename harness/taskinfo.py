#!/usr/bin/env python3
"""Print one field of a task for the runner: `prompt`, or `env` as KEY=value lines."""
import pathlib
import sys
import tomllib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mcp_call import env  # noqa: E402

task = tomllib.loads((pathlib.Path(sys.argv[1]) / "task.toml").read_text())
if sys.argv[2] == "prompt":
    print(task["prompt"].strip())
elif sys.argv[2] == "env":
    for key, value in task.get("env", {}).items():
        print(f"{key}={value.replace('{{SUPABASE_URL}}', env()['SUPABASE_URL'])}")
