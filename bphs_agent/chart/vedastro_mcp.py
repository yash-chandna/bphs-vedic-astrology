"""
VedAstro MCP client — connects to https://mcp-subagent.vedastro.org/api/mcp/public
and calls its tools from within our Python agent.

Supplements the REST client for:
- get_context_based_astrology_data: natural-language → any of 640+ calculations
- search_calculate_methods: discover available endpoints by keyword
- get_horoscope_predictions: bulk life predictions (used as supplementary data only;
  interpretation is still done by our BPHS skills, not accepted verbatim)

Auth: API key passed as Bearer token (StreamableHTTP transport).
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from bphs_agent import config

MCP_URL = "https://mcp-subagent.vedastro.org/api/mcp/public"


def _headers() -> dict[str, str]:
    h = {"Content-Type": "application/json"}
    if config.VEDASTRO_API_KEY:
        h["Authorization"] = f"Bearer {config.VEDASTRO_API_KEY}"
        h["x-api-key"] = config.VEDASTRO_API_KEY
    return h


def _birth_args(birth) -> dict:
    """Convert BirthData to the flat args VedAstro MCP tools expect."""
    from bphs_agent.chart.models import BirthData
    b: BirthData = birth
    # VedAstro MCP accepts: date DD/MM/YYYY, time HH:MM, latitude, longitude, timezone +HH:MM
    return {
        "date": b.date,
        "time": b.time,
        "latitude": b.latitude,
        "longitude": b.longitude,
        "timezone": b.timezone,
    }


def _call_tool(tool_name: str, arguments: dict) -> Any:
    """
    Call a VedAstro MCP tool via StreamableHTTP (synchronous wrapper).
    VedAstro MCP uses JSON-RPC 2.0 over HTTP POST.
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments,
        },
    }
    resp = httpx.post(MCP_URL, headers=_headers(), json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        raise RuntimeError(f"VedAstro MCP error ({tool_name}): {data['error']}")

    result = data.get("result", {})
    # MCP tool results are in result.content — list of {type, text} blocks
    content = result.get("content", [])
    if content and isinstance(content, list):
        return content[0].get("text", "")
    return result


def get_context_data(birth, query: str) -> str:
    """
    Plain-English query → VedAstro routes to the right calculation automatically.
    E.g. query = "What is the Shadbala of Jupiter?"
    Returns raw text result.
    """
    args = _birth_args(birth)
    args["query"] = query
    return _call_tool("get_context_based_astrology_data", args)


def get_horoscope_predictions(birth) -> str:
    """
    200+ life predictions from VedAstro.
    NOTE: We use these as supplementary raw data only — our BPHS skills do the
    interpretation. We do NOT pass VedAstro's interpretations directly to the user.
    """
    args = _birth_args(birth)
    return _call_tool("get_horoscope_predictions", args)


def search_methods(keyword: str) -> str:
    """Discover available VedAstro calculation methods by keyword."""
    return _call_tool("search_calculate_methods", {"query": keyword})


def search_bphs_mcp(query: str, top_k: int = 5) -> list[dict]:
    """
    Search BPHS text via VedAstro MCP's context tool.
    Returns list of {text, page, score} dicts (same shape as retriever.BPHSPassage).
    Falls back to empty list on error.
    """
    try:
        raw = _call_tool("get_context_based_astrology_data", {
            "query": f"BPHS says: {query}",
            "date": "01/01/2000", "time": "12:00",
            "latitude": 0.0, "longitude": 0.0, "timezone": "+00:00",
        })
        # VedAstro returns plain text; wrap it as a single passage
        if raw and isinstance(raw, str) and len(raw) > 20:
            return [{"text": raw, "page": 0, "score": 1.0}]
    except Exception:
        pass
    return []


def is_available() -> bool:
    """Quick connectivity check — returns True if VedAstro MCP responds."""
    try:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        resp = httpx.post(MCP_URL, headers=_headers(), json=payload, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False
