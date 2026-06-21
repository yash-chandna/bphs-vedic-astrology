"""
BaseSkill — every sub-agent skill inherits from this.

Contract:
- run(chart, query) → SkillResult
- Every Finding must have a bphs_citation.
- [UNVERIFIED] findings are stored separately and excluded from the final report.
- Skills first use hardcoded rules, then fall back to VedAstro SearchSourceText
  (which encodes results permanently into learned.py).
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from typing import ClassVar

from bphs_agent.chart.models import ChartData
from bphs_agent.knowledge.retriever import format_passages_for_prompt, get_or_fetch

CITATION_INSTRUCTION = """
CRITICAL RULES — you MUST follow these without exception:

1. For every statement you make, prefix it with a citation in this exact format:
   [BPHS Ch.X, Sl.Y] Your statement here.
   or, if page-based:
   [BPHS p.N] Your statement here.

2. If you cannot find a BPHS citation for a statement, prefix it with:
   [UNVERIFIED] Your statement here.
   Do NOT omit the prefix. Do NOT mix cited and uncited content in the same sentence.

3. NEVER add interpretations to appease the native. Only state what the chart
   and the BPHS text explicitly support. If the chart shows difficulty, say so.
   If it shows nothing remarkable, say so.

4. NEVER invent sloka numbers. If you don't know the exact sloka, use
   [BPHS Ch.X] (chapter only) or [BPHS p.N] (page number from source passages).

5. You are a Jyotishi trained exclusively in BPHS (Brihat Parashara Hora Shastra).
   You do not use other shastra, Jaimini, KP, or Western methods.
"""


@dataclass
class Finding:
    statement: str
    bphs_citation: str      # e.g. "BPHS Ch.36, Sl.4" or "BPHS p.214"
    is_verified: bool = True


@dataclass
class SkillResult:
    skill_name: str
    findings: list[Finding] = field(default_factory=list)
    unverified: list[str] = field(default_factory=list)
    raw_response: str = ""

    def cited_summary(self) -> str:
        """All verified findings as a formatted block for the synthesis pass."""
        if not self.findings:
            return f"[{self.skill_name}] No BPHS-verified findings for this chart."
        lines = [f"=== {self.skill_name} ==="]
        for f in self.findings:
            lines.append(f"[{f.bphs_citation}] {f.statement}")
        return "\n".join(lines)


def _parse_response(skill_name: str, text: str) -> SkillResult:
    """
    Parse the model's response into SkillResult.
    Expects each line to be prefixed with [BPHS ...] or [UNVERIFIED].
    """
    findings: list[Finding] = []
    unverified: list[str] = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("[UNVERIFIED]"):
            unverified.append(line[len("[UNVERIFIED]"):].strip())
        elif line.startswith("[BPHS"):
            bracket_end = line.index("]")
            citation = line[1:bracket_end]
            statement = line[bracket_end + 1:].strip()
            findings.append(Finding(statement=statement, bphs_citation=citation, is_verified=True))
        else:
            # Model forgot to prefix — treat as unverified
            unverified.append(line)

    return SkillResult(
        skill_name=skill_name,
        findings=findings,
        unverified=unverified,
        raw_response=text,
    )


def claude_call(system: str, user: str, max_tokens: int = 2048) -> str:
    """
    Call Claude via the `claude -p` CLI (no API key required — uses Claude Code auth).
    Raises RuntimeError if the call fails.
    """
    result = subprocess.run(
        [
            "claude", "-p", user,
            "--system-prompt", system,
            "--output-format", "text",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude -p failed: {result.stderr.strip()}")
    return result.stdout.strip()


class BaseSkill:
    """
    Each sub-agent skill subclasses this.

    Subclasses must define:
        SKILL_NAME: str
        RELEVANT_TOPIC_KEYS: list[str]  — keys for the retriever
        RELEVANT_QUERIES: list[str]     — queries to send to SearchSourceText
        _build_user_message(chart, query) -> str
    """

    SKILL_NAME: ClassVar[str] = "BaseSkill"
    RELEVANT_TOPIC_KEYS: ClassVar[list[str]] = []
    RELEVANT_QUERIES: ClassVar[list[str]] = []

    def _system_prompt(self, passages_block: str) -> str:
        raise NotImplementedError

    def _build_user_message(self, chart: ChartData, query: str | None) -> str:
        raise NotImplementedError

    def _fetch_passages(self) -> str:
        """Fetch all relevant BPHS passages for this skill (hardcoded first, then API)."""
        all_passages = []
        for key, query in zip(self.RELEVANT_TOPIC_KEYS, self.RELEVANT_QUERIES):
            passages = get_or_fetch(key, query, k=5)
            all_passages.extend(passages)
        return format_passages_for_prompt(all_passages) if all_passages else ""

    def run(self, chart: ChartData, query: str | None = None) -> SkillResult:
        passages_block = self._fetch_passages()
        system = self._system_prompt(passages_block)
        user_msg = self._build_user_message(chart, query)
        text = claude_call(system, user_msg)
        return _parse_response(self.SKILL_NAME, text)
