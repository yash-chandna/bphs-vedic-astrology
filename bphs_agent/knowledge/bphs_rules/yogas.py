"""
BPHS yoga definitions — trigger conditions for detection.
Sources: BPHS Ch. 35–40 (Yoga Phala), Ch. 36 (Raja Yogas), Ch. 37 (Dhana Yogas),
         Ch. 38 (Arista Yogas), Ch. 39 (Pancha Mahapurusha Yogas).

Each yoga is a dict with:
  name       : canonical name
  type       : raja / dhana / arista / pancha_mahapurusha / nabhasa / chandra / other
  bphs_ref   : chapter + sloka reference string
  description: plain-English rule (what must be true in the chart)
  strength   : "strong" | "moderate" | "weak" (how much weight to give when assessing)
"""

YOGAS: list[dict] = [

    # ── RAJA YOGAS (BPHS Ch. 36) ──────────────────────────────────────────
    {
        "name": "Raja Yoga (Kendra-Trikona)",
        "type": "raja",
        "bphs_ref": "BPHS Ch. 36",
        "description": (
            "Lords of a kendra (1, 4, 7, 10) and a trikona (1, 5, 9) are conjunct, "
            "exchange signs (parivartana), or aspect each other. The stronger the lords "
            "and the closer to an angle, the more powerful the yoga."
        ),
        "strength": "strong",
    },
    {
        "name": "Dharma-Karmadhipati Yoga",
        "type": "raja",
        "bphs_ref": "BPHS Ch. 36",
        "description": (
            "Lord of the 9th (dharma) and lord of the 10th (karma) conjoin, "
            "mutually aspect, or exchange signs. One of the most powerful Raja Yogas."
        ),
        "strength": "strong",
    },
    {
        "name": "Pancha Mahapurusha Yoga",
        "type": "pancha_mahapurusha",
        "bphs_ref": "BPHS Ch. 39",
        "description": (
            "Mars, Mercury, Jupiter, Venus, or Saturn is in its own sign or exaltation "
            "AND placed in a kendra (1, 4, 7, 10) from the lagna or from the Moon. "
            "Specific names: Ruchaka (Mars), Bhadra (Mercury), Hamsa (Jupiter), "
            "Malavya (Venus), Sasa (Saturn)."
        ),
        "strength": "strong",
    },

    # ── DHANA YOGAS (BPHS Ch. 37) ─────────────────────────────────────────
    {
        "name": "Dhana Yoga (2nd-11th lords)",
        "type": "dhana",
        "bphs_ref": "BPHS Ch. 37",
        "description": (
            "Lords of 2nd and 11th conjoin, exchange, or aspect each other, "
            "or one is placed in the other's house. Indicates wealth accumulation."
        ),
        "strength": "strong",
    },
    {
        "name": "Dhana Yoga (Lagna-2nd-11th)",
        "type": "dhana",
        "bphs_ref": "BPHS Ch. 37",
        "description": (
            "Lagna lord is associated with the lords of 2nd and/or 11th. "
            "The native earns wealth through own efforts."
        ),
        "strength": "moderate",
    },
    {
        "name": "Lakshmi Yoga",
        "type": "dhana",
        "bphs_ref": "BPHS Ch. 37",
        "description": (
            "Lord of 9th is in its own or exaltation sign, placed in a kendra or trikona. "
            "Venus (natural significator of wealth and beauty) is strong. "
            "Gives great fortune, wealth, and prosperity."
        ),
        "strength": "strong",
    },

    # ── ARISTA YOGAS — afflictions (BPHS Ch. 38) ─────────────────────────
    {
        "name": "Kemadruma Yoga",
        "type": "arista",
        "bphs_ref": "BPHS Ch. 38",
        "description": (
            "No planet (except the Sun and nodes) is in the 2nd or 12th from the Moon, "
            "AND no planet aspects the Moon. Causes poverty, misfortune, and mental anguish. "
            "Cancelled if Moon is in a kendra from lagna or if a planet is in a kendra."
        ),
        "strength": "strong",
    },
    {
        "name": "Balarishta (early life danger)",
        "type": "arista",
        "bphs_ref": "BPHS Ch. 38",
        "description": (
            "Moon afflicted by malefics (especially in 6th, 8th, 12th) with lagna lord weak, "
            "or Moon in kendra/trikona hemmed by malefics. Indicates danger in childhood. "
            "Classical BPHS rules for longevity assessment."
        ),
        "strength": "strong",
    },
    {
        "name": "Daridra Yoga (poverty)",
        "type": "arista",
        "bphs_ref": "BPHS Ch. 38",
        "description": (
            "Lord of 11th is in a dusthana (6, 8, 12) and associated with malefics, "
            "or lagna lord is weak and in a dusthana with malefics. "
            "Brings financial hardship."
        ),
        "strength": "moderate",
    },

    # ── NABHASA YOGAS (BPHS Ch. 35) ──────────────────────────────────────
    {
        "name": "Rajju Yoga",
        "type": "nabhasa",
        "bphs_ref": "BPHS Ch. 35",
        "description": "All planets in movable signs (Aries, Cancer, Libra, Capricorn). Indicates wandering, travel.",
        "strength": "moderate",
    },
    {
        "name": "Musala Yoga",
        "type": "nabhasa",
        "bphs_ref": "BPHS Ch. 35",
        "description": "All planets in fixed signs (Taurus, Leo, Scorpio, Aquarius). Fixed in one place, determined.",
        "strength": "moderate",
    },
    {
        "name": "Nala Yoga",
        "type": "nabhasa",
        "bphs_ref": "BPHS Ch. 35",
        "description": "All planets in dual signs (Gemini, Virgo, Sagittarius, Pisces). Skilled in many arts.",
        "strength": "moderate",
    },
    {
        "name": "Gada Yoga",
        "type": "nabhasa",
        "bphs_ref": "BPHS Ch. 35",
        "description": "All planets in two adjacent kendras (e.g. 1st and 4th). Industrious, accumulates wealth.",
        "strength": "moderate",
    },

    # ── CHANDRA (MOON) YOGAS ──────────────────────────────────────────────
    {
        "name": "Sunapha Yoga",
        "type": "chandra",
        "bphs_ref": "BPHS Ch. 35",
        "description": (
            "A planet other than the Sun is in the 2nd from the Moon. "
            "Gives self-earned wealth, intelligence, and status."
        ),
        "strength": "moderate",
    },
    {
        "name": "Anapha Yoga",
        "type": "chandra",
        "bphs_ref": "BPHS Ch. 35",
        "description": (
            "A planet other than the Sun is in the 12th from the Moon. "
            "Gives physical health, fame, and spiritual inclination."
        ),
        "strength": "moderate",
    },
    {
        "name": "Durudhara Yoga",
        "type": "chandra",
        "bphs_ref": "BPHS Ch. 35",
        "description": (
            "Planets (other than the Sun) are both in the 2nd and 12th from the Moon. "
            "Combines Sunapha + Anapha. Gives great wealth and status."
        ),
        "strength": "strong",
    },

    # ── VIPARITA RAJA YOGA (BPHS Ch. 36) ─────────────────────────────────
    {
        "name": "Viparita Raja Yoga",
        "type": "raja",
        "bphs_ref": "BPHS Ch. 36",
        "description": (
            "Lords of the three dusthana houses (6, 8, 12) are placed in each other's houses "
            "or conjoin in a dusthana, without being associated with the lagna lord or trikona lords. "
            "Turns misfortune into sudden rise — the native gains after a period of struggle or loss."
        ),
        "strength": "strong",
    },

    # ── NEECHA BHANGA RAJA YOGA ───────────────────────────────────────────
    {
        "name": "Neecha Bhanga Raja Yoga",
        "type": "raja",
        "bphs_ref": "BPHS Ch. 36",
        "description": (
            "A debilitated planet's debilitation is cancelled by one of several conditions: "
            "(1) the lord of the debilitation sign aspects the debilitated planet; "
            "(2) the planet that would be exalted in that sign is in a kendra; "
            "(3) the debilitated planet's dispositor is in a kendra from lagna or Moon; "
            "(4) the lord of the debilitated planet's navamsha sign is in a kendra. "
            "When cancelled, the planet becomes a source of Raja Yoga."
        ),
        "strength": "strong",
    },

    # ── GAJAKESARI YOGA ───────────────────────────────────────────────────
    {
        "name": "Gajakesari Yoga",
        "type": "raja",
        "bphs_ref": "BPHS Ch. 36",
        "description": (
            "Jupiter is in a kendra (1, 4, 7, 10) from the Moon. "
            "Gives fame, wisdom, wealth, and long life. Strength depends on Jupiter's dignity."
        ),
        "strength": "moderate",
    },

    # ── PARIVARTANA YOGA ──────────────────────────────────────────────────
    {
        "name": "Parivartana Yoga (sign exchange)",
        "type": "other",
        "bphs_ref": "BPHS Ch. 36",
        "description": (
            "Two planets are each placed in the other's own sign (mutual exchange). "
            "Treated as if both planets are conjunct in both houses. "
            "Between kendra/trikona lords: equivalent to a Raja Yoga conjunction."
        ),
        "strength": "strong",
    },

    # ── KUJA DOSHA (MANGAL DOSHA) ─────────────────────────────────────────
    {
        "name": "Kuja Dosha (Mangal Dosha)",
        "type": "arista",
        "bphs_ref": "BPHS Ch. 38",
        "description": (
            "Mars is placed in the 1st, 2nd, 4th, 7th, 8th, or 12th house from the lagna, Moon, or Venus. "
            "Afflicts marital harmony. Cancelled if Mars is in its own sign, exalted, with a benefic, "
            "or if the spouse also has Kuja Dosha."
        ),
        "strength": "moderate",
    },
]

# Quick lookup by yoga type
def get_yogas_by_type(yoga_type: str) -> list[dict]:
    return [y for y in YOGAS if y["type"] == yoga_type]

# All yoga names for reference
YOGA_NAMES = [y["name"] for y in YOGAS]
