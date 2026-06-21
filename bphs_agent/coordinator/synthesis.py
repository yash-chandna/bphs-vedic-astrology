"""
Synthesis — final Claude pass that converts all skill results into a
cohesive narrative reading.

The synthesiser's job is PROSE, not new analysis. It must not add any
interpretation beyond what the skills have already cited from BPHS.
"""

from __future__ import annotations

import subprocess

from bphs_agent.chart.models import ChartData
from bphs_agent.coordinator.orchestrator import OrchestratorResult
from bphs_agent.skills.base_skill import claude_call

_SYNTHESIS_SYSTEM = """
You are a senior Jyotishi writing the final reading for a client.

Your ONLY job is to weave the provided BPHS-cited skill findings into clear,
readable prose. You must NOT:
- Add any new interpretation not already present in the provided findings.
- Introduce yogas, dashas, or planetary effects not listed in the findings.
- Soften negative findings to appease the native.
- Invent or estimate BPHS citations — only use citations already in the findings.

Structure your response as:

## Chart Overview
(Lagna, Moon sign, overall chart signature — 2–3 sentences)

## Planetary Strengths
(Which planets are strong/weak and what that means for the reading)

## Key Yogas
(Only yogas that were BPHS-verified in the findings)

## Life Areas
(Group findings by life area: career, relationships, health, finances, spirituality, etc.)

## Current Period (Dasha)
(Mahadasha + Bhukti interpretation and what the next few years indicate)

## Divisional Chart Highlights
(D9 and any other divisionals analysed)

## Summary
(2–3 sentence honest summary of what the chart shows — strengths AND challenges)

Each statement must remain traceable to a [BPHS Ch.X] or [BPHS p.N] citation
from the findings. Do not add new citations.
"""


def synthesise(
    chart: ChartData,
    orchestrator_result: OrchestratorResult,
    query: str | None = None,
    stream: bool = False,
) -> str:
    """
    Run the synthesis pass.

    Args:
        chart: The birth chart (used for context only).
        orchestrator_result: All skill results from the orchestrator.
        query: Original user query (if any) to keep synthesis focused.
        stream: If True, stream to stdout and return full text at end.

    Returns:
        Full reading as a string.
    """
    cited_block = orchestrator_result.cited_block()
    unverified_count = len(orchestrator_result.all_unverified)

    user_content = f"""Native: {chart.birth.name}
Born: {chart.birth.date} {chart.birth.time} in {chart.birth.place}
Lagna: {chart.general.lagna_sign if chart.general else "Unknown"}
Moon Sign: {chart.general.moon_sign if chart.general else "Unknown"}
Moon Nakshatra: {chart.general.moon_nakshatra if chart.general else "Unknown"}

{f"User question: {query}" if query else ""}

--- SKILL FINDINGS (BPHS-cited only) ---

{cited_block}

--- END OF FINDINGS ---

Note: {unverified_count} unverified statement(s) were excluded from this reading.
Write the synthesis based solely on the findings above.
"""

    if stream:
        # Stream via claude -p with --output-format stream-json, falling back to plain text
        proc = subprocess.Popen(
            [
                "claude", "-p", user_content,
                "--system-prompt", _SYNTHESIS_SYSTEM,
                "--output-format", "text",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        full_text = ""
        for chunk in proc.stdout:
            print(chunk, end="", flush=True)
            full_text += chunk
        proc.wait()
        print()
        return full_text.strip()
    else:
        return claude_call(_SYNTHESIS_SYSTEM, user_content, max_tokens=4096)
