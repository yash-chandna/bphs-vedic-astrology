"""
BPHS house (bhava) data — significations, natural lords, karakas.
Sources: BPHS Ch. 11–15 (Bhava Phala), Ch. 32 (Karaka).
"""

# fmt: off

# 12 signs in zodiac order (used to map lagna to house lords)
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# Natural sign lord for each sign (used to compute house lord from lagna)
SIGN_LORD = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}

# BPHS — House classifications
KENDRA_HOUSES = [1, 4, 7, 10]          # angular — most powerful
TRIKONA_HOUSES = [1, 5, 9]             # trinal — most auspicious
DUSTHANA_HOUSES = [6, 8, 12]           # malefic houses
UPACHAYA_HOUSES = [3, 6, 10, 11]       # houses of growth
MARAKA_HOUSES = [2, 7]                 # death-inflicting

# BPHS Ch. 11–15 — Core significations of each bhava
HOUSE_SIGNIFICATIONS = {
    1:  ["self", "body", "personality", "vitality", "fame", "complexion", "head", "birth"],
    2:  ["wealth", "family", "speech", "face", "food", "right eye", "early education", "accumulated resources"],
    3:  ["courage", "younger siblings", "short journeys", "communication", "arms/shoulders", "servants", "fine arts"],
    4:  ["mother", "home", "property/land", "vehicles", "education", "happiness", "heart", "domestic peace"],
    5:  ["children", "intelligence", "past merit (purva punya)", "romance", "speculation", "stomach", "mantra"],
    6:  ["enemies", "disease", "debts", "service", "litigation", "maternal uncle", "intestines", "wounds"],
    7:  ["spouse", "partnerships", "foreign travel", "business", "sexual desire", "lower abdomen"],
    8:  ["longevity", "death", "legacies", "occult", "chronic disease", "obstacles", "genitals", "sudden events"],
    9:  ["dharma", "father", "guru", "higher education", "fortune", "long travel", "religion", "thighs"],
    10: ["career", "status", "authority", "government", "actions (karma)", "knees", "public life"],
    11: ["gains", "elder siblings", "income", "desires fulfilled", "left ear", "friends", "recovery from illness"],
    12: ["loss", "expenses", "moksha", "foreign lands", "left eye", "feet", "imprisonment", "bed pleasures"],
}

# BPHS — Natural karaka for each house (Sthira Karaka)
HOUSE_KARAKA = {
    1:  "Sun",
    2:  "Jupiter",
    3:  "Mars",
    4:  "Moon",
    5:  "Jupiter",
    6:  "Mars",
    7:  "Venus",
    8:  "Saturn",
    9:  "Sun",
    10: "Mercury",   # also Sun, Jupiter, Saturn
    11: "Jupiter",
    12: "Saturn",
}

# BPHS — Karaka Bhava Nashaya rule:
# When the natural karaka of a house is placed IN that same house,
# it tends to destroy the significations of that house over time.
# (e.g. Jupiter in 5th → may harm children; Venus in 7th → may harm marriage)
KARAKA_BHAVA_NASHAYA_NOTE = (
    "Per BPHS: the karaka placed in its own bhava (Karaka Bhava Nashaya) "
    "diminishes the significations of that house. This is a classical rule "
    "and must be stated when applicable."
)

# BPHS — Lord of house placed in various houses: general principle
# (abbreviated — full interpretations come from RAG over BPHS text)
HOUSE_LORD_IN_HOUSE_PRINCIPLE = {
    "kendra": "Placement of house lord in a kendra from lagna or from its own house strengthens significations.",
    "trikona": "Lord in trikona gives Raja Yoga potential and furthers dharmic significations.",
    "dusthana": "Lord in 6th, 8th, or 12th from its own house or from lagna weakens or destroys significations.",
    "11th": "Lord of any house in 11th generally gives gains and fulfillment of the house's significations.",
    "2nd": "Lord in 2nd brings wealth connected to the source house.",
}

# BPHS — Functional benefic/malefic by lagna
# Lords of kendras that are natural benefics lose some beneficence (Kendradhipati dosha).
# Lords of trikonas are always benefic regardless of natural nature.
def get_functional_nature(lagna_sign: str, planet: str) -> str:
    """
    Returns 'benefic', 'malefic', or 'neutral' for a planet given a lagna sign.
    Applies BPHS Kendradhipati dosha rule and trikona lordship rule.
    This is a simplified structural check; full interpretation requires chart context.
    """
    from bphs_agent.knowledge.bphs_rules.planets import OWN_SIGNS, NATURAL_NATURE
    signs = SIGNS
    lagna_idx = signs.index(lagna_sign)

    owned_houses = []
    for sign in OWN_SIGNS.get(planet, []):
        sign_idx = signs.index(sign)
        house_num = (sign_idx - lagna_idx) % 12 + 1
        owned_houses.append(house_num)

    if not owned_houses:
        return NATURAL_NATURE.get(planet, "neutral")

    owns_trikona = any(h in TRIKONA_HOUSES for h in owned_houses)
    owns_kendra = any(h in KENDRA_HOUSES for h in owned_houses)
    owns_dusthana = all(h in DUSTHANA_HOUSES for h in owned_houses)

    if owns_trikona:
        return "benefic"
    if owns_dusthana and not owns_kendra:
        return "malefic"
    if owns_kendra and not owns_trikona:
        nat = NATURAL_NATURE.get(planet, "neutral")
        # Kendradhipati dosha: natural benefic owning kendra loses some beneficence
        if nat == "benefic":
            return "neutral"
    return NATURAL_NATURE.get(planet, "neutral")
