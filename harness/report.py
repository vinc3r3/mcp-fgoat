#!/usr/bin/env python3
"""Write REPORT.md for one graded run: what the agent did, where it failed, what to fix.

  harness/report.py <task-dir> <run-dir>

Everything is generated from the transcript and results.json, except the "Reading"
section, which is taken from notes.md in the run directory when a person has written one.
"""
import json
import pathlib
import re
import sys
import tomllib

ICON = {"pass": "✅ pass", "fail": "❌ fail", "error": "⚠️ error", "not graded": "➖ not graded"}


def short(value, limit):
    text = re.sub(r"\s+", " ", value if isinstance(value, str) else json.dumps(value))
    return text if len(text) <= limit else text[: limit - 1] + "…"


def describe_call(name, args):
    if name.startswith("mcp__supabase__"):
        tool = name.replace("mcp__supabase__", "")
        detail = args.get("query") or args.get("sql") or args.get("graphql_query") or args.get("name") or args
        label = f"**Supabase `{tool}`**"
        if tool == "apply_migration":
            detail = f"{args.get('name')}: {args.get('query', '')}"
        return f"{label} {short(detail, 170) if detail else ''}".strip()
    if name == "Bash":
        return f"Shell: `{short(args.get('command', ''), 150).replace('`', chr(39))}`"
    if name in ("Write", "Edit", "Read"):
        path = pathlib.Path(args.get("file_path", "")).name
        return f"{name} file `{path}`"
    if name == "ToolSearch":
        return "Loaded Supabase tool definitions (client step, not scored)"
    return f"{name} {short(args, 120)}"


def describe_result(content):
    text = content if isinstance(content, str) else " ".join(
        b.get("text", "") for b in content if isinstance(b, dict))
    text = re.sub(r"Below is the result of the SQL query\..*?<untrusted-data-[0-9a-f-]+>", "", text, flags=re.S)
    text = re.sub(r"</untrusted-data.*", "", text, flags=re.S)
    return short(text.strip(), 240)


def noteworthy(text):
    low = text.lower()[:400]
    return any(w in low for w in ('"status":"cancelled"', '"error"', "permission denied", "exit code", "cannot open"))


def main():
    task_dir, run_dir = pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2]).resolve()
    task = tomllib.loads((task_dir / "task.toml").read_text())
    results = json.loads((run_dir / "results.json").read_text())
    meta = dict(kv.split("=", 1) for kv in (run_dir / "meta.txt").read_text().split("\n")[0].split() if "=" in kv)

    events = []
    for line in (run_dir / "transcript.jsonl").read_text().splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            pass
    final = next((e for e in reversed(events) if e.get("type") == "result"), {})

    steps, pending = [], {}
    for e in events:
        if e.get("type") == "assistant":
            for b in e["message"]["content"]:
                if b.get("type") == "tool_use":
                    pending[b["id"]] = len(steps)
                    steps.append([describe_call(b["name"], b.get("input") or {}), None])
        elif e.get("type") == "user":
            for b in e["message"]["content"]:
                if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id") in pending:
                    steps[pending[b["tool_use_id"]]][1] = describe_result(b.get("content") or "")

    passed = sum(r["status"] == "pass" for r in results)
    mcp_calls = sum(1 for s, _ in steps if s.startswith("**Supabase"))
    out = [
        f"# {task['name']}",
        "",
        f"Run `{run_dir.name}` of task `{task_dir.name}`.",
        "",
        "| | |",
        "|---|---|",
        f"| Result | **{passed} of {len(results)} checks passed** |",
        f"| Agent | Claude Code, model `{meta.get('model', '?')}` |",
        f"| Server configuration | `{meta.get('scenario', 'default')}` |",
        f"| Duration | {round(final.get('duration_ms', 0) / 1000)} s, {final.get('num_turns', '?')} turns, "
        f"{mcp_calls} Supabase MCP calls |",
        f"| Cost | ${final.get('total_cost_usd', 0):.2f} |",
        "",
        "## Prompt",
        "",
        "> " + task["prompt"].strip().replace("\n", "\n> "),
        "",
    ]
    if (run_dir / "notes.md").exists():
        out += ["## Reading", "", (run_dir / "notes.md").read_text().strip(), ""]

    out += ["## Checks", "", "| Result | Kind | Check | Evidence |", "|---|---|---|---|"]
    for r in results:
        out.append(f"| {ICON[r['status']]} | {r['kind']} | {r['text']} | {short(r['evidence'], 200).replace('|', '/')} |")

    fixes = []
    for r in results:
        if r["status"] == "fail" and r.get("if_fails") and r["if_fails"] not in [f for _, f in fixes]:
            fixes.append((r["id"], r["if_fails"]))
    out += ["", "## What the provider should change", ""]
    out += [f"- **{cid}:** {fix}" for cid, fix in fixes] or [
        "No failed check in this run points to a provider-side change."]

    out += ["", "## What the agent did", "", "Steps marked ⚠️ returned an error, a refusal or a cancellation.", ""]
    for i, (call, result) in enumerate(steps, 1):
        flag = " ⚠️" if result and noteworthy(result) else ""
        out.append(f"{i}. {call}{flag}")
        if result and (flag or call.startswith("**Supabase `apply_migration`")):
            out.append(f"   - Returned: `{result.replace('`', chr(39))}`")

    out += ["", "## The agent's final message", "", "> " + (final.get("result") or "").strip().replace("\n", "\n> "), ""]
    (run_dir / "REPORT.md").write_text("\n".join(out))
    print(f"wrote {run_dir / 'REPORT.md'} ({passed}/{len(results)})")


if __name__ == "__main__":
    main()
