import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Only needed for image reader (vision) and VedAstro API calls.
# All skill LLM calls now use `claude -p` via Claude Code — no API key required.
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
VEDASTRO_API_KEY: str = os.getenv("VEDASTRO_API_KEY", "")

DEFAULT_AYANAMSA: str = os.getenv("DEFAULT_AYANAMSA", "LAHIRI")

# Model used only by image_reader.py (vision call, cannot use claude -p).
# All other LLM calls go through the claude CLI.
COORDINATOR_MODEL: str = os.getenv("COORDINATOR_MODEL", "claude-sonnet-4-6")
