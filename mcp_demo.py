#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Xuezhe MCP Demo
----------------
A GitHub-friendly demo client for:
https://mcp.xuezhe.pro/mcp

Features:
- Initialize MCP session
- Send initialized notification
- List tools
- Call a specific tool
- Pretty print responses
- Simple CLI interface
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, Optional

import httpx


DEFAULT_MCP_URL = "https://mcp.xuezhe.pro/mcp"
DEFAULT_PROTOCOL_VERSION = "2025-03-26"


def pretty_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


class MCPError(Exception):
    pass


class MCPClient:
    def __init__(
        self,
        url: str,
        api_key: str,
        protocol_version: str = DEFAULT_PROTOCOL_VERSION,
        timeout: float = 30.0,
    ) -> None:
        self.url = url
        self.api_key = api_key
        self.protocol_version = protocol_version
        self.timeout = timeout
        self.session_id: Optional[str] = None
        self.client = httpx.Client(timeout=self.timeout, follow_redirects=True)

    def _headers(self) -> Dict[str, str]:
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": self.protocol_version,
        }
        if self.session_id:
            # Dual-write for maximum compatibility
            headers["Mcp-Session-Id"] = self.session_id
            headers["MCP-Session-Id"] = self.session_id
        return headers

    def _post(self, payload: Dict[str, Any]) -> tuple[httpx.Response, Optional[Any]]:
        response = self.client.post(self.url, headers=self._headers(), json=payload)

        content_type = (response.headers.get("content-type") or "").lower()
        body_text = response.text.strip()

        # MCP notification often returns 202 with empty body
        if response.status_code == 202 and not body_text:
            return response, None

        if not body_text:
            return response, None

        if "application/json" in content_type:
            try:
                return response, response.json()
            except Exception:
                return response, {"raw_text": response.text}

        return response, {"raw_text": response.text}

    def initialize(self) -> Dict[str, Any]:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": self.protocol_version,
                "capabilities": {},
                "clientInfo": {
                    "name": "xuezhe-mcp-demo",
                    "version": "1.0.0",
                },
            },
        }

        response, data = self._post(payload)

        if response.status_code != 200:
            raise MCPError(f"Initialize failed: HTTP {response.status_code}\n{pretty_json(data)}")

        self.session_id = (
            response.headers.get("Mcp-Session-Id")
            or response.headers.get("MCP-Session-Id")
        )

        if not self.session_id:
            raise MCPError("Initialize succeeded but no Session ID returned.")

        if not isinstance(data, dict) or "result" not in data:
            raise MCPError(f"Unexpected initialize response:\n{pretty_json(data)}")

        return data

    def send_initialized_notification(self) -> None:
        payload = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }

        response, data = self._post(payload)

        if response.status_code not in (200, 202):
            raise MCPError(
                f"Initialized notification failed: HTTP {response.status_code}\n{pretty_json(data)}"
            )

    def list_tools(self) -> Dict[str, Any]:
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }

        response, data = self._post(payload)

        if response.status_code != 200:
            raise MCPError(f"tools/list failed: HTTP {response.status_code}\n{pretty_json(data)}")

        if not isinstance(data, dict):
            raise MCPError(f"Unexpected tools/list response:\n{pretty_json(data)}")

        return data

    def call_tool(self, name: str, arguments: Dict[str, Any], request_id: int = 3) -> Dict[str, Any]:
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments,
            },
        }

        response, data = self._post(payload)

        if response.status_code != 200:
            raise MCPError(
                f"tools/call failed: HTTP {response.status_code}\n{pretty_json(data)}"
            )

        if not isinstance(data, dict):
            raise MCPError(f"Unexpected tools/call response:\n{pretty_json(data)}")

        return data

    def close(self) -> None:
        try:
            if self.session_id:
                self.client.delete(self.url, headers=self._headers())
        finally:
            self.client.close()


def extract_tool_result_text(tool_call_response: Dict[str, Any]) -> Optional[str]:
    """
    MCP tool result often looks like:
    {
      "result": {
        "content": [
          {"type":"text","text":"{...json string...}"}
        ],
        "isError": false
      }
    }
    """
    try:
        content = tool_call_response["result"]["content"]
        if isinstance(content, list):
            for item in content:
                if item.get("type") == "text" and "text" in item:
                    return item["text"]
    except Exception:
        return None
    return None


