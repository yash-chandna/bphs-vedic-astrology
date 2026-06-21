"""
CLI — interactive REPL for the BPHS agent.

Usage:
    python -m bphs_agent

Commands in session:
    /full              — Full BPHS reading for the loaded profile
    /question <text>   — Targeted question (runs relevant skills only)
    /image <path>      — Load chart from a North Indian chart image
    /dasha <YYYY YYYY> — Dasha analysis for a date range (e.g. /dasha 2024 2030)
    /astrocartography <city> <lat> <lon>  — Relocate to a city
    /transits [N]      — Gochar analysis for next N months (default 6)
    /profile           — Show current birth profile
    /new               — Enter a new birth profile
    /rectify           — Birth time rectification (Janma Kala Shuddhi)
    /exit              — Exit
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from bphs_agent.chart.client import get_full_chart, get_dasha, get_divisional_chart
from bphs_agent.chart.models import BirthData
from bphs_agent.coordinator.orchestrator import run_full_reading, run_targeted
from bphs_agent.coordinator.synthesis import synthesise
from bphs_agent.skills.chart_image_skill import ChartImageSkill

PROFILES_DIR = Path.home() / ".bphs_agent" / "profiles"
PROFILES_DIR.mkdir(parents=True, exist_ok=True)


def _prompt_birth_data() -> BirthData:
    print("\n── Enter Birth Details ──────────────────────")
    name = input("Name: ").strip() or "Native"
    date = input("Date of birth (DD/MM/YYYY): ").strip()
    time = input("Time of birth (HH:MM, 24h): ").strip()
    place = input("Place of birth (city name): ").strip()
    lat = float(input("Latitude (e.g. 19.0760 for Mumbai): ").strip())
    lon = float(input("Longitude (e.g. 72.8777 for Mumbai): ").strip())
    tz = input("Timezone offset (e.g. +05:30): ").strip()
    ayan = input("Ayanamsa (LAHIRI/RAMAN, default LAHIRI): ").strip().upper() or "LAHIRI"
    return BirthData(name=name, date=date, time=time, place=place,
                     latitude=lat, longitude=lon, timezone=tz, ayanamsa=ayan)


def _save_profile(birth: BirthData) -> None:
    path = PROFILES_DIR / f"{birth.name.replace(' ', '_')}.json"
    path.write_text(json.dumps(birth.__dict__, indent=2), encoding="utf-8")
    print(f"Profile saved: {path}")


def _load_or_prompt() -> BirthData:
    profiles = sorted(PROFILES_DIR.glob("*.json"))
    if profiles:
        print("\nSaved profiles:")
        for i, p in enumerate(profiles):
            print(f"  [{i+1}] {p.stem}")
        print(f"  [n] Enter new profile")
        choice = input("Select: ").strip().lower()
        if choice == "n":
            birth = _prompt_birth_data()
            _save_profile(birth)
            return birth
        try:
            idx = int(choice) - 1
            data = json.loads(profiles[idx].read_text(encoding="utf-8"))
            return BirthData(**data)
        except (ValueError, IndexError):
            pass
    birth = _prompt_birth_data()
    _save_profile(birth)
    return birth


def _skill_progress(skill_name: str, result) -> None:
    n_found = len(result.findings)
    n_unver = len(result.unverified)
    print(f"  ✓ {skill_name}: {n_found} BPHS findings" +
          (f" ({n_unver} unverified, excluded)" if n_unver else ""))


def main() -> None:
    print("═" * 60)
    print("  BPHS Vedic Astrology Agent")
    print("  Strictly per Brihat Parashara Hora Shastra")
    print("═" * 60)

    birth = _load_or_prompt()
    print(f"\nLoaded: {birth.name} — {birth.date} {birth.time} {birth.place}")
    print("Fetching chart from VedAstro…")
    chart = get_full_chart(birth)
    print(f"Chart loaded. Lagna: {chart.general.lagna_sign if chart.general else 'unknown'}")
    print("\nType a question, or use /full /question /transits /image /dasha /astrocartography /exit\n")

    while True:
        try:
            user_input = input("▶ ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("/exit", "/quit", "exit", "quit"):
            print("Bye.")
            break

        elif user_input.lower() == "/full":
            print("\nRunning full BPHS reading…\n")
            orch_result = run_full_reading(chart, on_skill_done=_skill_progress)
            print("\n" + "─" * 60 + "\n")
            synthesise(chart, orch_result, stream=True)
            print("\n" + "─" * 60)

        elif user_input.lower().startswith("/question "):
            q = user_input[10:].strip()
            print(f"\nRunning targeted analysis for: {q}\n")
            orch_result = run_targeted(chart, q)
            print()
            synthesise(chart, orch_result, query=q, stream=True)
            print()

        elif user_input.lower().startswith("/image "):
            path = user_input[7:].strip().strip('"')
            print(f"\nReading chart image: {path}")
            skill = ChartImageSkill()
            try:
                image_chart, image_result = skill.run_image(path, birth)
                print(f"Extracted: {len(image_chart.planets)} planets, lagna={image_result.findings[0].statement if image_result.findings else '?'}")
                # Replace working chart with image-based chart
                chart = image_chart
                print("Chart updated from image. Use /full or /question to read it.")
            except Exception as e:
                print(f"Error reading image: {e}")

        elif user_input.lower().startswith("/transits"):
            parts = user_input.split()
            months = int(parts[1]) if len(parts) > 1 else 6
            print(f"\nFetching current transits + {months}-month outlook…\n")
            from bphs_agent.skills.transit_skill import TransitSkill
            orch_result = run_targeted(chart, f"transit gochar next {months} months", skill_names=["TransitSkill"])
            print()
            synthesise(chart, orch_result, query="Gochar transit analysis", stream=True)
            print()

        elif user_input.lower().startswith("/dasha"):
            parts = user_input.split()
            start_y = parts[1] if len(parts) > 1 else None
            end_y = parts[2] if len(parts) > 2 else None
            start = f"01/01/{start_y}" if start_y else None
            end = f"31/12/{end_y}" if end_y else None
            print(f"\nFetching dasha periods {start or 'now'} → {end or '+5y'}…")
            dasha = get_dasha(birth, start, end)
            chart.dasha = dasha
            orch_result = run_targeted(chart, "dasha period timing", skill_names=["DashaSkill"])
            synthesise(chart, orch_result, query="Interpret the dasha periods", stream=True)
            print()

        elif user_input.lower().startswith("/astrocartography "):
            parts = user_input.split(None, 3)
            if len(parts) < 4:
                print("Usage: /astrocartography <city> <lat> <lon>")
            else:
                _, place, lat_s, lon_s = parts
                try:
                    from bphs_agent.skills.astrocartography_skill import AstrocartographySkill
                    skill = AstrocartographySkill()
                    sr = skill.run_for_location(chart, place, float(lat_s), float(lon_s))
                    from bphs_agent.coordinator.orchestrator import OrchestratorResult
                    orch = OrchestratorResult(skill_results=[sr])
                    orch.all_findings = [f.statement for f in sr.findings]
                    synthesise(chart, orch, query=f"Relocation to {place}", stream=True)
                    print()
                except Exception as e:
                    print(f"Error: {e}")

        elif user_input.lower() == "/profile":
            print(f"\n{birth.__dict__}")

        elif user_input.lower().startswith("/rectify"):
            from datetime import date as _date
            from bphs_agent.chart.rectification import LifeEvent, EVENT_LABELS
            from bphs_agent.skills.rectification_skill import RectificationSkill
            from bphs_agent.coordinator.orchestrator import OrchestratorResult

            print("\n── Birth Time Rectification (Janma Kala Shuddhi) ────────────")
            print("Enter known life events. BPHS determines the expected dasha lord")
            print("from the event type — you only need to supply the date.\n")

            # Show numbered event type menu
            type_keys = list(EVENT_LABELS.keys())
            for i, k in enumerate(type_keys, 1):
                print(f"  [{i:2d}] {EVENT_LABELS[k]}")
            print()

            events: list[LifeEvent] = []
            while True:
                choice = input("  Event type number (or Enter to finish): ").strip()
                if not choice:
                    break
                try:
                    event_type = type_keys[int(choice) - 1]
                except (ValueError, IndexError):
                    print("  Invalid choice — try again.")
                    continue
                dt_str = input(f"  Date of {EVENT_LABELS[event_type]} (DD/MM/YYYY): ").strip()
                try:
                    dv, mv, yv = dt_str.split("/")
                    evt_date = _date(int(yv), int(mv), int(dv))
                except ValueError:
                    print("  Invalid date — skipping.")
                    continue
                desc = input("  Brief description (optional): ").strip() or EVENT_LABELS[event_type]
                events.append(LifeEvent(description=desc, event_date=evt_date, event_type=event_type))
                print(f"  ✓ Added: {desc} on {evt_date}")

            lagna_hint = input("\nKnown lagna sign (e.g. Scorpio, or Enter to skip): ").strip() or None

            if not events:
                print("No events entered — cannot rectify without constraints.")
            else:
                print(f"\nSweeping {chart.birth.date} with {len(events)} event(s) at 1-minute resolution…")
                print("(This takes ~5–10 seconds)\n")
                skill = RectificationSkill(events=events, known_lagna=lagna_hint)
                sr = skill.run(chart)
                orch = OrchestratorResult(skill_results=[sr])
                orch.all_findings = [f.statement for f in sr.findings]
                orch.all_unverified = sr.unverified
                synthesise(chart, orch, query="Birth time rectification results", stream=True)
                print()

        elif user_input.lower() == "/new":
            birth = _load_or_prompt()
            print("Fetching chart…")
            chart = get_full_chart(birth)
            print(f"Chart loaded. Lagna: {chart.general.lagna_sign if chart.general else 'unknown'}")

        else:
            # Treat plain text as a question
            print(f"\nRunning targeted analysis…\n")
            orch_result = run_targeted(chart, user_input)
            print()
            synthesise(chart, orch_result, query=user_input, stream=True)
            print()


if __name__ == "__main__":
    main()
