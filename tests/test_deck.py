import pytest
from conftest import requires_sdk
from config import DECK_SIZE
from deck import (
    build_basic_mono_deck,
    build_optimized_mono_deck,
    load_attack_pool,
    load_deck_csv,
    save_deck_csv,
    validate_deck,
)


@requires_sdk
def test_build_basic_mono_deck_is_legal(card_pool):
    from cg_bridge import EnergyType

    deck = build_basic_mono_deck(card_pool, EnergyType.FIRE)
    assert len(deck) == DECK_SIZE
    assert validate_deck(deck, card_pool) == []


@requires_sdk
def test_save_load_roundtrip(tmp_path, sample_deck):
    path = tmp_path / "deck.csv"
    save_deck_csv(sample_deck, path)
    loaded = load_deck_csv(path)
    assert loaded == sample_deck


@requires_sdk
def test_validate_deck_flags_wrong_size(card_pool, sample_deck):
    violations = validate_deck(sample_deck[:-1], card_pool)
    assert any("60" in v or str(DECK_SIZE) in v for v in violations)


@requires_sdk
def test_build_optimized_mono_deck_is_legal(card_pool):
    from cg_bridge import EnergyType

    attack_pool = load_attack_pool()
    deck = build_optimized_mono_deck(card_pool, attack_pool, EnergyType.FIRE)
    assert len(deck) == DECK_SIZE
    assert validate_deck(deck, card_pool) == []


@requires_sdk
def test_validate_deck_flags_multiple_ace_specs(card_pool):
    ace_specs = [c for c in card_pool.values() if c.aceSpec][:2]
    if len(ace_specs) < 2:
        pytest.skip("card pool doesn't have 2+ distinct ACE SPEC cards to test with")
    deck = [ace_specs[0].cardId, ace_specs[1].cardId] + [ace_specs[0].cardId] * (DECK_SIZE - 2)
    violations = validate_deck(deck, card_pool)
    assert any("ACE SPEC" in v for v in violations)
