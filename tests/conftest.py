import pytest
from cg_bridge import SDK_AVAILABLE

requires_sdk = pytest.mark.skipif(
    not SDK_AVAILABLE,
    reason="competition data/ not downloaded; run "
    "`kaggle competitions download -c pokemon-tcg-ai-battle -p data/raw/`",
)


@pytest.fixture(scope="session")
def card_pool():
    from deck import load_card_pool

    return load_card_pool()


@pytest.fixture(scope="session")
def sample_deck(card_pool):
    from cg_bridge import EnergyType
    from deck import build_basic_mono_deck

    return build_basic_mono_deck(card_pool, EnergyType.FIRE)
