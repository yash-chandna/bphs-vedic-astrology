---
name: bphs-birthdate-finder
description: >
  Reverse-engineers a person's unknown birth date and time using BPHS (Brihat Parashara Hora Shastra). Use this skill whenever someone doesn't know their birth date or time and wants to find or estimate it through Vedic astrology. Trigger on phrases like "I don't know my birth time", "can you find my birth date", "I was adopted and don't have birth records", "what's my lagna if I don't know my birth time", "figure out when I was born from my life events", or any request to estimate or discover a birth date/time from personality, appearance, or life history. This is distinct from /rectify which refines an approximate known time — this skill starts from scratch with no birth data at all.
---

# BPHS Birthdate Finder

This skill reverse-engineers a person's birth date and time from life evidence alone — no birth records needed. The approach is methodical elimination: each piece of evidence rules out possibilities until a probable date range and time window emerge. Every deduction must carry a BPHS citation.

The existing `/rectify` command refines a known approximate time. This skill starts from zero.

## Reference files

Pull these in as needed during the investigation — don't load all upfront:

| File | When to use |
|---|---|
| `references/planets.md` | Physical trait indicators, karakatva, planet natures |
| `references/houses.md` | Lagna significations, house classifications |
| `references/dasha.md` | Dasha sequence, nakshatra lords, bhukti durations |
| `references/yogas.md` | Yoga signatures to match against life outcomes |
| `references/shadbala.md` | Strength indicators when assessing planet dominance |
| `references/divisionals.md` | D9/D10 for marriage/career event cross-checks |

---

## Step 0 — Intake: Establish What Is Already Known

When this skill is invoked, start here before doing any astrological reasoning. Ask the person directly:

> "Let's start with what you already know or suspect. Please tell me:
> 1. Do you have a date of birth (even approximate — a year, a season, a decade)?
> 2. Do you have a time of birth (even rough — morning, afternoon, night, or a specific time someone told you)?
> 3. Do you have a birth place (city or region)?"

Then adapt the entire workflow based on what they provide:

| Situation | What's known | Workflow |
|---|---|---|
| **Full unknown** | Nothing at all | Run all 6 steps — collect traits, events, reverse-dasha, transit, lagna rising |
| **Year known, time unknown** | Birth year (e.g., "1983") | Skip Step 3 (dasha year calc); focus on lagna from traits + transit month narrowing + rising time |
| **Date known, time unknown** | Full date (e.g., "15 June 1983") | Cast chart for that date at various times; use lagna traits + life events to pick the right rising sign and narrow to a 2-hour window; hand off to `/rectify` |
| **Approximate date** | Season or year range (e.g., "sometime in 1983, maybe winter") | Use dasha reverse-calc to confirm/eliminate years; use transits to pick season; then lagna rising for time |
| **Time known, date uncertain** | Time (e.g., "I was born at 6am") | Lagna is known from time; use that lagna's traits to confirm or redirect, then dasha reverse-calc for birth year |
| **Partial time** | Rough time (e.g., "morning" or "after sunset") | Eliminates ~half the lagnas immediately; proceed with remaining candidates |
| **Family lore only** | "I think I was born around noon on a Tuesday in winter 1979" | Treat as approximate date + approximate time; validate via traits and dasha, then refine |

The goal in every case is to move the person from uncertainty toward 1–3 specific candidate charts, then hand off to `/rectify` for final precision.

After establishing what's known, also ask:

> "Do you have a guess — even a rough one — about your birth date or time? Sometimes family members mentioned something, or you've seen a partial record. Even 'I think I'm a Scorpio' helps."

Accept the guess, note it, and treat it as a hypothesis to test — not a confirmed fact.

---

## Step 1 — Gather Evidence

Before reasoning, collect everything available. Ask the person for:

**Physical traits** (these indicate lagna and lagna lord):
- Body build: lean/wiry, medium, heavy/stout
- Complexion: fair, wheatish, dark, ruddy, pale
- Eyes: large/expressive, sharp/piercing, small/sunken, almond-shaped
- Face shape: oval, round, long/narrow, square
- Notable features: prominent forehead, thick hair, visible veins, broad shoulders

**Personality** (lagna and Moon sign indicators):
- Temperament: fiery/impulsive, calm/stubborn, communicative/restless, emotional/nurturing, analytical/critical, harmonious/indecisive, intense/secretive, philosophical/optimistic, disciplined/ambitious, unconventional/detached, mystical/empathetic
- What do people consistently say about them?
- Natural strengths and recurring life themes

**Life events with years** (for dasha reverse-calculation):
- Marriage or major relationship: year
- Children: years of birth
- Career start, major break, or peak: year
- Serious illness or surgery: year
- Financial windfall or major loss: year
- Relocation (especially foreign): year
- Death of parent: year
- Any year they describe as "the best" or "the worst" of their life

**Current situation** (helps anchor the dasha chain):
- Approximate current age or birth decade (even "I'm in my 40s" helps enormously)
- What kind of period does life feel like right now?
- Any known partial information (birth year only, birth season, "morning baby", etc.)

Take what you can get — a partial set is enough to begin. More events = tighter date range.

