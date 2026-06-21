"""
BPHS Gochar (Transit) rules.
Sources: BPHS Ch. 51–58 (Gochar Phala), Ch. 66–69 (Ashtakvarga for transits).

Gochar = movement of planets in the sky relative to the natal Moon sign (Janma Rashi)
and to natal planetary positions. BPHS is explicit: transits must be read from the
Moon sign FIRST, then from the lagna, then from the natal planet being transited.
"""

# fmt: off

# ── TRANSIT RESULTS FROM MOON SIGN (JANMA RASHI) ─────────────────────────────
# BPHS Ch. 51–58: each planet transiting each house FROM THE MOON
# house_from_moon: 1 = transiting the same sign as natal Moon
# Results: "good" | "bad" | "mixed"

GOCHAR_FROM_MOON: dict[str, dict[int, dict]] = {
    "Sun": {
        1:  {"result": "bad",   "bphs_ref": "BPHS Ch. 51", "effect": "Eye disease, fear, wandering, trouble from government/authority."},
        2:  {"result": "bad",   "bphs_ref": "BPHS Ch. 51", "effect": "Financial loss, trouble from speech, family discord."},
        3:  {"result": "good",  "bphs_ref": "BPHS Ch. 51", "effect": "Gain of wealth, courage, victory over enemies, good health."},
        4:  {"result": "bad",   "bphs_ref": "BPHS Ch. 51", "effect": "Unhappiness, loss of domestic peace, trouble from mother."},
        5:  {"result": "bad",   "bphs_ref": "BPHS Ch. 51", "effect": "Mental anguish, trouble with children, digestive issues."},
        6:  {"result": "good",  "bphs_ref": "BPHS Ch. 51", "effect": "Destruction of enemies, good health, financial gains."},
        7:  {"result": "bad",   "bphs_ref": "BPHS Ch. 51", "effect": "Trouble during travel, quarrels with spouse."},
        8:  {"result": "bad",   "bphs_ref": "BPHS Ch. 51", "effect": "Eye disease, fever, fear, ill health."},
        9:  {"result": "bad",   "bphs_ref": "BPHS Ch. 51", "effect": "Loss of fortune, trouble from father, obstacles in dharmic activities."},
        10: {"result": "good",  "bphs_ref": "BPHS Ch. 51", "effect": "Success in career, recognition from authority, professional gains."},
        11: {"result": "good",  "bphs_ref": "BPHS Ch. 51", "effect": "Financial gains, fulfillment of desires, good health."},
        12: {"result": "bad",   "bphs_ref": "BPHS Ch. 51", "effect": "Expenses, loss of prestige, eye trouble, foreign travel against will."},
    },
    "Moon": {
        1:  {"result": "bad",   "bphs_ref": "BPHS Ch. 52", "effect": "Mental unease, wandering, ill health."},
        2:  {"result": "good",  "bphs_ref": "BPHS Ch. 52", "effect": "Gain of wealth, family happiness, good food."},
        3:  {"result": "good",  "bphs_ref": "BPHS Ch. 52", "effect": "Gain of clothes, happiness, courage."},
        4:  {"result": "bad",   "bphs_ref": "BPHS Ch. 52", "effect": "Unhappiness, trouble from mother and home."},
        5:  {"result": "bad",   "bphs_ref": "BPHS Ch. 52", "effect": "Mental suffering, trouble with children."},
        6:  {"result": "good",  "bphs_ref": "BPHS Ch. 52", "effect": "Defeat of enemies, good health."},
        7:  {"result": "good",  "bphs_ref": "BPHS Ch. 52", "effect": "Happiness from spouse, comforts, travel."},
        8:  {"result": "bad",   "bphs_ref": "BPHS Ch. 52", "effect": "Ill health, fear, financial loss."},
        9:  {"result": "bad",   "bphs_ref": "BPHS Ch. 52", "effect": "Loss of fortune, conflict with father/guru."},
        10: {"result": "bad",   "bphs_ref": "BPHS Ch. 52", "effect": "Career obstacles, mental worry."},
        11: {"result": "good",  "bphs_ref": "BPHS Ch. 52", "effect": "Gains, recovery from illness, desires fulfilled."},
        12: {"result": "bad",   "bphs_ref": "BPHS Ch. 52", "effect": "Expenses, loss of sleep, eye trouble."},
    },
    "Mars": {
        1:  {"result": "bad",   "bphs_ref": "BPHS Ch. 53", "effect": "Quarrels, injury, blood disorders, fever."},
        2:  {"result": "bad",   "bphs_ref": "BPHS Ch. 53", "effect": "Financial loss, family trouble, harsh speech."},
        3:  {"result": "good",  "bphs_ref": "BPHS Ch. 53", "effect": "Gain of wealth, courage, victory, good health."},
        4:  {"result": "bad",   "bphs_ref": "BPHS Ch. 53", "effect": "Trouble at home, loss of property, danger from fire/accidents."},
        5:  {"result": "bad",   "bphs_ref": "BPHS Ch. 53", "effect": "Trouble with children, mental suffering."},
        6:  {"result": "good",  "bphs_ref": "BPHS Ch. 53", "effect": "Destruction of enemies, good health, gains."},
        7:  {"result": "bad",   "bphs_ref": "BPHS Ch. 53", "effect": "Marital conflicts, trouble in partnerships."},
        8:  {"result": "bad",   "bphs_ref": "BPHS Ch. 53", "effect": "Danger, surgery risk, accidents, blood trouble."},
        9:  {"result": "bad",   "bphs_ref": "BPHS Ch. 53", "effect": "Loss of fortune, conflict with father, trouble in dharmic pursuits."},
        10: {"result": "bad",   "bphs_ref": "BPHS Ch. 53", "effect": "Career setbacks, disputes with superiors."},
        11: {"result": "good",  "bphs_ref": "BPHS Ch. 53", "effect": "Financial gains, recovery from illness."},
        12: {"result": "bad",   "bphs_ref": "BPHS Ch. 53", "effect": "Expenses, imprisonment risk, secret enemies."},
    },
    "Mercury": {
        1:  {"result": "mixed", "bphs_ref": "BPHS Ch. 54", "effect": "Gains from trade and communication; some restlessness."},
        2:  {"result": "good",  "bphs_ref": "BPHS Ch. 54", "effect": "Good speech, financial gains, family happiness."},
        3:  {"result": "bad",   "bphs_ref": "BPHS Ch. 54", "effect": "Trouble from siblings, unnecessary travel."},
        4:  {"result": "good",  "bphs_ref": "BPHS Ch. 54", "effect": "Domestic happiness, good education, property gains."},
        5:  {"result": "good",  "bphs_ref": "BPHS Ch. 54", "effect": "Intellectual gains, good children, speculation success."},
        6:  {"result": "bad",   "bphs_ref": "BPHS Ch. 54", "effect": "Enemies active, skin trouble, disputes."},
        7:  {"result": "good",  "bphs_ref": "BPHS Ch. 54", "effect": "Happiness from spouse, business success."},
        8:  {"result": "bad",   "bphs_ref": "BPHS Ch. 54", "effect": "Fear, obstacles, mental trouble."},
        9:  {"result": "good",  "bphs_ref": "BPHS Ch. 54", "effect": "Fortune increases, good relationship with father/teacher."},
        10: {"result": "good",  "bphs_ref": "BPHS Ch. 54", "effect": "Career advancement, recognition, success in business."},
        11: {"result": "good",  "bphs_ref": "BPHS Ch. 54", "effect": "Financial gains, desires fulfilled."},
        12: {"result": "bad",   "bphs_ref": "BPHS Ch. 54", "effect": "Expenses, deception, skin trouble."},
    },
    "Jupiter": {
        1:  {"result": "bad",   "bphs_ref": "BPHS Ch. 55", "effect": "Physical trouble, wandering, loss of status."},
        2:  {"result": "good",  "bphs_ref": "BPHS Ch. 55", "effect": "Great financial gains, family happiness, good speech."},
        3:  {"result": "bad",   "bphs_ref": "BPHS Ch. 55", "effect": "Trouble from siblings, unnecessary expenses."},
        4:  {"result": "bad",   "bphs_ref": "BPHS Ch. 55", "effect": "Unhappiness at home, trouble with mother/property."},
        5:  {"result": "good",  "bphs_ref": "BPHS Ch. 55", "effect": "Blessed with children, intelligence, spiritual progress."},
        6:  {"result": "bad",   "bphs_ref": "BPHS Ch. 55", "effect": "Disease, defeat by enemies, financial loss."},
        7:  {"result": "good",  "bphs_ref": "BPHS Ch. 55", "effect": "Marital happiness, gains from partnerships, travel."},
        8:  {"result": "bad",   "bphs_ref": "BPHS Ch. 55", "effect": "Ill health, financial loss, fear of death."},
        9:  {"result": "good",  "bphs_ref": "BPHS Ch. 55", "effect": "Great fortune, pilgrimage, father's well-being, dharmic gains."},
        10: {"result": "bad",   "bphs_ref": "BPHS Ch. 55", "effect": "Career obstacles, humiliation, loss of authority."},
        11: {"result": "good",  "bphs_ref": "BPHS Ch. 55", "effect": "Excellent financial gains, all desires fulfilled."},
        12: {"result": "bad",   "bphs_ref": "BPHS Ch. 55", "effect": "Expenses, loss of prestige, spiritual seeking (moksha inclination)."},
    },
    "Venus": {
        1:  {"result": "good",  "bphs_ref": "BPHS Ch. 56", "effect": "Happiness, comforts, gains, romantic pleasure."},
        2:  {"result": "good",  "bphs_ref": "BPHS Ch. 56", "effect": "Financial gains, good food, family happiness."},
        3:  {"result": "bad",   "bphs_ref": "BPHS Ch. 56", "effect": "Trouble from siblings, unnecessary expenses."},
        4:  {"result": "good",  "bphs_ref": "BPHS Ch. 56", "effect": "Domestic happiness, vehicles, comforts."},
        5:  {"result": "bad",   "bphs_ref": "BPHS Ch. 56", "effect": "Trouble with children, mental suffering."},
        6:  {"result": "bad",   "bphs_ref": "BPHS Ch. 56", "effect": "Disease, enemies active, disputes."},
        7:  {"result": "good",  "bphs_ref": "BPHS Ch. 56", "effect": "Excellent for marriage, romantic happiness, spouse's well-being."},
        8:  {"result": "good",  "bphs_ref": "BPHS Ch. 56", "effect": "Financial gains, gains through inheritance or spouse."},
        9:  {"result": "bad",   "bphs_ref": "BPHS Ch. 56", "effect": "Trouble with father, loss of fortune."},
        10: {"result": "bad",   "bphs_ref": "BPHS Ch. 56", "effect": "Career obstacles, unhappiness in work."},
        11: {"result": "good",  "bphs_ref": "BPHS Ch. 56", "effect": "Financial gains, happiness, romantic success."},
        12: {"result": "good",  "bphs_ref": "BPHS Ch. 56", "effect": "Bed pleasures, sensual enjoyment, foreign travel for pleasure."},
    },
    "Saturn": {
        1:  {"result": "bad",   "bphs_ref": "BPHS Ch. 57", "effect": "Physical suffering, wandering, loss of position — especially during Sade Sati."},
        2:  {"result": "bad",   "bphs_ref": "BPHS Ch. 57", "effect": "Financial loss, family trouble, speech problems."},
        3:  {"result": "good",  "bphs_ref": "BPHS Ch. 57", "effect": "Gain of wealth, courage, victory over enemies."},
        4:  {"result": "bad",   "bphs_ref": "BPHS Ch. 57", "effect": "Domestic unhappiness, trouble with mother, loss of property."},
        5:  {"result": "bad",   "bphs_ref": "BPHS Ch. 57", "effect": "Trouble with children, mental suffering."},
        6:  {"result": "good",  "bphs_ref": "BPHS Ch. 57", "effect": "Destruction of enemies, good health, financial gains."},
        7:  {"result": "bad",   "bphs_ref": "BPHS Ch. 57", "effect": "Marital trouble, disease, loss during travel."},
        8:  {"result": "bad",   "bphs_ref": "BPHS Ch. 57", "effect": "Chronic disease, financial loss, fear."},
        9:  {"result": "bad",   "bphs_ref": "BPHS Ch. 57", "effect": "Loss of fortune, trouble with father, decline in dharmic activities."},
        10: {"result": "good",  "bphs_ref": "BPHS Ch. 57", "effect": "Career success (especially Saturn ruling 10th or exalted), authority."},
        11: {"result": "good",  "bphs_ref": "BPHS Ch. 57", "effect": "Financial gains, income increases."},
        12: {"result": "bad",   "bphs_ref": "BPHS Ch. 57", "effect": "Expenses, imprisonment risk, loss of sleep."},
    },
    "Rahu": {
        1:  {"result": "bad",   "bphs_ref": "BPHS Ch. 58", "effect": "Disease, fear, mental confusion, sudden unexpected events."},
        2:  {"result": "bad",   "bphs_ref": "BPHS Ch. 58", "effect": "Financial loss, family trouble."},
        3:  {"result": "good",  "bphs_ref": "BPHS Ch. 58", "effect": "Courage, gains through unconventional means."},
        4:  {"result": "bad",   "bphs_ref": "BPHS Ch. 58", "effect": "Domestic unhappiness, property trouble, mother's ill health."},
        5:  {"result": "bad",   "bphs_ref": "BPHS Ch. 58", "effect": "Mental suffering, trouble with children."},
        6:  {"result": "good",  "bphs_ref": "BPHS Ch. 58", "effect": "Defeat of enemies, gains."},
        7:  {"result": "bad",   "bphs_ref": "BPHS Ch. 58", "effect": "Marital discord, travel difficulties."},
        8:  {"result": "bad",   "bphs_ref": "BPHS Ch. 58", "effect": "Fear, accidents, sudden loss."},
        9:  {"result": "bad",   "bphs_ref": "BPHS Ch. 58", "effect": "Loss of fortune, obstacles in dharmic pursuits."},
        10: {"result": "mixed", "bphs_ref": "BPHS Ch. 58", "effect": "Sudden career changes; can bring rise or fall unexpectedly."},
        11: {"result": "good",  "bphs_ref": "BPHS Ch. 58", "effect": "Financial gains through unexpected means."},
        12: {"result": "bad",   "bphs_ref": "BPHS Ch. 58", "effect": "Expenses, hidden enemies, foreign travel."},
    },
    "Ketu": {
        1:  {"result": "bad",   "bphs_ref": "BPHS Ch. 58", "effect": "Ill health, accidents, spiritual restlessness."},
        2:  {"result": "bad",   "bphs_ref": "BPHS Ch. 58", "effect": "Financial loss, family trouble."},
        3:  {"result": "good",  "bphs_ref": "BPHS Ch. 58", "effect": "Courage, gains, spiritual progress."},
        4:  {"result": "bad",   "bphs_ref": "BPHS Ch. 58", "effect": "Domestic unhappiness, loss of property."},
        5:  {"result": "bad",   "bphs_ref": "BPHS Ch. 58", "effect": "Trouble with children, mental suffering."},
        6:  {"result": "good",  "bphs_ref": "BPHS Ch. 58", "effect": "Defeat of enemies, gains."},
        7:  {"result": "bad",   "bphs_ref": "BPHS Ch. 58", "effect": "Marital difficulty, health of spouse."},
        8:  {"result": "bad",   "bphs_ref": "BPHS Ch. 58", "effect": "Fear, accidents, sudden events."},
        9:  {"result": "bad",   "bphs_ref": "BPHS Ch. 58", "effect": "Loss of fortune, separation from guru."},
        10: {"result": "mixed", "bphs_ref": "BPHS Ch. 58", "effect": "Career disruption; can point towards spirituality."},
        11: {"result": "good",  "bphs_ref": "BPHS Ch. 58", "effect": "Spiritual gains, material gains through past efforts."},
        12: {"result": "good",  "bphs_ref": "BPHS Ch. 58", "effect": "Moksha inclination, spiritual progress, foreign settlement."},
    },
}