def print_banner(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_initialize_response(data: Dict[str, Any], session_id: str) -> None:
    print_banner("INITIALIZE")
    result = data.get("result", {})
    print("Server:", result.get("serverInfo", {}).get("name"))
    print("Version:", result.get("serverInfo", {}).get("version"))
    print("Protocol:", result.get("protocolVersion"))
    print("Session ID:", session_id)


def print_tools_summary(data: Dict[str, Any]) -> None:
    print_banner("TOOLS")
    tools = data.get("result", {}).get("tools", [])
    print(f"Total tools: {len(tools)}\n")
    for idx, tool in enumerate(tools, start=1):
        name = tool.get("name", "")
        desc = (tool.get("description") or "").strip().splitlines()[0] if tool.get("description") else ""
        print(f"{idx:02d}. {name}")
        if desc:
            print(f"    {desc}")


def print_tool_call_response(tool_name: str, data: Dict[str, Any]) -> None:
    print_banner(f"TOOL RESULT: {tool_name}")

    text = extract_tool_result_text(data)
    if text:
        try:
            parsed = json.loads(text)
            print(pretty_json(parsed))
            return
        except Exception:
            print(text)
            return

    print(pretty_json(data))


def demo_examples(mcp: MCPClient) -> None:
    print_banner("RUNNING DEMO EXAMPLES")

    examples = [
        (
            "institution_ranking",
            {"mode": "global", "order_by": "works_count", "limit": 5, "page": 1},
        ),
        (
            "talent_discovery",
            {"keyword": "Artificial Intelligence", "order_by": "influence", "limit": 5, "page": 1},
        ),
        (
            "national_tech_structure",
            {"country_code": "CN"},
        ),
    ]

    for i, (tool_name, args) in enumerate(examples, start=1):
        print(f"\n[{i}] Calling {tool_name} with args: {args}")
        result = mcp.call_tool(tool_name, args, request_id=100 + i)
        print_tool_call_response(tool_name, result)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Xuezhe MCP Demo Client")
    parser.add_argument(
        "--url",
        default=DEFAULT_MCP_URL,
        help=f"MCP server URL (default: {DEFAULT_MCP_URL})",
    )
    parser.add_argument(
        "--api-key",
        required=True,
        help="X-API-Key for MCP server",
    )
    parser.add_argument(
        "--list-tools",
        action="store_true",
        help="List available tools",
    )
    parser.add_argument(
        "--tool",
        help="Tool name to call, e.g. institution_ranking",
    )
    parser.add_argument(
        "--args",
        default="{}",
        help='JSON string for tool arguments, e.g. \'{"mode":"global","limit":5}\'',
    )
    parser.add_argument(
        "--run-examples",
        action="store_true",
        help="Run built-in demo examples",
    )
    parser.add_argument(
        "--raw-tools",
        action="store_true",
        help="Print full raw tools/list JSON",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        tool_args = json.loads(args.args)
        if not isinstance(tool_args, dict):
            raise ValueError("--args must be a JSON object")
    except Exception as e:
        print(f"Invalid --args JSON: {e}", file=sys.stderr)
        return 2

    mcp = MCPClient(url=args.url, api_key=args.api_key)

    try:
        init_data = mcp.initialize()
        print_initialize_response(init_data, mcp.session_id or "")
        mcp.send_initialized_notification()

        if args.list_tools or args.raw_tools:
            tools_data = mcp.list_tools()
            if args.raw_tools:
                print_banner("RAW TOOLS JSON")
                print(pretty_json(tools_data))
            else:
                print_tools_summary(tools_data)

        if args.tool:
            result = mcp.call_tool(args.tool, tool_args)
            print_tool_call_response(args.tool, result)

        if args.run_examples:
            demo_examples(mcp)

        if not any([args.list_tools, args.raw_tools, args.tool, args.run_examples]):
            print_banner("QUICK START")
            print("Connected successfully.")
            print("Try one of these:")
            print("  --list-tools")
            print('  --tool institution_ranking --args \'{"mode":"global","limit":5}\'')
            print("  --run-examples")

        return 0

    except MCPError as e:
        print(f"\n[MCP ERROR]\n{e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    finally:
        mcp.close()


if __name__ == "__main__":
    raise SystemExit(main())
