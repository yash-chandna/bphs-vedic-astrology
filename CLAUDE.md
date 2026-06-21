# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the agent

```bash
# Install dependencies
pip install -r requirements.txt

# Run the interactive CLI
python -m bphs_agent
```

No `ANTHROPIC_API_KEY` is required for normal use — all skill and synthesis LLM calls go through the `claude` CLI (Claude Code), which handles auth automatically. Optionally copy `.env.example` to `.env` and set `VEDASTRO_API_KEY` for the VedAstro data source, and `ANTHROPIC_API_KEY` only if you use the `/image` chart reader (vision).

## Architecture

This is a multi-agent Vedic astrology system strictly based on Brihat Parashara Hora Shastra (BPHS). The data flow is:

```
User input → CLI (interfaces/cli.py)
           → chart.client  → VedAstro API → ChartData (chart/models.py)
           → Orchestrator  → Skills (parallel analysis)
           → Synthesis     → final prose reading
```

### Key layers

**`chart/`** — Data acquisition and models
- `models.py`: `ChartData` is the central data object passed everywhere. Contains `BirthData`, `PlanetData` (keyed by name), `HouseData` (keyed by 1–12), `AshtakvargaData`, `DashaData`, and nested `divisionals` dict.
- `client.py`: Fetches from VedAstro REST API and populates `ChartData`.
- `image_reader.py`: Extracts chart data from North Indian chart images via Claude vision (**requires `ANTHROPIC_API_KEY`** — vision calls cannot go through `claude -p`).
- `ephemeris.py`: Direct ephemeris calculations via `pyswisseph`.
- `vedastro_mcp.py`: MCP-based fallback for VedAstro queries.

**`skills/`** — Sub-agent skill modules (one per astrological topic)
- All inherit from `base_skill.BaseSkill`.
- `BaseSkill.run(chart, query) → SkillResult` calls `claude_call()` from `base_skill.py`, which runs `claude -p` as a subprocess — no API key needed.
- Every `Finding` must carry a `bphs_citation`. Lines prefixed `[UNVERIFIED]` are excluded from the final reading.
- Skills first check `knowledge/retriever.get_or_fetch()` for BPHS passages before calling the LLM.

**`coordinator/`** — Orchestration and synthesis
- `orchestrator.py`: `run_full_reading()` runs all 9 skills in BPHS-prescribed sequence (Shadbala → Lagna → Planets → Houses → Yogas → Divisionals → Ashtakvarga → Dasha → optional Transits/Astrocartography). `run_targeted()` infers which skills to run from query keywords.
- `synthesis.py`: `synthesise()` takes all `SkillResult`s and calls `claude_call()` to produce prose. Synthesis must not add new interpretations beyond what skills already cited.

**`knowledge/`** — Two-tier BPHS knowledge retrieval
- `retriever.get_or_fetch(topic_key, query)`: checks `bphs_rules/learned.py` first (zero-cost), falls back to VedAstro `SearchSourceText` REST API, then MCP fallback. Results are written back to `learned.py` permanently to reduce future API calls.
- `bphs_rules/`: Static hardcoded rules modules (planets, houses, yogas, dasha, divisionals, shadbala, transits) plus auto-generated `learned.py`.

**`interfaces/`**
- `cli.py`: Interactive REPL. Profiles saved to `~/.bphs_agent/profiles/` as JSON.
- `api.py`: FastAPI wrapper (run with `uvicorn bphs_agent.interfaces.api:app`).

## LLM calls — how they work

All LLM calls go through `skills/base_skill.py::claude_call(system, user)`, which runs:

```python
subprocess.run(["claude", "-p", user, "--system-prompt", system, "--output-format", "text"])
```

This uses the Claude Code CLI's existing authentication — no separate API key. The `claude` binary must be on PATH (it is when running inside Claude Code).

**Exception:** `chart/image_reader.py` uses the Anthropic Python SDK directly for vision (base64 image input), which `claude -p` does not support. This is the only place that requires `ANTHROPIC_API_KEY`.

## Configuration (`.env`)

| Variable | Required | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | Only for `/image` | Vision chart reader |
| `VEDASTRO_API_KEY` | Optional | Faster VedAstro data access |
| `DEFAULT_AYANAMSA` | Optional | Default `LAHIRI` |
| `COORDINATOR_MODEL` | Optional | Model for image reader, default `claude-sonnet-4-6` |

## Citation enforcement

Every statement the LLM produces must be prefixed with `[BPHS Ch.X, Sl.Y]` or `[BPHS p.N]`. Unprefixed lines or `[UNVERIFIED]` lines are parsed out by `base_skill._parse_response()` and excluded from the synthesis input. Do not relax this constraint — it is the core quality gate of the system.

## Skills reference

| Skill | Topic | CLI command |
|---|---|---|
| `LagnaSkill` | Ascendant & lagna lord | `/question lagna` |
| `PlanetSkill` | Planet-by-planet analysis | `/question planet` |
| `HouseSkill` | Bhava analysis | `/question house` |
| `ShabdalaSkill` | Planetary strength ranking | `/question strength` |
| `YogaSkill` | Yoga identification | `/question yoga` |
| `DivisionalSkill` | D9/D10 divisional charts | `/question navamsha` |
| `AshtakvargaSkill` | Ashtakvarga bindus | `/question ashtakvarga` |
| `DashaSkill` | Vimshottari dasha periods | `/dasha` |
| `TransitSkill` | Gochar / transit analysis | `/transits` |
| `RectificationSkill` | Birth time rectification (Janma Kala Shuddhi) | `/rectify` |
| `AstrocartographySkill` | Relocation analysis | `/astrocartography` |
| `ChartImageSkill` | Extract chart from image | `/image` |

## Adding a new skill

1. Create `skills/my_skill.py` subclassing `BaseSkill`.
2. Define `SKILL_NAME`, `RELEVANT_TOPIC_KEYS`, `RELEVANT_QUERIES`, `_system_prompt()`, and `_build_user_message()`.
3. Register it in `coordinator/orchestrator.py` (`skill_map` and optionally `run_full_reading`).
4. Add keyword triggers in `_infer_skills()` if it should be auto-selected.
5. LLM calls are handled automatically by `BaseSkill.run()` via `claude_call()` — no API key setup needed.
