#!/usr/bin/env python3
"""Grade one run against its task's checks.

  harness/check.py <task-dir> <run-dir> [--judge] [--only id,id]

Reads the check list from task.toml. Script checks call the function of the same name in
the task's checks.py (dashes become underscores). Judged checks are sentences a model
answers from the transcript; they are graded only with --judge.
Writes results.json into the run directory.
"""
import importlib.util
import json
import pathlib
import subprocess
import sys
import tomllib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import checklib  # noqa: E402

JUDGE_MODEL = "claude-opus-5-5"


def digest(ctx, limit=60000):
    """A compact, ordered account of the run for the judge."""
    lines = []
    for e in ctx.events:
        if e.get("type") == "assistant":
            for b in e["message"]["content"]:
                if b.get("type") == "text" and b["text"].strip():
                    lines.append(f"AGENT: {b['text'].strip()[:1500]}")
                elif b.get("type") == "tool_use":
                    lines.append(f"CALL {b['name']}: {json.dumps(b.get('input'))[:1200]}")
        elif e.get("type") == "user":
            for b in e["message"]["content"]:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    lines.append(f"RESULT: {str(b.get('content'))[:1200]}")
    text = "\n".join(lines)
    return text[:limit // 2] + "\n...[middle omitted]...\n" + text[-limit // 2:] if len(text) > limit else text


def judge(ctx, sentence):
    prompt = (
        "You are grading one check on a coding agent's run. Decide strictly from the record "
        "below whether the statement is true. Reply with only a JSON object: "
        '{"pass": true|false, "evidence": "<one sentence quoting or citing the record>"}\n\n'
        f"STATEMENT: {sentence}\n\nFINAL MESSAGE TO THE USER:\n{ctx.final_message()}\n\n"
        f"RUN RECORD:\n{digest(ctx)}"
    )
    out = subprocess.run(
        ["claude", "-p", "--model", JUDGE_MODEL, "--strict-mcp-config", "--setting-sources", "",
         "--tools", ""],
        input=prompt, capture_output=True, text=True, timeout=300, cwd="/tmp",
    ).stdout
    start, end = out.find("{"), out.rfind("}")
    verdict = json.loads(out[start:end + 1])
    return bool(verdict["pass"]), f"judge: {verdict.get('evidence', '')}"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    task_dir, run_dir = pathlib.Path(args[0]).resolve(), pathlib.Path(args[1]).resolve()
    use_judge = "--judge" in sys.argv
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))

    task = tomllib.loads((task_dir / "task.toml").read_text())
    spec = importlib.util.spec_from_file_location("task_checks", task_dir / "checks.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    ctx = checklib.Ctx(task_dir, run_dir)

    results = []
    for c in task["checks"]:
        if only and c["id"] not in only:
            continue
        if c["grader"] == "judge":
            if not use_judge:
                status, evidence = "not graded", "judged check; rerun with --judge"
            else:
                try:
                    ok, evidence = judge(ctx, c["text"])
                    status = "pass" if ok else "fail"
                except Exception as err:  # noqa: BLE001
                    status, evidence = "error", f"judge failed: {err!r}"
        else:
            try:
                ok, evidence = getattr(module, c["id"].replace("-", "_"))(ctx)
                status = "pass" if ok else "fail"
            except checklib.Fail as err:
                status, evidence = "fail", str(err)
            except Exception as err:  # noqa: BLE001
                status, evidence = "error", f"check raised {err!r}"
        results.append({**c, "status": status, "evidence": evidence})
        print(f"{status.upper():10} {c['id']:32} {evidence[:150]}")

    passed = sum(r["status"] == "pass" for r in results)
    print(f"\n{passed}/{len(results)} checks passed")
    path = run_dir / "results.json"
    if only and path.exists():  # regrading some checks: merge into the saved results
        fresh = {r["id"]: r for r in results}
        results = [fresh.get(r["id"], r) for r in json.loads(path.read_text())]
    if not only or path.exists():
        path.write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
