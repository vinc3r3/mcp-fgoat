#!/usr/bin/env bash
# Run one task with a headless coding agent and save the transcript.
#
#   harness/run.sh <task-dir> [run-name]
#
# The agent starts in a fresh copy of the template, outside this repo, with only the
# Supabase MCP server attached. Only the MCP server receives the access token and project ref: the secret key in .env stays with the check scripts.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
TASK_DIR="$(cd "$1" && pwd)"
TASK="$(basename "$TASK_DIR")"
RUN_NAME="${2:-$(date +%Y%m%d-%H%M%S)}"
MODEL="${MODEL:-claude-opus-5-5}"
# SCENARIO=default        the server as a company gets it out of the box
# SCENARIO=prompts-skipped the server's documented setting for unattended clients, which
#                          skips its confirmation prompts for SQL and migrations
SCENARIO="${SCENARIO:-default}"
MCP_CONFIG="$REPO/harness/mcp.json"
if [ "$SCENARIO" = "prompts-skipped" ]; then MCP_CONFIG="$REPO/harness/mcp.prompts-skipped.json"; fi
OUT="$REPO/runs/$TASK/$RUN_NAME"
WORK="${WORK_ROOT:-$HOME/.cache/mcp-fgoat-runs}/$TASK/$RUN_NAME"

env_value() { grep "^$1=" "$REPO/.env" | cut -d= -f2-; }

mkdir -p "$OUT" "$WORK"

# Known provider state: empty project, base schema and data, then the task's planted faults.
python3 "$REPO/harness/seed.py" "$TASK_DIR" > "$OUT/seed.log" 2>&1

# Fresh checkout of the starter app, plus any task-specific files.
rsync -a --exclude node_modules --exclude .next "$REPO/template/" "$WORK/"
if [ -d "$TASK_DIR/overlay" ]; then rsync -a "$TASK_DIR/overlay/" "$WORK/"; fi
printf 'NEXT_PUBLIC_SUPABASE_URL=%s\nNEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=%s\n' \
  "$(env_value SUPABASE_URL)" "$(env_value SUPABASE_PUBLISHABLE_KEY)" > "$WORK/.env.local"
# Extra values a task hands the agent, from [env] in task.toml.
python3 "$REPO/harness/taskinfo.py" "$TASK_DIR" env >> "$WORK/.env.local"

cd "$WORK"
# Setup runs before the agent so an install failure is never blamed on it.
npm install --no-audit --no-fund > "$OUT/setup.log" 2>&1
git init -q && git add -A && git commit -qm "template" --allow-empty

echo "task=$TASK model=$MODEL scenario=$SCENARIO work=$WORK" | tee "$OUT/meta.txt"

# The token is passed under a name the Supabase CLI does not read, so the CLI is not
# silently logged in and the MCP server stays the only authenticated route.
SUPABASE_MCP_TOKEN="$(env_value SUPABASE_ACCESS_TOKEN)" \
SUPABASE_MCP_PROJECT_REF="$(env_value SUPABASE_PROJECT_REF)" \
claude -p "$(python3 "$REPO/harness/taskinfo.py" "$TASK_DIR" prompt)" \
  --model "$MODEL" \
  --mcp-config "$MCP_CONFIG" --strict-mcp-config \
  --setting-sources "" \
  --dangerously-skip-permissions \
  --output-format stream-json --verbose \
  < /dev/null > "$OUT/transcript.jsonl" 2> "$OUT/stderr.txt" || echo "agent exited non-zero" | tee -a "$OUT/meta.txt"

# What the agent changed in the working directory.
git add -A && git diff --cached --stat > "$OUT/diff-stat.txt" && git diff --cached > "$OUT/changes.diff"
echo "$WORK" > "$OUT/workdir.txt"
echo "done: $OUT"
