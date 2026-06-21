"""
BPHS Divisional Chart (Varga) rules.
Sources: BPHS Ch. 6 (Shodashavarga), Ch. 7 (Varga Phala).

Each divisional chart is a sub-division of the rasi chart used to assess
specific life areas with greater precision. Never interpret a divisional chart
in isolation — always read in context of the D1 (Rasi) chart.
"""

# fmt: off

# 16 Shodashavarga divisional charts per BPHS Ch. 6
DIVISIONAL_CHARTS = {
    "D1":  {
        "name": "Rasi (Natal/Birth Chart)",
        "division": 1,
        "purpose": "Overall life, body, personality — the primary chart for all readings.",
        "bphs_ref": "BPHS Ch. 6",
    },
    "D2":  {
        "name": "Hora",
        "division": 2,
        "purpose": "Wealth and finances. Sun hora = male/gold/father's wealth; Moon hora = female/silver/mother's wealth.",
        "bphs_ref": "BPHS Ch. 6",
    },
    "D3":  {
        "name": "Drekkana",
        "division": 3,
        "purpose": "Siblings, courage, and co-born. Also used for death and afterlife in some BPHS chapters.",
        "bphs_ref": "BPHS Ch. 6",
    },
    "D4":  {
        "name": "Chaturthamsa (Turyamsa)",
        "division": 4,
        "purpose": "Immovable property, fortune from land and homes.",
        "bphs_ref": "BPHS Ch. 6",
    },
    "D7":  {
        "name": "Saptamsa",
        "division": 7,
        "purpose": "Children and grandchildren. Primary chart for progeny analysis.",
        "bphs_ref": "BPHS Ch. 6",
    },
    "D9":  {
        "name": "Navamsa",
        "division": 9,
        "purpose": (
            "Spouse, marriage, dharma, and the soul's deeper nature. "
            "The most important divisional chart — always read alongside D1. "
            "A weak D1 planet strong in D9 gains strength; vice versa weakens results."
        ),
        "bphs_ref": "BPHS Ch. 6",
    },
    "D10": {
        "name": "Dasamsa (Dashamsa)",
        "division": 10,
        "purpose": "Career, profession, status, and actions in the world (karma).",
        "bphs_ref": "BPHS Ch. 6",
    },
    "D12": {
        "name": "Dwadashamsa",
        "division": 12,
        "purpose": "Parents — father and mother. Ancestry and genetic inheritance.",
        "bphs_ref": "BPHS Ch. 6",
    },
    "D16": {
        "name": "Shodashamsa (Kalamsa)",
        "division": 16,
        "purpose": "Vehicles, comforts, and happiness from conveyances.",
        "bphs_ref": "BPHS Ch. 6",
    },
    "D20": {
        "name": "Vimshamsa",
        "division": 20,
        "purpose": "Spiritual practice, upasana, and religious merit.",
        "bphs_ref": "BPHS Ch. 6",
    },
    "D24": {
        "name": "Chaturvimshamsa (Siddhamsa)",
        "division": 24,
        "purpose": "Education, learning, and knowledge attainment.",
        "bphs_ref": "BPHS Ch. 6",
    },
    "D27": {
        "name": "Nakshatramsa (Bhamsa)",
        "division": 27,
        "purpose": "Strength, vitality, and physical prowess.",
        "bphs_ref": "BPHS Ch. 6",
    },
    "D30": {
        "name": "Trimshamsa",
        "division": 30,
        "purpose": "Misfortunes, evils, and diseases. Also used for female horoscopy.",
        "bphs_ref": "BPHS Ch. 6",
    },
    "D40": {
        "name": "Khavedamsa (Chatvarimsamsa)",
        "division": 40,
        "purpose": "Auspicious and inauspicious effects — maternal lineage.",
        "bphs_ref": "BPHS Ch. 6",
    },
    "D45": {
        "name": "Akshavedamsa",
        "division": 45,
        "purpose": "General well-being — paternal lineage.",
        "bphs_ref": "BPHS Ch. 6",
    },
    "D60": {
        "name": "Shashtiamsha",
        "division": 60,
        "purpose": (
            "Past life karma and the subtlest level of fate. "
            "Given the highest weight among all vargas in BPHS. "
            "Requires accurate birth time (within minutes)."
        ),
        "bphs_ref": "BPHS Ch. 6",
    },
}

# Varga Visesha — special dignity status from multiple varga positions (BPHS Ch. 7)
VARGA_VISESHA = {
    "Parijata":    {"vargas": 2, "note": "Planet in own/exaltation in 2 of 16 vargas. Comfortable life."},
    "Uttama":      {"vargas": 3, "note": "3 vargas. Good standard of living."},
    "Gopura":      {"vargas": 4, "note": "4 vargas. Nobility and leadership qualities."},
    "Simhasana":   {"vargas": 5, "note": "5 vargas. Authority and power — like a king's seat."},
    "Paravata":    {"vargas": 6, "note": "6 vargas. Great independence and happiness."},
    "Devaloka":    {"vargas": 7, "note": "7 vargas. Divine pleasures and high spiritual merit."},
    "Brahmaloka":  {"vargas": 8, "note": "8 vargas. Closest to Brahman — very rare, supreme attainment."},
    "Srikantha":   {"vargas": 9, "note": "9 vargas. Extremely powerful, blessed by Shiva."},
    "Mridanga":    {"vargas": 10, "note": "10 vargas. Fame lasting beyond one life."},
}

# Key D9 interpretation rules per BPHS
NAVAMSA_RULES = {
    "vargottama": (
        "A planet in the same sign in D1 and D9 is Vargottama — greatly strengthened. "
        "Even a debilitated Vargottama planet gains significant power per BPHS Ch. 7."
    ),
    "d1_strong_d9_weak": (
        "A planet strong in D1 but weak (debilitated, enemy sign) in D9 gives "
        "initial promise that fades or is not fully realized per BPHS Ch. 7."
    ),
    "d1_weak_d9_strong": (
        "A planet weak in D1 but strong in D9 is better than it appears — "
        "results improve over time, especially after its dasha per BPHS Ch. 7."
    ),
    "atmakaraka_navamsa": (
        "The Navamsa lagna and the planet that occupies the Navamsa lagna are important "
        "for understanding the deeper purpose and spiritual direction of the native per BPHS."
    ),
}