# ── SADE SATI (BPHS Ch. 57) ──────────────────────────────────────────────────
# Saturn transiting the 12th, 1st, and 2nd from natal Moon = 7.5 years of difficulty
SADE_SATI_NOTE = (
    "Per BPHS Ch. 57: Saturn transiting the 12th, 1st, and 2nd houses from the natal Moon "
    "constitutes Sade Sati (7.5 years). Each phase (12th, 1st, 2nd) lasts ~2.5 years. "
    "Effects are most intense when Saturn transits the natal Moon sign itself (1st phase of Sade Sati). "
    "Results depend on Saturn's natal strength, its lordship, and the native's lagna."
)

# ── ASHTAMA SHANI ──────────────────────────────────────────────────────────────
ASHTAMA_SHANI_NOTE = (
    "Per BPHS: Saturn transiting the 8th from natal Moon (Ashtama Shani) causes health troubles, "
    "financial loss, obstacles, and general suffering. Duration ~2.5 years."
)

# ── GURU CHANDAL / JUPITER TRANSIT ────────────────────────────────────────────
JUPITER_TRANSIT_NOTE = (
    "Jupiter takes ~1 year per sign (12-year cycle). "
    "Jupiter transiting the 2nd, 5th, 7th, 9th, 11th from natal Moon gives good results per BPHS. "
    "Jupiter transiting 1st, 4th, 6th, 8th, 10th, 12th gives difficulty."
)