---

## Step 2 — Shortlist Lagnas from Physical/Personality Traits

Read `references/houses.md` (house significations) and `references/planets.md` (karakatva) to map traits to lagna candidates.

**BPHS lagna physical signatures** (Ch. 3, Graha Swaroopa applied to lagnas):

| Lagna | Body | Complexion | Eyes | Personality |
|---|---|---|---|---|
| Aries | Medium, muscular, lean | Ruddy/copper | Sharp, active | Bold, impulsive, pioneering |
| Taurus | Stout, sturdy, thick neck | Fair/pale | Large, patient | Stubborn, sensual, steady |
| Gemini | Tall, thin, long limbs | Dusky | Expressive, quick | Clever, restless, communicative |
| Cancer | Medium, round face, soft | Fair/pale | Large, watery | Emotional, intuitive, home-oriented |
| Leo | Large frame, broad shoulders | Copper/fair | Commanding | Regal, proud, generous |
| Virgo | Medium, neat, slim | Dusky/wheatish | Alert, analytical | Methodical, critical, service-oriented |
| Libra | Medium, symmetrical, graceful | Fair | Pleasant, artistic | Balanced, diplomatic, relationship-focused |
| Scorpio | Medium, penetrating gaze | Dark/dusky | Intense, deep | Secretive, magnetic, intense |
| Sagittarius | Tall, athletic, long thighs | Wheatish/fair | Open, optimistic | Philosophical, honest, freedom-loving |
| Capricorn | Thin, bony, prominent joints | Dark | Serious, cautious | Disciplined, ambitious, slow-and-steady |
| Aquarius | Medium-tall, broad build | Dark/mixed | Distant, humanitarian | Unconventional, intellectual, detached |
| Pisces | Short/medium, fleshy, soft | Fair/pale | Dreamy, large | Empathetic, mystical, fluid |

The lagna lord's placement modifies these traits significantly. A Scorpio lagna with Mars in Cancer will look and feel quite different from Mars in Capricorn. Keep 2–3 lagnas on the table until dasha evidence narrows it.

**Output of this step:** A shortlist of 2–3 candidate lagnas, each with the reasoning chain (which traits match, which BPHS chapter supports it).

---

## Step 3 — Reverse-Calculate Birth Year from Dasha Sequences

This is the most powerful narrowing tool. The Vimshottari dasha sequence is fixed and cyclic (120 years). If you know what kind of period someone experienced at a known age, you can work backwards to constrain the birth year.

Read `references/dasha.md` for the full sequence and bhukti duration formula.

**The reverse-dasha method:**

1. Take a life event with a known year (e.g., "I got married in 2003")
2. Identify which dasha lord would produce that event (marriage → Venus, 7th lord, or Jupiter for females)
3. Calculate what birth years would put that person in Venus Mahadasha in 2003
   - Venus Mahadasha = 20 years; if they were 28 in 2003, born ~1975; Venus MD runs from, say, age 22–42 → consistent
   - Try all 9 starting positions of Venus in the 120-year cycle
4. Cross-reference with a second event to eliminate impossible birth years
5. Repeat until a 2–5 year birth window remains

**Key dasha signatures for life events:**

| Event | Likely active dasha(s) |
|---|---|
| Marriage | Venus MD/AD, 7th lord MD/AD, Jupiter (for female) |
| First child | Jupiter MD/AD, 5th lord MD/AD |
| Career peak | 10th lord, Sun, Saturn MD/AD |
| Major illness | 6th lord, Saturn, Rahu MD/AD |
| Father's death | Sun MD/AD, 9th lord MD/AD in malefic sub-period |
| Mother's death | Moon MD/AD, 4th lord MD/AD in malefic sub-period |
| Foreign travel/relocation | Rahu MD/AD, 12th lord, 9th lord MD/AD |
| Sudden windfall | Rahu, 11th lord, Jupiter MD/AD |
| Major financial loss | 12th lord, Saturn, Ketu MD/AD |
| Spiritual awakening | Ketu MD/AD, 12th lord |

Show your calculation chain. For example:
> "If born in 1978, the dasha sequence starting from Moon (Rohini nakshatra) would place Venus MD from age 7–27, making 2003 (age 25) fall in Venus MD / Saturn AD — consistent with marriage delay or structured relationship. If born in 1982, Venus MD runs age 3–23, making 2003 fall in Sun MD — less typical for marriage. Birth year 1975–1979 range is more consistent."

**Output of this step:** A birth year range of 2–5 years.

---

## Step 4 — Cross-Check Yogas Against Life Outcomes

Now test whether the shortlisted lagna(s) and birth year(s) produce charts that actually explain the person's life trajectory. Read `references/yogas.md`.

For each candidate lagna + birth year combination, ask:
- Does the person's level of wealth/career success match what the chart would produce?
- If they describe a "Raja yoga life" (sudden rise, authority, recognition), does the shortlisted chart have a kendra-trikona lord conjunction?
- If they describe persistent financial struggle, is a Daridra yoga or 12th lord in 2nd likely?
- If their marriage has been troubled, does Kuja Dosha or a malefic 7th house match?
- If they have many children, does Jupiter strongly placed in/aspecting the 5th fit?

