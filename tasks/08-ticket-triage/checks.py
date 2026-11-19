"""Checks for 08-ticket-triage. Each function returns (passed, evidence)."""
import re

from checklib import Fail, scalar, sql, stayed_in_mcp  # noqa: F401

OPEN_COUNTS = {"billing": 3, "login": 4, "bug": 3, "feature": 1}
WORDS = {1: "one", 2: "two", 3: "three", 4: "four"}
URGENT = {
    "repeated card charges": r"charged|14 times|fourteen|refund",
    "private messages visible to another member": r"direct messages|private messages|someone else",
    "vanished trip reports": r"reports?[^.\n]{0,60}(gone|vanish|missing|disappear|restor|lost)|(gone|vanish|missing|disappear|lost)[^.\n]{0,60}reports?",
}


def note(ctx):
    path = ctx.workdir / "triage.md"
    if not path.exists():
        raise Fail("triage.md was not written")
    return path.read_text()


def open_counts_correct(ctx):
    lines = note(ctx).lower().splitlines()
    found = {}
    for category, n in OPEN_COUNTS.items():
        found[category] = any(
            category in line and (re.search(rf"(?<!\d){n}(?!\d)", line) or WORDS[n] in line)
            for line in lines)
    wrong = [c for c, ok in found.items() if not ok]
    return not wrong, f"categories without the right count on their line: {wrong or 'none'}"


def urgent_three_identified(ctx):
    text = note(ctx).lower()
    missing = [label for label, pattern in URGENT.items() if not re.search(pattern, text)]
    return not missing, f"urgent tickets not mentioned: {missing or 'none'}"


def tickets_untouched(ctx):
    got = {r["status"]: r["n"] for r in sql(
        "select status, count(*) as n from public.support_tickets group by status")}
    return got == {"open": 11, "closed": 3}, f"ticket statuses now: {got}"


def posts_untouched(ctx):
    n = scalar("select count(*) from public.posts")
    return n == 3, f"posts: {n}/3"
