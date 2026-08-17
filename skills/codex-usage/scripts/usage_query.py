#!/usr/bin/env python3
"""Query remaining quota for local Codex and OpenCode Go subscriptions.

Read-only, no external installation required. Both sources use standard
credential files that exist on any machine where the user has logged in:

- codex:       ~/.codex/auth.json (OAuth tokens) + `codex app-server --stdio`
               JSON-RPC method `account/rateLimits/read`
- opencode-go: ~/.local/share/opencode/auth.json (API key) + GET
               https://opencode.ai/zen/go/v1/usage

Output is JSON on stdout, always oriented around REMAINING (not used).
Exit code 0 on success, 1 on any failure (error JSON on stderr).

Usage:
  python3 usage_query.py [all|codex|opencode-go]
"""

import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone

CODEX_AUTH = os.path.expanduser("~/.codex/auth.json")
OPENCODE_AUTH = os.path.expanduser("~/.local/share/opencode/auth.json")
USAGE_URL = "https://opencode.ai/zen/go/v1/usage"
TIMEOUT = 12


def err(msg):
    print(json.dumps({"error": msg}, ensure_ascii=False), file=sys.stderr)


def local_time(epoch_s):
    if not epoch_s:
        return None
    try:
        return datetime.fromtimestamp(float(epoch_s)).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(epoch_s)


def iso_local(iso):
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(iso)


def find_codex_binary():
    candidates = [
        os.environ.get("CODEX_BIN"),
        os.path.expanduser("~/.local/bin/codex"),
        "/usr/local/bin/codex",
        "/usr/bin/codex",
        "codex",
    ]
    for c in candidates:
        if not c:
            continue
        if os.path.sep in c and os.path.isfile(c):
            return c
        from shutil import which

        found = which(c)
        if found:
            return found
    return None


def codex_quota():
    """Spawn codex app-server and ask for rate limits via JSON-RPC."""
    if not os.path.isfile(CODEX_AUTH):
        raise RuntimeError(f"no codex login: {CODEX_AUTH} not found")
    binary = find_codex_binary()
    if not binary:
        raise RuntimeError("codex CLI not found in PATH or common locations")

    proc = subprocess.Popen(
        [binary, "app-server", "--stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    try:
        def send(obj):
            proc.stdin.write((json.dumps(obj) + "\n").encode())
            proc.stdin.flush()

        send({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": 1, "capabilities": {},
                "clientInfo": {"name": "usage-query", "version": "1.0"},
            },
        })
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        send({"jsonrpc": "2.0", "id": 2, "method": "account/rateLimits/read"})

        deadline = __import__("time").time() + TIMEOUT
        while __import__("time").time() < deadline:
            line = proc.stdout.readline()
            if not line:
                break
            try:
                msg = json.loads(line)
            except Exception:
                continue
            if msg.get("id") == 2:
                if msg.get("error"):
                    raise RuntimeError(msg["error"].get("message", "codex rateLimits error"))
                return msg.get("result") or {}
        raise RuntimeError("codex app-server did not answer account/rateLimits/read")
    finally:
        try:
            proc.kill()
        except Exception:
            pass


def opencode_quota():
    """Fetch official usage endpoint with the stored Go API key."""
    if not os.path.isfile(OPENCODE_AUTH):
        raise RuntimeError(f"no opencode-go login: {OPENCODE_AUTH} not found")
    data = json.load(open(OPENCODE_AUTH, encoding="utf-8"))
    key = data.get("opencode-go", {}).get("key")
    if not key:
        raise RuntimeError("opencode-go key missing in auth.json")

    req = urllib.request.Request(USAGE_URL, headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "User-Agent": "roxy-usage-query/1.0",
    })
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        body = json.loads(resp.read().decode())
    usage = body.get("usage")
    if not usage:
        raise RuntimeError("unexpected usage response shape")
    return usage


def remaining(percent):
    try:
        p = float(percent)
    except (TypeError, ValueError):
        return None
    return round(100 - p)


def main():
    source = sys.argv[1] if len(sys.argv) > 1 else "all"
    if source not in ("all", "codex", "opencode-go"):
        err(f"unknown source: {source} (use all|codex|opencode-go)")
        sys.exit(1)

    out = {"fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}

    if source in ("all", "codex"):
        try:
            r = codex_quota()
            limits = r.get("rateLimits") or {}
            primary = limits.get("primary") or {}
            out["codex"] = {
                "plan": limits.get("planType"),
                "primary_window": {
                    "name": "weekly (7d)" if (primary.get("windowDurationMins") or 0) >= 10080 else "rolling",
                    "remaining_percent": remaining(primary.get("usedPercent")),
                    "used_percent": primary.get("usedPercent"),
                    "resets_at_local": local_time(primary.get("resetsAt")),
                    "reached": limits.get("rateLimitReachedType"),
                },
                "spend_control_reached": limits.get("spendControlReached"),
                "reset_credits_available": (r.get("rateLimitResetCredits") or {}).get("availableCount", 0),
            }
        except Exception as e:
            out["codex"] = {"error": str(e)}

    if source in ("all", "opencode-go"):
        try:
            u = opencode_quota()
            windows = {}
            for key, label, limit in (
                ("rolling", "rolling_5h", None),
                ("weekly", "weekly", None),
                ("monthly", "monthly", None),
            ):
                w = u.get(key) or {}
                windows[label] = {
                    "remaining_percent": remaining(w.get("percent")),
                    "used_percent": w.get("percent"),
                    "resets_at_local": iso_local(w.get("resetsAt")),
                    "status": w.get("status"),
                }
            out["opencode_go"] = windows
        except Exception as e:
            out["opencode_go"] = {"error": str(e)}

    print(json.dumps(out, ensure_ascii=False, indent=2))
    if "codex" in out and isinstance(out["codex"], dict) and out["codex"].get("error"):
        sys.exit(1)
    if "opencode_go" in out and isinstance(out["opencode_go"], dict) and out["opencode_go"].get("error"):
        sys.exit(1)


if __name__ == "__main__":
    main()