# ── VEDHA (OBSTRUCTION) RULE ──────────────────────────────────────────────────
# BPHS: a planet transiting a good house is obstructed (vedha) if another planet
# transits a specific opposing house simultaneously
VEDHA_PAIRS: dict[str, dict[int, int]] = {
    # planet: {good_house: obstructing_house}
    "Sun":     {3: 9, 6: 12, 10: 4, 11: 5},
    "Moon":    {1: 5, 3: 9, 6: 12, 7: 2, 10: 4, 11: 8},
    "Mars":    {3: 12, 6: 9, 11: 5},
    "Mercury": {2: 5, 4: 3, 6: 9, 10: 8, 11: 12},
    "Jupiter": {2: 12, 5: 4, 7: 3, 9: 10, 11: 8},
    "Venus":   {1: 8, 2: 7, 3: 1, 4: 10, 5: 9, 8: 5, 11: 6, 12: 3},
    "Saturn":  {3: 12, 6: 9, 11: 5},
}
# Note: Vedha does not apply between Sun-Saturn or Moon-Mercury

# ── TRANSIT DURATION (APPROXIMATE) ───────────────────────────────────────────
TRANSIT_DURATION_DAYS = {
    "Sun":     30,
    "Moon":    2.25,   # 2 days 6 hours per sign
    "Mars":    45,     # ~45 days per sign on average (varies with retrograde)
    "Mercury": 25,     # variable, with retrograde periods
    "Jupiter": 365,    # ~1 year per sign
    "Venus":   25,     # variable
    "Saturn":  900,    # ~2.5 years per sign
    "Rahu":    548,    # ~18 months per sign (retrograde motion)
    "Ketu":    548,
}
