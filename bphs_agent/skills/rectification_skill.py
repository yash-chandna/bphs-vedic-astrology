"""
RectificationSkill — BPHS-driven mechanical birth time rectification.

The engine (chart/rectification.py) sweeps the birth day, derives the Vimshottari
dasha tree for each candidate minute, and scores each candidate by checking whether
known life events fall in the dasha period of the BPHS-prescribed house lord.

The LLM is called only once, after the sweep, to interpret the top candidates
against BPHS appearance descriptions (Ch. 6–8) and recommend the best window.
"""

from __future__ import annotations

from bphs_agent.chart.models import ChartData
from bphs_agent.chart.rectification import CandidateTime, LifeEvent, find_birth_time
from bphs_agent.skills.base_skill import BaseSkill, SkillResult, Finding, CITATION_INSTRUCTION, claude_call


class RectificationSkill(BaseSkill):
    SKILL_NAME = "Birth Time Rectification"
    RELEVANT_TOPIC_KEYS = ["birth_time_rectification_lagna", "vimshottari_dasha_balance"]
    RELEVANT_QUERIES = [
        "birth time rectification Vimshottari dasha balance BPHS Ch 46",
        "Moon nakshatra dasha balance rectification BPHS",
    ]

    def __init__(
        self,
        events: list[LifeEvent] | None = None,
        known_lagna: str | None = None,
    ) -> None:
        self.events = events or []
        self.known_lagna = known_lagna

    def _system_prompt(self, passages_block: str) -> str:
        return f"""You are a Jyotishi interpreting mechanical birth time rectification results (BPHS Ch. 46).

{CITATION_INSTRUCTION}

The candidate birth times were computed by sweeping pyswisseph over the birth date,
building Vimshottari dasha trees, and scoring each minute against life events using
BPHS house-lord rules.  Do NOT recompute or second-guess the mechanical results.

Your job:
1. For each candidate lagna sign, cite the BPHS description of that rising sign's
   physical appearance and nature (Ch. 6–8). State whether it plausibly fits the native.
2. Comment on the lagna lord's strength (sign, house, dignity) in each candidate.
3. If multiple lagnas score equally, name one further life event (with its expected
   house lord per BPHS Ch. 11–15) that would distinguish between them.
4. Give a single recommended birth time window with your reasoning.

{passages_block}
"""

    def _build_user_message(self, chart: ChartData, query: str | None) -> str:
        return ""  # not used — run() calls _llm_interpret directly

    def run(self, chart: ChartData, query: str | None = None) -> SkillResult:
        # ── 1. Mechanical sweep ───────────────────────────────────────────────
        candidates = find_birth_time(
            chart.birth,
            self.events,
            known_lagna=self.known_lagna,
            min_score=1.0,
        )
        if not candidates:
            candidates = find_birth_time(
                chart.birth,
                self.events,
                known_lagna=self.known_lagna,
                min_score=0.0,
            )

        findings: list[Finding] = []
        unverified: list[str] = []

        if not candidates:
            unverified.append("No candidate birth times found. Check event dates and types.")
            return SkillResult(skill_name=self.SKILL_NAME, findings=findings, unverified=unverified)

        # ── 2. Emit per-event constraint findings ─────────────────────────────
        from bphs_agent.chart.rectification import EVENT_HOUSES, _house_lord
        for e in self.events:
            if e.event_type in EVENT_HOUSES:
                ph, sh, karaka = EVENT_HOUSES[e.event_type]
                findings.append(Finding(
                    statement=(
                        f"'{e.description}' on {e.event_date}: BPHS assigns this to "
                        f"house {ph} (lord varies by lagna) + natural karaka {karaka}. "
                        f"Expected dasha lord = house {ph} lord per BPHS Ch. 11–15."
                    ),
                    bphs_citation="BPHS Ch. 11",
                ))

        # ── 3. Emit candidate windows ─────────────────────────────────────────
        windows = _lagna_windows(candidates)
        for w in windows:
            best = w[0]
            time_range = f"{w[0].local_time}–{w[-1].local_time}" if len(w) > 1 else w[0].local_time
            per_event = "; ".join(
                f"{self.events[i].event_type}={s:.2f}"
                for i, s in enumerate(best.event_scores)
            ) if self.events else "no events"
            findings.append(Finding(
                statement=(
                    f"Candidate {time_range} | Lagna: {best.lagna_sign} | "
                    f"Moon {best.moon_lon:.3f}° {best.moon_nakshatra} "
                    f"(lord: {best.moon_nakshatra_lord}) | "
                    f"Dasha balance at birth: {best.dasha_balance} | "
                    f"Score: {best.total_score:.2f} ({per_event})"
                ),
                bphs_citation="BPHS Ch. 46",
            ))

        # ── 4. LLM interpretation of top candidates ───────────────────────────
        passages_block = self._fetch_passages()
        narrative = self._llm_interpret(chart, candidates, passages_block, query)
        for line in narrative.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("[BPHS"):
                bracket_end = line.index("]")
                citation = line[1:bracket_end]
                findings.append(Finding(statement=line[bracket_end + 1:].strip(), bphs_citation=citation))
            elif line.startswith("[UNVERIFIED]"):
                unverified.append(line[len("[UNVERIFIED]"):].strip())
            else:
                unverified.append(line)

        return SkillResult(skill_name=self.SKILL_NAME, findings=findings, unverified=unverified)

    def _llm_interpret(
        self,
        chart: ChartData,
        candidates: list[CandidateTime],
        passages_block: str,
        query: str | None,
    ) -> str:
        # Deduplicate to one representative per lagna window
        seen: set[str] = set()
        top: list[CandidateTime] = []
        for c in candidates:
            if c.lagna_sign not in seen:
                seen.add(c.lagna_sign)
                top.append(c)
            if len(top) == 5:
                break

        lines = [
            f"Native: {chart.birth.name}",
            f"Birth date: {chart.birth.date}  Place: {chart.birth.place}",
            "",
            "CANDIDATE WINDOWS (computed mechanically):",
        ]
        for i, c in enumerate(top, 1):
            lines.append(
                f"  [{i}] {c.local_time} | Lagna: {c.lagna_sign} | "
                f"Moon {c.moon_lon:.3f}° {c.moon_nakshatra} | "
                f"Dasha balance: {c.dasha_balance} | Score: {c.total_score:.2f}"
            )

        if self.events:
            lines += ["", "LIFE EVENTS (constraints used):"]
            from bphs_agent.chart.rectification import EVENT_HOUSES
            for e in self.events:
                ph = EVENT_HOUSES.get(e.event_type, (None,))[0]
                lines.append(
                    f"  {e.event_date}: {e.description} "
                    f"(type={e.event_type}, BPHS primary house={ph})"
                )

        if query:
            lines += ["", f"User question: {query}"]

        lines += ["", "Analyse per BPHS Ch. 6–8. Cite every statement with [BPHS Ch.X]."]

        return claude_call(self._system_prompt(passages_block), "\n".join(lines), max_tokens=1024)


def _lagna_windows(candidates: list[CandidateTime]) -> list[list[CandidateTime]]:
    """Group consecutive same-lagna candidates (already sorted by local_time)."""
    if not candidates:
        return []
    by_time = sorted(candidates, key=lambda c: c.local_time)
    windows: list[list[CandidateTime]] = []
    cur = [by_time[0]]
    for c in by_time[1:]:
        if c.lagna_sign == cur[0].lagna_sign:
            cur.append(c)
        else:
            windows.append(cur)
            cur = [c]
    windows.append(cur)
    return windows
