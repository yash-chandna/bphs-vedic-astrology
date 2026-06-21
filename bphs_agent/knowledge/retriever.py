"""
BPHS knowledge retrieval — two-tier:

1. Hardcoded rules (bphs_rules/) — zero latency, zero cost; grows over time.
2. VedAstro SearchSourceText API — fallback when rules don't cover the topic.
   Results are returned AND optionally written back to the rules file
   so they become hardcoded on the next lookup.

Design intent: steadily reduce dependence on the API as the rules grow.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

import httpx

from bphs_agent import config

VEDASTRO_SEARCH_URL = (
    "https://api.vedastro.org/api/Calculate/SearchSourceText"
    "/Query/{query}/TopK/{k}/SourceName/Brihat-Parashara-Hora-Shastra"
)

RULES_DIR = Path(__file__).parent / "bphs_rules"
LEARNED_FILE = RULES_DIR / "learned.py"


@dataclass
class BPHSPassage:
    text: str
    page: int
    score: float
    source: str = "VedAstro/BPHS"

    def formatted(self) -> str:
        return f"[BPHS p.{self.page}, score={self.score:.2f}]\n{self.text.strip()}"


def search_bphs(query: str, k: int = 5) -> list[BPHSPassage]:
    """
    Query VedAstro's pre-indexed BPHS (text-embedding-3-small).
    Returns up to k passages ordered by relevance.
    Free tier: 5 searches/minute. Retries once on 429.
    """
    import time as _time

    url = VEDASTRO_SEARCH_URL.format(query=quote(query), k=k)
    headers = {}
    if config.VEDASTRO_API_KEY:
        headers["x-api-key"] = config.VEDASTRO_API_KEY

    for attempt in range(2):
        resp = httpx.get(url, headers=headers, timeout=20)
        if resp.status_code == 429:
            _time.sleep(15)   # back off and retry once
            continue
        resp.raise_for_status()
        break

    data = resp.json()

    if data.get("Status") != "Pass":
        return []

    passages = []
    for item in data.get("Payload", []):
        passages.append(
            BPHSPassage(
                text=item.get("text", ""),
                page=item.get("page", 0),
                score=item.get("score", 0.0),
            )
        )
    return passages


def format_passages_for_prompt(passages: list[BPHSPassage]) -> str:
    """Format passages as a block for insertion into a skill system prompt."""
    if not passages:
        return ""
    lines = ["--- BPHS SOURCE PASSAGES (via VedAstro) ---"]
    for i, p in enumerate(passages, 1):
        lines.append(f"\n[{i}] {p.formatted()}")
    lines.append("\n--- END OF BPHS PASSAGES ---")
    return "\n".join(lines)


def learn_and_encode(topic_key: str, passages: list[BPHSPassage]) -> None:
    """
    Permanently encode retrieved BPHS passages into learned.py so they become
    hardcoded on the next lookup. Call this after receiving API results.

    topic_key: a short snake_case key, e.g. "saturn_7th_house"
    """
    if not passages:
        return

    # Load existing learned entries
    learned: dict[str, list[dict]] = {}
    if LEARNED_FILE.exists():
        namespace: dict = {}
        exec(LEARNED_FILE.read_text(encoding="utf-8"), namespace)  # noqa: S102
        learned = namespace.get("LEARNED", {})

    if topic_key in learned:
        return  # already encoded — do not overwrite

    learned[topic_key] = [
        {"text": p.text, "page": p.page, "score": p.score} for p in passages
    ]

    # Write back as a Python literal (human-readable, editable)
    lines = [
        '"""',
        "Auto-encoded BPHS passages learned via VedAstro SearchSourceText.",
        "Each key is a topic; each value is a list of {text, page, score} dicts.",
        "Edit or extend these entries freely — they take precedence over API lookups.",
        '"""',
        "",
        f"LEARNED: dict[str, list[dict]] = {json.dumps(learned, indent=2, ensure_ascii=False)}",
        "",
    ]
    LEARNED_FILE.write_text("\n".join(lines), encoding="utf-8")


def get_learned(topic_key: str) -> list[BPHSPassage] | None:
    """
    Return hardcoded passages for a topic if already learned, else None.
    None signals the caller to fall back to the API and then call learn_and_encode.
    """
    if not LEARNED_FILE.exists():
        return None
    namespace: dict = {}
    exec(LEARNED_FILE.read_text(encoding="utf-8"), namespace)  # noqa: S102
    learned: dict = namespace.get("LEARNED", {})
    entries = learned.get(topic_key)
    if not entries:
        return None
    return [BPHSPassage(text=e["text"], page=e["page"], score=e["score"]) for e in entries]


def get_or_fetch(topic_key: str, query: str, k: int = 5) -> list[BPHSPassage]:
    """
    Preferred entry point for skills:
    1. Check learned.py (hardcoded) → return immediately if found.
    2. Try VedAstro REST SearchSourceText.
    3. If REST fails/empty, try VedAstro MCP search_bphs_mcp.
    4. Encode result into learned.py for future requests.
    5. Return passages.
    """
    cached = get_learned(topic_key)
    if cached:
        return cached

    passages = search_bphs(query, k=k)

    if not passages:
        # Fallback to MCP
        try:
            from bphs_agent.chart.vedastro_mcp import search_bphs_mcp
            mcp_results = search_bphs_mcp(query)
            passages = [
                BPHSPassage(text=r["text"], page=r["page"], score=r["score"])
                for r in mcp_results
            ]
        except Exception:
            pass

    if passages:
        learn_and_encode(topic_key, passages)
    return passages
