"""
BPHS planetary data — natural nature, dignities, aspects, relationships.
Sources: BPHS Ch. 3 (Graha Swaroopa), Ch. 4 (Graha Maitri), Ch. 27–28 (Shadbala).
"""

# fmt: off

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

# BPHS Ch. 3 — Natural benefic / malefic
NATURAL_NATURE = {
    "Sun":     "malefic",
    "Moon":    "benefic",   # full Moon; waning Moon within 72° of Sun → malefic
    "Mars":    "malefic",
    "Mercury": "benefic",   # alone or with benefics; with malefics → malefic
    "Jupiter": "benefic",
    "Venus":   "benefic",
    "Saturn":  "malefic",
    "Rahu":    "malefic",
    "Ketu":    "malefic",
}

# BPHS Ch. 3 — Own signs (Moolatrikona + Swakshetra)
# Moolatrikona is the primary rulership; all others are Swakshetra
MOOLTRIKONA = {
    "Sun":     ("Leo", (0, 20)),       # 0–20° Leo
    "Moon":    ("Taurus", (4, 30)),    # 4–30° Taurus (Rohini)
    "Mars":    ("Aries", (0, 12)),     # 0–12° Aries
    "Mercury": ("Virgo", (16, 20)),    # 16–20° Virgo
    "Jupiter": ("Sagittarius", (0, 10)),
    "Venus":   ("Libra", (0, 15)),
    "Saturn":  ("Aquarius", (0, 20)),
    "Rahu":    None,
    "Ketu":    None,
}

OWN_SIGNS = {
    "Sun":     ["Leo"],
    "Moon":    ["Cancer"],
    "Mars":    ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"],
    "Jupiter": ["Sagittarius", "Pisces"],
    "Venus":   ["Taurus", "Libra"],
    "Saturn":  ["Capricorn", "Aquarius"],
    "Rahu":    [],   # BPHS gives Rahu/Ketu Aquarius/Scorpio in some chapters; treat as none for dignity
    "Ketu":    [],
}

# BPHS Ch. 3 — Exaltation sign + exact degree of max exaltation
EXALTATION = {
    "Sun":     ("Aries", 10),
    "Moon":    ("Taurus", 3),
    "Mars":    ("Capricorn", 28),
    "Mercury": ("Virgo", 15),
    "Jupiter": ("Cancer", 5),
    "Venus":   ("Pisces", 27),
    "Saturn":  ("Libra", 20),
    "Rahu":    ("Gemini", None),   # varies by tradition; Taurus in some BPHS editions
    "Ketu":    ("Sagittarius", None),
}

# Debilitation = opposite sign of exaltation
DEBILITATION = {
    "Sun":     ("Libra", 10),
    "Moon":    ("Scorpio", 3),
    "Mars":    ("Cancer", 28),
    "Mercury": ("Pisces", 15),
    "Jupiter": ("Capricorn", 5),
    "Venus":   ("Virgo", 27),
    "Saturn":  ("Aries", 20),
    "Rahu":    ("Sagittarius", None),
    "Ketu":    ("Gemini", None),
}

# BPHS Ch. 4 — Permanent friends, enemies, neutrals (Naisargika Maitri)
PERMANENT_FRIENDS = {
    "Sun":     ["Moon", "Mars", "Jupiter"],
    "Moon":    ["Sun", "Mercury"],
    "Mars":    ["Sun", "Moon", "Jupiter"],
    "Mercury": ["Sun", "Venus"],
    "Jupiter": ["Sun", "Moon", "Mars"],
    "Venus":   ["Mercury", "Saturn"],
    "Saturn":  ["Mercury", "Venus"],
    "Rahu":    ["Venus", "Saturn"],
    "Ketu":    ["Mars", "Venus", "Saturn"],
}
PERMANENT_ENEMIES = {
    "Sun":     ["Venus", "Saturn"],
    "Moon":    ["None"],
    "Mars":    ["Mercury"],
    "Mercury": ["Moon"],
    "Jupiter": ["Mercury", "Venus"],
    "Venus":   ["Sun", "Moon"],
    "Saturn":  ["Sun", "Moon", "Mars"],
    "Rahu":    ["Sun", "Moon"],
    "Ketu":    ["Sun", "Moon"],
}
PERMANENT_NEUTRALS = {
    "Sun":     ["Mercury"],
    "Moon":    ["Mars", "Jupiter", "Venus", "Saturn"],
    "Mars":    ["Venus", "Saturn"],
    "Mercury": ["Mars", "Jupiter", "Saturn"],
    "Jupiter": ["Saturn"],
    "Venus":   ["Mars", "Jupiter"],
    "Saturn":  ["Jupiter"],
    "Rahu":    ["Mars", "Jupiter", "Mercury"],
    "Ketu":    ["Mercury", "Jupiter"],
}

# BPHS Ch. 26 — Full aspects (drishti) each planet casts
# All planets aspect the 7th from themselves.
# Special aspects:
SPECIAL_ASPECTS = {
    "Mars":    [4, 7, 8],    # 4th, 7th, 8th from itself
    "Jupiter": [5, 7, 9],
    "Saturn":  [3, 7, 10],
    "Rahu":    [5, 7, 9],    # Same as Jupiter per BPHS
    "Ketu":    [5, 7, 9],
}
ALL_PLANETS_ASPECT = {p: [7] for p in PLANETS}
for p, houses in SPECIAL_ASPECTS.items():
    ALL_PLANETS_ASPECT[p] = houses

# BPHS — Karakatva (primary significations) of each planet
KARAKATVA = {
    "Sun":     ["soul (Atma)", "father", "king", "government", "health", "vitality", "bones", "heart"],
    "Moon":    ["mind", "mother", "emotions", "liquids", "public", "travel", "breasts", "left eye"],
    "Mars":    ["courage", "brothers", "land", "property", "enemies", "surgery", "blood", "younger siblings"],
    "Mercury": ["intelligence", "speech", "education", "trade", "skin", "maternal uncle", "communication"],
    "Jupiter": ["wisdom", "children", "husband (for female)", "dharma", "wealth", "teacher", "liver", "fat"],
    "Venus":   ["wife (for male)", "marriage", "comforts", "vehicles", "arts", "beauty", "semen", "eyes"],
    "Saturn":  ["longevity", "sorrow", "servants", "masses", "iron", "agriculture", "legs", "discipline"],
    "Rahu":    ["paternal grandfather", "foreigners", "sudden events", "poison", "illusion"],
    "Ketu":    ["maternal grandfather", "moksha", "spirituality", "past life", "occult"],
}

# BPHS Ch. 3 — Chara (movable) karakas used for Jaimini; included for completeness
# (the above are Sthira/fixed karakas for Parashari system)

# Planet colours, gems, directions — referenced in some BPHS predictions
PLANET_COLOR = {
    "Sun": "copper/red", "Moon": "white", "Mars": "blood red",
    "Mercury": "green", "Jupiter": "yellow/golden", "Venus": "variegated/white",
    "Saturn": "dark/black", "Rahu": "smoky", "Ketu": "spotted",
}

PLANET_GEM = {
    "Sun": "Ruby", "Moon": "Pearl", "Mars": "Coral",
    "Mercury": "Emerald", "Jupiter": "Yellow Sapphire", "Venus": "Diamond",
    "Saturn": "Blue Sapphire", "Rahu": "Hessonite (Gomed)", "Ketu": "Cat's Eye (Lahsuniya)",
}
