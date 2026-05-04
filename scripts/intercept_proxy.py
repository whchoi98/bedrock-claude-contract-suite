"""Local intercepting proxy for Bedrock / Mantle traffic from Claude Code.

Listens on http://127.0.0.1:9001 and forwards every request to the real
Bedrock endpoint. Each request body is parsed (when JSON) and a structured
log entry is written to logs/intercept.jsonl describing:

  - which path was hit (Invoke vs Mantle vs Anthropic Messages shape)
  - whether the body has any cache_control breakpoints
  - the ttl value of each breakpoint (or "<missing>" if none → defaults to 5m)
  - which top-level keys the body has (system, tools, messages, ...)
  - response status and the usage.cache_creation breakdown extracted from
    the response (parsed best-effort for both invoke and SSE responses)

Usage:
    UPSTREAM=https://bedrock-runtime.ap-northeast-2.amazonaws.com \
    LOG_FILE=logs/intercept.jsonl \
    python3 scripts/intercept_proxy.py

Then point Claude Code at it:
    export ANTHROPIC_BEDROCK_BASE_URL=http://127.0.0.1:9001
    export ANTHROPIC_BEDROCK_MANTLE_BASE_URL=http://127.0.0.1:9001
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx

DEFAULT_UPSTREAM = "https://bedrock-runtime.ap-northeast-2.amazonaws.com"
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
LOG_PATH = PROJECT_ROOT / "logs" / "intercept.jsonl"
HOP_BY_HOP = {"connection", "transfer-encoding", "keep-alive", "upgrade",
              "proxy-authenticate", "proxy-authorization", "te", "trailers",
              "content-length", "host"}


def _scan_cache_breakpoints(node, path: str = "$") -> list[dict]:
    """Walk the JSON request body and collect every cache_control occurrence."""
    out: list[dict] = []
    if isinstance(node, dict):
        if "cache_control" in node:
            cc = node["cache_control"]
            ttl = cc.get("ttl") if isinstance(cc, dict) else "<non-dict>"
            out.append({
                "path": path,
                "type": cc.get("type") if isinstance(cc, dict) else None,
                "ttl": ttl if ttl is not None else "<missing>",
                "raw": cc,
            })
        for k, v in node.items():
            out.extend(_scan_cache_breakpoints(v, f"{path}.{k}"))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out.extend(_scan_cache_breakpoints(v, f"{path}[{i}]"))
    return out


def _summarize_request(body: bytes) -> dict:
    try:
        obj = json.loads(body)
    except json.JSONDecodeError:
        return {"json_parse": "failed", "size": len(body)}
    bps = _scan_cache_breakpoints(obj)
    summary = {
        "size": len(body),
        "top_level_keys": sorted(obj.keys()) if isinstance(obj, dict) else None,
        "cache_breakpoint_count": len(bps),
        "cache_breakpoints": bps,
    }
    if isinstance(obj, dict):
        summary["has_system"] = "system" in obj
        summary["has_tools"] = "tools" in obj
        summary["message_count"] = (
            len(obj["messages"]) if isinstance(obj.get("messages"), list) else None
        )
        summary["model"] = obj.get("model") or obj.get("modelId")
        summary["max_tokens"] = obj.get("max_tokens")
        if isinstance(obj.get("anthropic_beta"), list):
            summary["anthropic_beta"] = obj["anthropic_beta"]
    return summary


def _extract_usage_from_response_bytes(data: bytes, content_type: str) -> dict | None:
    """Best-effort extraction of usage.cache_creation breakdown.

    Bedrock /invoke returns a single JSON; /invoke-with-response-stream
    returns AWS event stream binary that wraps SSE JSON events. We try
    several shapes.
    """
    text = data.decode("utf-8", errors="replace")
    candidates: list[str] = []
    # Try whole-body JSON first
    candidates.append(text)
    # Try last "message_delta"/"message_start" SSE event in stream
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            candidates.append(line)
        if "data:" in line:
            after = line.split("data:", 1)[1].strip()
            if after:
                candidates.append(after)
    seen_usage = None
    for c in candidates:
        try:
            obj = json.loads(c)
        except json.JSONDecodeError:
            continue
        usage = None
        if isinstance(obj, dict):
            if "usage" in obj:
                usage = obj["usage"]
            elif obj.get("type") == "message_delta" and "usage" in obj:
                usage = obj["usage"]
            elif obj.get("type") == "message_start":
                msg = obj.get("message") or {}
                if "usage" in msg:
                    usage = msg["usage"]
        if isinstance(usage, dict):
            seen_usage = {
                "input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"),
                "cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
                "cache_read_input_tokens": usage.get("cache_read_input_tokens"),
                "cache_creation": usage.get("cache_creation"),
            }
    return seen_usage


def make_handler(upstream: str, log_path: pathlib.Path, label: str):
    log_lock = threading.Lock()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_fh = log_path.open("a", buffering=1)
    upstream_client = httpx.Client(http2=False, timeout=300.0, verify=True)

    def write_log(entry: dict) -> None:
        entry["t"] = dt.datetime.now(dt.timezone.utc).isoformat()
        with log_lock:
            log_fh.write(json.dumps(entry, default=str) + "\n")

    class Handler(BaseHTTPRequestHandler):
        timeout = 300

        def log_message(self, fmt, *args):  # quiet stdout spam
            return

        def _proxy(self):
            clen = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(clen) if clen > 0 else b""
            req_summary = _summarize_request(body) if body else {"size": 0}
            fwd_headers = {
                k: v for k, v in self.headers.items()
                if k.lower() not in HOP_BY_HOP
            }
            url = upstream.rstrip("/") + self.path
            inbound_header_summary = {
                k: ("<set>" if k.lower() == "authorization" else v[:80])
                for k, v in self.headers.items()
            }
            try:
                upstream_resp = upstream_client.request(
                    self.command, url, content=body, headers=fwd_headers,
                )
                resp_bytes = upstream_resp.content
                resp_status = upstream_resp.status_code
                resp_headers = list(upstream_resp.headers.multi_items())
                usage = _extract_usage_from_response_bytes(
                    resp_bytes, upstream_resp.headers.get("content-type", "")
                )
                write_log({
                    "label": label,
                    "method": self.command,
                    "path": self.path,
                    "inbound_headers": inbound_header_summary,
                    "request": req_summary,
                    "response_status": resp_status,
                    "response_size": len(resp_bytes),
                    "response_body_preview": resp_bytes[:300].decode("utf-8", errors="replace"),
                    "response_usage": usage,
                })
                self.send_response(resp_status)
                for k, v in resp_headers:
                    if k.lower() in HOP_BY_HOP:
                        continue
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(resp_bytes)
            except (httpx.HTTPError, OSError) as e:
                write_log({
                    "label": label,
                    "method": self.command,
                    "path": self.path,
                    "request": req_summary,
                    "error": f"{type(e).__name__}: {e}",
                })
                self.send_response(502)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"proxy_error": str(e)}).encode())

        do_POST = _proxy
        do_GET = _proxy
        do_PUT = _proxy
        do_DELETE = _proxy
        do_OPTIONS = _proxy

    return Handler


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9001)
    ap.add_argument("--upstream", default=os.environ.get("UPSTREAM", DEFAULT_UPSTREAM))
    ap.add_argument("--log-file", default=os.environ.get("LOG_FILE", str(LOG_PATH)))
    ap.add_argument("--label", default=os.environ.get("PROXY_LABEL", "default"))
    args = ap.parse_args()

    log_path = pathlib.Path(args.log_file)
    handler = make_handler(args.upstream, log_path, args.label)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"Intercepting proxy listening on http://127.0.0.1:{args.port}")
    print(f"  upstream: {args.upstream}")
    print(f"  log:      {log_path}")
    print(f"  label:    {args.label}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
