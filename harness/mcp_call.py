#!/usr/bin/env python3
"""Minimal MCP client for the hosted Supabase server (streamable HTTP, stdlib only).

Used to probe the server exactly as an agent sees it: raw tool descriptions, raw results,
raw errors. Reads SUPABASE_ACCESS_TOKEN and SUPABASE_PROJECT_REF from .env.

  harness/mcp_call.py list                      # tool names, descriptions, schemas
  harness/mcp_call.py call <tool> '<json args>' # one tool call
  harness/mcp_call.py --query 'features=storage' list
"""
import json
import pathlib
import socket
import sys
import urllib.error
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
socket.setdefaulttimeout(90)  # a stalled connection must fail, not hang a run


def env():
    out = {}
    for line in (REPO / ".env").read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            out[k] = v
    return out


class Client:
    CAPS = {}
    def __init__(self, extra_query=""):
        e = env()
        self.url = f"https://mcp.supabase.com/mcp?project_ref={e['SUPABASE_PROJECT_REF']}"
        if extra_query:
            self.url += "&" + extra_query
        self.headers = {
            "Authorization": f"Bearer {e['SUPABASE_ACCESS_TOKEN']}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            # The default Python-urllib agent string is rejected by the server's CDN (403, error 1010).
            "User-Agent": "mcp-fgoat-probe/0.1 (MCP client; AX evaluation)",
        }
        self.id = 0
        self.init = self.rpc(
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": self.CAPS,
                "clientInfo": {"name": "probe", "version": "0"},
            },
        )
        self.rpc("notifications/initialized", None, notify=True)

    def rpc(self, method, params, notify=False):
        body = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            body["params"] = params
        if not notify:
            self.id += 1
            body["id"] = self.id
        req = urllib.request.Request(self.url, json.dumps(body).encode(), self.headers)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                sid = r.headers.get("Mcp-Session-Id")
                if sid:
                    self.headers["Mcp-Session-Id"] = sid
                raw = r.read().decode()
                ctype = r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as err:
            return {"http_error": err.code, "body": err.read().decode()[:2000]}
        if notify or not raw.strip():
            return None
        if "text/event-stream" in ctype:
            msgs = [json.loads(l[5:]) for l in raw.splitlines() if l.startswith("data:")]
            # Server-initiated requests (e.g. elicitation) arrive before the final response.
            final = [m for m in msgs if m.get("id") == body.get("id") and "method" not in m]
            others = [m for m in msgs if m not in final]
            res = final[-1] if final else {"no_final_response": True}
            if others:
                res["_server_messages"] = others
            return res
        return json.loads(raw)


def main():
    args = sys.argv[1:]
    query = ""
    if args and args[0] == "--query":
        query, args = args[1], args[2:]
    c = Client(query)
    if args[0] == "init":
        print(json.dumps(c.init, indent=2))
    elif args[0] == "list":
        print(json.dumps(c.rpc("tools/list", {}), indent=2))
    elif args[0] == "call":
        a = json.loads(args[2]) if len(args) > 2 else {}
        print(json.dumps(c.rpc("tools/call", {"name": args[1], "arguments": a}), indent=2))


if __name__ == "__main__":
    main()
