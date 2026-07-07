"""
Bridge to the competition's vendored `cg` SDK (data/raw/sample_submission/sample_submission/cg).

The SDK is not an installable package — it ships inside the downloaded, gitignored
competition dataset. This module is the single place that adds it to sys.path so the
rest of src/ can `import cg_bridge` without knowing where the data lives on disk.

Importing this module never raises even if the dataset hasn't been downloaded yet;
call check_sdk_available() to test first (used by tests/ to skip SDK-dependent cases).
"""

import logging
import sys

from config import SDK_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def check_sdk_available() -> bool:
    """True if the competition dataset has been downloaded and `cg` imports cleanly."""
    if str(SDK_DIR) not in sys.path:
        sys.path.insert(0, str(SDK_DIR))
    try:
        import cg.api  # noqa: F401
        import cg.game  # noqa: F401
    except ImportError:
        return False
    return True


SDK_AVAILABLE = check_sdk_available()

if SDK_AVAILABLE:
    from cg.api import (  # noqa: F401 -- re-exported for the rest of src/ to import from cg_bridge
        AreaType,
        Attack,
        Card,
        CardData,
        CardType,
        EnergyType,
        Log,
        LogType,
        Observation,
        Option,
        OptionType,
        Pokemon,
        PlayerState,
        SearchState,
        SelectContext,
        SelectData,
        SelectType,
        Skill,
        SpecialConditionType,
        State,
        all_attack,
        all_card_data,
        search_begin,
        search_end,
        search_release,
        search_step,
        to_observation_class,
    )
    from cg.game import battle_finish, battle_select, battle_start, visualize_data  # noqa: F401
else:
    logger.warning(
        "cg SDK not found at %s — download the competition data first: "
        "kaggle competitions download -c pokemon-tcg-ai-battle -p data/raw/",
        SDK_DIR,
    )


def main() -> None:
    if not SDK_AVAILABLE:
        logger.error("cg SDK unavailable at %s", SDK_DIR)
        return
    cards = all_card_data()
    logger.info("cg SDK loaded from %s (%d cards in the engine's card database)", SDK_DIR, len(cards))


if __name__ == "__main__":
    main()
