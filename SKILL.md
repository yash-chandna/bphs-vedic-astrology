---
name: bphs-vedic-astrology
description: >
  Full Vedic astrology readings and matchmaking strictly based on Brihat Parashara Hora Shastra (BPHS), with a self-growing knowledge base. Use this skill whenever the user wants a birth chart reading, Jyotish analysis, planetary analysis, yoga identification, dasha periods, navamsha/divisional chart analysis, ashtakvarga, transit analysis, birth time rectification, astrocartography, or marriage compatibility (kundali milan / matchmaking). Trigger on any mention of Vedic astrology, birth chart, kundali, lagna, rashi, nakshatra, dasha, graha, bhava, yoga (Jyotish context), Jyotish, BPHS, or any compatibility/matchmaking request involving birth data. Also trigger if the user asks to inspect, extend, or query the BPHS knowledge database. Even if the user just provides a birth date, time, and place without naming the system, use this skill.
---

# BPHS Vedic Astrology Skill

Strict BPHS-based multi-agent astrology system with a self-growing knowledge database. Every statement must cite a BPHS chapter/sloka. The system gets smarter with each use because newly fetched passages are permanently stored locally.

## Reference files

Read these when you need knowledge for a specific domain — don't load all of them upfront:

| File | When to read |
|---|---|
| `references/planets.md` | Planetary dignities, aspects, relationships, karakatva |
| `references/houses.md` | Bhava significations, classifications, karakas |
| `references/yogas.md` | Raja, Dhana, Arista, Nabhasa, Chandra yoga rules |
| `references/dasha.md` | Vimshottari sequence, nakshatra lords, phala principles |
| `references/shadbala.md` | Six balas, minimum thresholds, Ishta/Kashta Phala |
| `references/divisionals.md` | 16 Shodashavarga charts, Navamsa rules, Varga Visesha |
| `references/matchmaking.md` | Ashtakoot Guna Milan, Mangal Dosha, chart compatibility |

---

## The Knowledge Database: `learned.py`

`bphs_agent/knowledge/bphs_rules/learned.py` is the system's persistent, growing knowledge base — source-controlled and never to be deleted.

### How it works

Every time a skill encounters a topic not already known, it fetches the relevant BPHS passages from VedAstro and **permanently writes them into `learned.py`**. The next time that topic appears, the system reads locally — instantly, for free.

```python
LEARNED: dict[str, list[dict]] = {
  "lagna_lord_effects": [
    {"text": "...", "page": 42, "score": 0.93},
  ],
  "saturn_7th_house": [...],
}
```

### Lookup hierarchy (checked in this order)

1. **Hardcoded rules** (`references/*.md` + `bphs_rules/planets.py` etc.) — highest authority
2. **`learned.py`** — permanently encoded passages from past sessions; BPHS rules trump these if they conflict
3. **VedAstro REST API** — live semantic search over the full BPHS text
4. **VedAstro MCP** — fallback if REST is unavailable

Entry point for all lookups: `knowledge/retriever.get_or_fetch(topic_key, query)` — walks the hierarchy and writes back to `learned.py` automatically.

### Inspecting the knowledge base

```python
from bphs_agent.knowledge.retriever import get_learned
passages = get_learned("saturn_7th_house")  # None if not yet learned
```

To manually enrich `learned.py`, edit it directly — it's a plain Python dict. Format:
```python
"my_topic_key": [{"text": "BPHS passage", "page": 214, "score": 1.0}]
```

To pre-warm topics before a reading:
```python
from bphs_agent.knowledge.retriever import get_or_fetch
get_or_fetch("moon_in_scorpio", "Moon placed in Scorpio sign effects BPHS")
```

---

## Setup (one-time)

```bash
cd C:\Users\YASHC\OneDrive\Desktop\BPHS
pip install -r requirements.txt
```

Optional: set `VEDASTRO_API_KEY` in `.env` for faster fetches. No `ANTHROPIC_API_KEY` needed except for `/image`.

---

## Skill Categories

### Category 1 — Birth Chart Reading

A full reading runs all skills in BPHS sequence: Shadbala → Lagna → Planets → Houses → Yogas → Divisionals → Ashtakvarga → Dasha → optional Transits.

**CLI:**
```bash
python -m bphs_agent
/load <name> <date> <time> <place>   # e.g. /load Arjun 1990-07-15 14:30 Mumbai
/full                                 # complete reading
```

**Python API:**
```python
from bphs_agent.chart.client import fetch_chart
from bphs_agent.coordinator.orchestrator import run_full_reading
from bphs_agent.coordinator.synthesis import synthesise

chart = fetch_chart(name="Arjun", dob="1990-07-15", tob="14:30", place="Mumbai")
result = run_full_reading(chart)
print(synthesise(result.all_findings, chart))
```

### Category 2 — Targeted Analysis

Ask about a specific topic rather than a full reading:

| Topic | CLI command | Reference |
|---|---|---|
| Ascendant & lagna lord | `/question lagna` | `references/houses.md` |
| Planet-by-planet | `/question planet` | `references/planets.md` |
| Bhava (house) analysis | `/question house` | `references/houses.md` |
| Planetary strength | `/question strength` | `references/shadbala.md` |
| Yoga identification | `/question yoga` | `references/yogas.md` |
| Navamsha / D9 | `/question navamsha` | `references/divisionals.md` |
| Ashtakvarga bindus | `/question ashtakvarga` | `references/shadbala.md` |

### Category 3 — Timing & Transits

| Topic | CLI command | Reference |
|---|---|---|
| Vimshottari Dasha periods | `/dasha` | `references/dasha.md` |
| Gochar (transit) analysis | `/transits` | — |
| Birth time rectification | `/rectify` | — |

### Category 4 — Location & Special

| Topic | CLI command |
|---|---|
| Astrocartography / relocation | `/astrocartography` |
| Chart from image (North Indian) | `/image <path>` (requires `ANTHROPIC_API_KEY`) |

### Category 5 — Matchmaking (Kundali Milan)

Read `references/matchmaking.md` for the full system. Covers:
- Ashtakoot Guna Milan (8 factors, score /36)
- Mangal Dosha assessment
- 7th house & karaka analysis across both charts
- Navamsa (D9) comparison
- Dasha timing for marriage

```bash
/load Person1 1992-03-15 09:20 Delhi
/load Person2 1993-07-22 14:45 Mumbai
/match Person1 Person2
```

---

## Citation enforcement

Every output line must be prefixed `[BPHS Ch.X, Sl.Y]` or `[BPHS p.N]`. Lines marked `[UNVERIFIED]` are stripped before synthesis. This is the system's core quality gate.

---

## Architecture

```
User → CLI / API
     → chart.client  → VedAstro API → ChartData
     → Orchestrator  → Skills (BPHS sequence)
          ↓ each skill calls get_or_fetch()
          → learned.py (hit) → return instantly
          → VedAstro API (miss) → encode into learned.py → return
     → Synthesis     → cited prose reading
```

All LLM calls run `claude -p` via subprocess. See `CLAUDE.md` for developer docs.

---

## Adding a new skill

1. Create `bphs_agent/skills/my_skill.py` subclassing `BaseSkill`
2. Define `SKILL_NAME`, `RELEVANT_TOPIC_KEYS`, `RELEVANT_QUERIES`, `_system_prompt()`, `_build_user_message()`
3. Call `get_or_fetch(topic_key, query)` in `run()` to fetch BPHS passages — this populates `learned.py` automatically
4. Register in `coordinator/orchestrator.py` and add keyword triggers in `_infer_skills()`
5. Add a corresponding reference markdown file in `references/` if the skill introduces new knowledge domains
