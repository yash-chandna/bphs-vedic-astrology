# Kundali Milan — Vedic Matchmaking (BPHS & Parashari tradition)

Kundali Milan is the process of comparing two birth charts to assess compatibility for marriage. The BPHS prescribes specific techniques; use all three layers together for a complete assessment.

## 1. Ashtakoot (8-factor) Guna Milan

The most widely used system. Maximum score: 36 points. Minimum recommended for marriage: 18 points.

| Koot | Max Points | What it measures |
|---|---|---|
| **Varna** | 1 | Spiritual compatibility and ego balance |
| **Vashya** | 2 | Control, influence, and mutual attraction |
| **Tara** | 3 | Birth star compatibility and health/longevity |
| **Yoni** | 4 | Physical/sexual compatibility and instinctive nature |
| **Graha Maitri** | 5 | Mental compatibility; determined by Moon sign lords' friendship |
| **Gana** | 6 | Temperament match: Deva (divine), Manava (human), Rakshasa (demonic) |
| **Bhakoot (Rasi)** | 7 | Emotional connection, family prosperity, mutual love |
| **Nadi** | 8 | Genetic and health compatibility; same Nadi = 0 points (contraindicated) |

### Gana Compatibility
- Deva + Deva: 6/6
- Manava + Manava: 6/6
- Rakshasa + Rakshasa: 6/6
- Deva + Manava: 5/6
- Deva + Rakshasa: 0/6 (significant incompatibility)
- Manava + Rakshasa: 0/6

### Bhakoot (Rasi distance) compatibility
Problematic Bhakoot combinations (Moon sign distances): 2-12, 5-9, 6-8 from each other are considered inauspicious without remedial planets.

### Nadi Types
- Adi (Vata), Madhya (Pitta), Antya (Kapha)
- Same Nadi for both partners = 0/8 and is classically contraindicated (genetic similarity, health concerns)

## 2. Mangal Dosha (Kuja Dosha) Check

Check Mars in 1st, 2nd, 4th, 7th, 8th, or 12th from lagna, Moon, and Venus in both charts.

- Both partners having Kuja Dosha: cancels the dosha (compatible)
- One partner with dosha, other without: classical contraindication for the unafflicted partner's longevity
- Cancellation conditions: Mars in own sign (Aries/Scorpio), exalted (Capricorn), with benefic Jupiter/Venus, or in friendly sign

## 3. Chart-Level Compatibility (beyond Ashtakoot)

Ashtakoot is a screening system — chart-level analysis is essential for a complete reading. Assess:

### 7th House (Spouse)
- 7th lord placement, strength, and aspects in both D1 and D9 (Navamsa)
- Benefics in or aspecting 7th = marital happiness; malefics = friction
- 7th lord in dusthana (6,8,12) = delayed or troubled marriage

### Venus (for male chart) / Jupiter (for female chart)
- Karaka for spouse: Venus for males, Jupiter for females
- Dignity, house placement, and aspects on these karakas reveals spouse's quality and marital longevity
- Both combust or debilitated without Neecha Bhanga = significant concern

### Navamsa (D9) — Marriage chart
- Compare both partners' D9 charts
- 7th house and its lord in D9 shows the deeper marital karma
- Vargottama planets in D9 greatly strengthen their significations

### Dasha Timing
- Current dasha/antardasha of Venus or 7th lord often correlates with marriage timing
- Mutual dasha overlap of Venus/Jupiter periods between partners indicates favorable timing

## 4. Compatibility Output Format

When producing a matchmaking reading, structure the output as:

**Section 1 — Ashtakoot Score**: Present the 8-koot table with scores, total/36, and whether the overall score meets the minimum threshold.

**Section 2 — Dosha Analysis**: Mangal Dosha status for each partner and the net result.

**Section 3 — 7th House & Karaka Analysis**: Strength of marital indicators in both charts.

**Section 4 — Navamsa Comparison**: Key observations from D9 for both partners.

**Section 5 — Timing**: Relevant dashas and whether the current period supports marriage.

**Section 6 — Overall Assessment**: Synthesized verdict with specific strengths and cautions. All statements must carry BPHS citations.

## Loading charts for matchmaking

```bash
# In the CLI:
/load Person1 1992-03-15 09:20 Delhi
/load Person2 1993-07-22 14:45 Mumbai
/match Person1 Person2
```

Or via Python API — load both charts separately and pass to the matchmaking skill when implemented.
