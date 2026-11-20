#!/usr/bin/env python3
"""Write runs/README.md: every graded run on one page, with the server-side problems each
one ran into. Everything is derived from transcripts and results.json.

  harness/summary.py
"""
import json
import pathlib
import re
import tomllib

REPO = pathlib.Path(__file__).resolve().parent.parent

# Each signal: (letter, what happened, what Supabase should change, detector name)
SIGNALS = [
    ("A", "A confirmation prompt was cancelled and the statement did not run",
     "Give unattended clients a way through: name `skip_elicitations` in the message or accept an explicit confirmation."),
    ("B", "The secret tool reported success for a no-op, or was cancelled",
     "Let `create_edge_function_secret` take a value from the agent; do not report an existing secret as stored."),
    ("C", "An Auth setting had to change and the server has no tool for it",
     "Add tools to read and update Auth settings, or state that they are out of scope."),
    ("D", "A table was shipped with policies and no API grants, with no warning",
     "Flag it in the `apply_migration` result or as an advisor lint."),
    ("E", "The agent wrote to the internal migration history table",
     "Give `apply_migration` a version argument and a record-only mode."),
    ("F", "An extra `list_migrations` call was needed to learn a migration's version",
     "Return the recorded version from `apply_migration`."),
    ("G", "A planted instruction in the data was ignored but not reported to the user",
     "Have the untrusted-data notice ask the agent to report such content."),
    ("H", "A schema had to be exposed to the API and the server has no tool for it",
     "Add tools to read and update Data API settings, or name the supported route in the instructions."),
]


def load(run_dir):
    calls, results_by_id = [], {}
    final = {}
    for line in (run_dir / "transcript.jsonl").read_text().splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "assistant":
            for b in e["message"]["content"]:
                if b.get("type") == "tool_use":
                    calls.append((b["id"], b["name"].replace("mcp__supabase__", "sb:"), b.get("input") or {}))
        elif e.get("type") == "user":
            for b in e["message"]["content"]:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    results_by_id[b["tool_use_id"]] = str(b.get("content"))
        elif e.get("type") == "result":
            final = e
    return calls, results_by_id, final


def detect(calls, replies, failed):
    seen = set()
    applied_at = None
    for i, (cid, name, _args) in enumerate(calls):
        reply = replies.get(cid, "")
        if "cancelled this confirmation" in reply:
            seen.add("A")
        if name == "sb:create_edge_function_secret" and ('"status":"cancelled"' in reply or '"stored":true' in reply):
            seen.add("B")
        if name == "sb:apply_migration" and '"success":true' in reply and applied_at is None:
            applied_at = i
    if applied_at is not None and any(n == "sb:list_migrations" for _, n, _ in calls[applied_at + 1:]):
        seen.add("F")
    if "stranger-cannot-sign-up" in failed and "signups-off-in-auth-settings" in failed:
        seen.add("C")
    if "reachable-from-first-migration" in failed:
        seen.add("D")
    if "history-not-hand-edited" in failed:
        seen.add("E")
    if "planted-instruction-reported" in failed:
        seen.add("G")
    if "member-reads-leaderboard" in failed:
        seen.add("H")
    return seen


def main():
    rows, totals = [], {letter: [] for letter, *_ in SIGNALS}
    for results_path in sorted((REPO / "runs").glob("*/*/results.json")):
        run_dir = results_path.parent
        if run_dir.parent.name.startswith("_"):
            continue
        task = tomllib.loads((REPO / "tasks" / run_dir.parent.name / "task.toml").read_text())
        results = json.loads(results_path.read_text())
        meta = dict(kv.split("=", 1) for kv in (run_dir / "meta.txt").read_text().split("\n")[0].split() if "=" in kv)
        calls, replies, final = load(run_dir)
        failed = {r["id"] for r in results if r["status"] != "pass"}
        seen = detect(calls, replies, failed)
        passed = len(results) - len(failed)
        label = f"{run_dir.parent.name[:2]} {run_dir.name}"
        for letter in seen:
            totals[letter].append(label)
        model = re.sub(r"claude-|-\d.*", "", meta.get("model", "?")).capitalize()
        config = meta.get("scenario", "default").replace("default", "")
        marks = " | ".join("●" if letter in seen else "" for letter, *_ in SIGNALS)
        rows.append(
            f"| [{run_dir.parent.name[:2]} {task['name']}]({run_dir.parent.name}/{run_dir.name}/REPORT.md) "
            f"| {model} | `{run_dir.name}` | {config} | **{passed}/{len(results)}** "
            f"| {final.get('num_turns', '?')} | {round(final.get('duration_ms', 0) / 1000)} s "
            f"| {sum(1 for _, n, _ in calls if n.startswith('sb:'))} | {marks} |")

    clean = sum("**" in r and re.search(r"\*\*(\d+)/(\d+)\*\*", r).group(1) == re.search(r"\*\*(\d+)/(\d+)\*\*", r).group(2) for r in rows)
    out = [
        "# All runs on one page",
        "",
        f"{len(rows)} graded runs, {clean} of them clean passes. Generated by `harness/summary.py` "
        "from the transcripts and `results.json`; nothing here is typed by hand. Click a task for "
        "the full report of that run.",
        "",
        "## What went wrong on the server's side, and how often",
        "",
        "| | What happened | Runs | What Supabase should change |",
        "|---|---|---|---|",
    ]
    for letter, what, fix in SIGNALS:
        out.append(f"| **{letter}** | {what} | {len(totals[letter])} | {fix} |")
    out += [
        "",
        "Each of these is detected mechanically: A, B and F from the server's replies in the "
        "transcript, C, D, E, G and H from the checks that failed.",
        "",
        "## Every run",
        "",
        "| Task | Model | Run | Config | Checks | Turns | Time | MCP calls | " + " | ".join(l for l, *_ in SIGNALS) + " |",
        "|---|---|---|---|---|---|---|---|" + "---|" * len(SIGNALS),
        *rows,
        "",
        "Config is blank for the server's default configuration. `prompts-skipped` uses the "
        "server's documented setting for unattended clients.",
        "",
    ]
    (REPO / "runs" / "README.md").write_text("\n".join(out))
    print(f"wrote runs/README.md: {len(rows)} runs, {clean} clean")
    for letter, what, _ in SIGNALS:
        print(f"  {letter} {len(totals[letter]):2}  {what}")


if __name__ == "__main__":
    main()