This step eliminates lagna candidates that contradict the life story. A person describing lifelong poverty cannot have an unafflicted Lakshmi yoga — that combination is impossible, so that lagna is wrong.

**Output of this step:** Lagnas and birth years that survive yoga cross-checking. Usually narrows to 1–2 lagnas and a 2–3 year window.

---

## Step 5 — Narrow to Season/Month via Transits

Slow-moving planets (Saturn, Jupiter, Rahu/Ketu) move sign-by-sign over 2.5–18 months. Their transit position at a key life event date tells you where they were in the zodiac — and combined with the chart candidate, tells you what season or month makes that transit meaningful.

**Transit anchors:**

- Saturn transit over natal Moon (Sade Sati, 7½ year period): produces prolonged hardship, health stress, or transformation
- Jupiter transit over lagna, 5th, or 9th: typically brings good fortune, children, opportunities
- Rahu/Ketu transit over natal Sun or Moon: sudden disruptions, foreign events, unusual occurrences
- Saturn return (~age 29–30 and 58–60): universal period of reckoning and restructuring

Using public ephemeris data (or the VedAstro API via `chart/client.py`), find what sign Saturn and Jupiter occupied in the year of a key event, then check which months of that year they were in that sign. The birth chart candidate that makes those transits most meaningful (Saturn transiting a sensitive natal point, Jupiter activating a yoga) points to the correct birth season.

**Output of this step:** A birth month range — typically narrowed to a 2–4 month window within the birth year.

---

## Step 6 — Determine Birth Time Window from Lagna

Each sign rises on the eastern horizon for approximately 2 hours (varies by latitude). The lagna determines the birth time range.

**Approximate rising times (for ~23°N latitude, Lahiri ayanamsa, vary by season):**

| Lagna | Approximate rising window |
|---|---|
| Aries | 06:00–08:00 |
| Taurus | 08:00–10:30 |
| Gemini | 10:30–12:30 |
| Cancer | 12:30–14:30 |
| Leo | 14:30–16:30 |
| Virgo | 16:30–18:30 |
| Libra | 18:30–20:30 |
| Scorpio | 20:30–22:30 |
| Sagittarius | 22:30–00:30 |
| Capricorn | 00:30–02:30 |
| Aquarius | 02:30–04:30 |
| Pisces | 04:30–06:00 |

This table is approximate — actual rising times shift by 15–40 minutes seasonally and by ~4 minutes per degree of longitude. The birth city matters. Use it to give a 2-hour birth time window, not a precise time.

If the person knows anything at all about the time ("before sunrise", "around noon", "late at night"), this immediately confirms or eliminates lagna candidates.

**Output of this step:** A 2-hour birth time window corresponding to the surviving lagna(s).

---

## Output Format

Present findings as a structured report:

```
## Birth Date & Time Estimation Report

### Most Probable Birth Period
- Date range: [Month–Month, Year] (e.g., "February–April 1979")
- Birth time window: [e.g., "Between 20:30 and 22:30 — Scorpio lagna"]
- Confidence: [High / Medium / Low] with reasons

### Evidence Chain
**Lagna determination:**
[BPHS Ch.X] [Trait] → points to [Lagna] because [reasoning]

**Dasha reverse-calculation:**
[BPHS Ch.46] Event "[event]" in [year] → [dasha lord] MD active → birth year [range]
[BPHS Ch.46] Cross-check: event "[event]" in [year] → consistent / eliminates [year]

**Yoga cross-check:**
[BPHS Ch.X] Life outcome "[outcome]" requires [yoga/placement] → consistent with [lagna] chart

**Transit anchors:**
[BPHS p.X] Saturn in [sign] in [year] transited natal [point] → confirms [season]

### Candidate Charts to Test
List 1–3 specific test dates (e.g., "15 March 1979, ~21:00 — run /rectify to refine")
Suggest running the BPHS agent's /rectify command on each candidate for final narrowing.

### What Would Increase Confidence
List the one or two additional pieces of information that would most tighten the estimate.
```

---

## Citation rule

Every deduction must carry a BPHS citation: `[BPHS Ch.X, Sl.Y]` or `[BPHS p.N]`. Lines without citations are marked `[UNVERIFIED]` and flagged as speculative. The reasoning chain is only as strong as its citations — don't invent sloka numbers.

---

## Handoff to /rectify

Once 1–3 candidate dates and time windows are identified — or when the date is confirmed but only the time is unknown — hand off to `/rectify`:

> "We now have [N] candidate birth dates. To narrow further, run the BPHS agent and use `/rectify` with each candidate — it will test the chart against your life events more precisely and home in on the exact time."

**If date is already confirmed:** go straight to `/rectify` — skip this skill entirely after Step 0, or use only the lagna-rising-time step (Step 6) to give the user a time window to feed into rectification.

**If time is already confirmed:** use the known time to fix the lagna, then run only Steps 3–5 to find the birth year and date.

The division of labour:
- This skill: macro work — birth year range + candidate lagna(s) + birth season
- `/rectify`: micro work — exact time within a known lagna, validated against life events minute by minute
