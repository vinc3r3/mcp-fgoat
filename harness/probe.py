#!/usr/bin/env python3
"""Run a batch of MCP tool calls and save each raw response under probe/.

  harness/probe.py <batch-name> '<json list of [tool, args]>' [extra-query]
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mcp_call import Client, REPO  # noqa: E402

name, calls = sys.argv[1], json.loads(sys.argv[2])
client = Client(sys.argv[3] if len(sys.argv) > 3 else "")
out_dir = REPO / "probe" / name
out_dir.mkdir(parents=True, exist_ok=True)

for i, (tool, args) in enumerate(calls):
    res = client.rpc("tools/call", {"name": tool, "arguments": args})
    (out_dir / f"{i:02d}-{tool}.json").write_text(
        json.dumps({"tool": tool, "arguments": args, "response": res}, indent=2)
    )
    print(f"\n=== {tool} {json.dumps(args)[:200]}")
    r = (res or {}).get("result", res) or {}
    if "content" in r:
        print("isError:", r.get("isError"), "| structuredContent:", "structuredContent" in r)
        for c in r["content"]:
            text = c.get("text") or str(c)
            print(text[:1500] + (f" ...[{len(text)} chars]" if len(text) > 1500 else ""))
    else:
        print(json.dumps(res)[:1500])
    if (res or {}).get("_server_messages"):
        print("SERVER MESSAGES:", json.dumps(res["_server_messages"])[:1000])
