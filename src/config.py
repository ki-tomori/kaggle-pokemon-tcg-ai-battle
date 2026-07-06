"""
Project-wide constants and paths.
All hardcoded values belong here — never inline them in other modules.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
DECKS_DIR = DATA_DIR / "decks"

# The competition's vendored `cg` SDK ships inside the downloaded dataset,
# not as an installable package — cg_bridge.py adds this to sys.path.
SDK_DIR = RAW_DIR / "sample_submission" / "sample_submission"
CARD_DATA_EN = RAW_DIR / "EN_Card_Data.csv"
CARD_DATA_JP = RAW_DIR / "JP_Card_Data.csv"

SUBMISSIONS_DIR = ROOT_DIR / "submissions"
REPORTS_DIR = ROOT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
EXPERIMENTS_DIR = ROOT_DIR / "experiments"

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
SEED = 42

# ---------------------------------------------------------------------------
# Battle rules / safety limits
# ---------------------------------------------------------------------------
DECK_SIZE = 60
# Guards against an agent/engine bug producing an unbounded match; a match
# hitting this cap is treated as aborted rather than hung forever.
MAX_ACTIONS_PER_MATCH = 3000
DEFAULT_N_MATCHES = 100
