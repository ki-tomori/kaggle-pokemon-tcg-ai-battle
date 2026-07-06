"""
Deck construction and validation.

Deck legality here (60 cards, <=4 copies per non-basic-energy card, <=1 ACE SPEC,
unlimited Basic Energy) follows standard Pokémon TCG deckbuilding rules. These are
best-effort defaults, not yet confirmed against this competition's own rules page —
run the `competition-researcher` subagent against the official Rules tab before
relying on validate_deck() for anything beyond a smoke-test baseline deck.
"""

import csv
import logging
from pathlib import Path

from cg_bridge import CardData, CardType, EnergyType
from config import DECK_SIZE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MAX_COPIES_PER_CARD = 4


def load_card_pool() -> dict[int, CardData]:
    """Load every card the engine knows about, keyed by card ID."""
    from cg_bridge import all_card_data

    return {card.cardId: card for card in all_card_data()}


def build_basic_mono_deck(
    card_pool: dict[int, CardData],
    energy_type: EnergyType,
    n_basic_lines: int = 6,
) -> list[int]:
    """Build the simplest legal deck: a handful of Basic Pokémon of one energy type,
    padded out with that type's Basic Energy. Not competitive — a baseline smoke test.

    n_basic_lines defaults to 6 (24 Pokémon + 36 Energy): with only 1-3 lines the
    deck is so thin that most matches end from running out of Pokémon or decking
    out rather than from combat decisions, which is a weak signal for comparing agents.
    """
    basics = [
        card
        for card in card_pool.values()
        if card.basic and card.energyType == energy_type and card.cardType == CardType.POKEMON
    ]
    if not basics:
        raise ValueError(f"No Basic Pokémon found for energy type {energy_type!r}.")
    chosen = basics[:n_basic_lines]

    energy_cards = [
        card
        for card in card_pool.values()
        if card.cardType == CardType.BASIC_ENERGY and card.energyType == energy_type
    ]
    if not energy_cards:
        raise ValueError(f"No Basic Energy card found for energy type {energy_type!r}.")
    energy_card_id = energy_cards[0].cardId

    deck: list[int] = []
    for card in chosen:
        deck.extend([card.cardId] * MAX_COPIES_PER_CARD)

    deck.extend([energy_card_id] * (DECK_SIZE - len(deck)))
    return deck[:DECK_SIZE]


def validate_deck(deck: list[int], card_pool: dict[int, CardData]) -> list[str]:
    """Return a list of legality violations; empty list means the deck looks legal."""
    violations: list[str] = []

    if len(deck) != DECK_SIZE:
        violations.append(f"Deck has {len(deck)} cards, expected {DECK_SIZE}.")

    unknown_ids = {card_id for card_id in deck if card_id not in card_pool}
    if unknown_ids:
        violations.append(f"Unknown card IDs: {sorted(unknown_ids)}")

    has_basic_pokemon = any(
        card_pool[card_id].basic and card_pool[card_id].cardType == CardType.POKEMON
        for card_id in deck
        if card_id in card_pool
    )
    if not has_basic_pokemon:
        violations.append("Deck contains no Basic Pokémon.")

    counts: dict[int, int] = {}
    for card_id in deck:
        counts[card_id] = counts.get(card_id, 0) + 1

    for card_id, count in counts.items():
        card = card_pool.get(card_id)
        if card is None:
            continue
        if card.cardType == CardType.BASIC_ENERGY:
            continue
        if card.aceSpec and count > 1:
            violations.append(f"ACE SPEC card {card_id} ({card.name}) appears {count} times, max 1.")
        elif count > MAX_COPIES_PER_CARD:
            violations.append(
                f"Card {card_id} ({card.name}) appears {count} times, max {MAX_COPIES_PER_CARD}."
            )

    return violations


def save_deck_csv(deck: list[int], path: Path | str) -> None:
    """Write one card ID per line, matching the format the competition's sample agent reads."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        for card_id in deck:
            writer.writerow([card_id])
    logger.info("Saved %d-card deck to %s", len(deck), path)


def load_deck_csv(path: Path | str) -> list[int]:
    """Read a deck previously written by save_deck_csv()."""
    with open(path) as f:
        return [int(row[0]) for row in csv.reader(f) if row]


def main() -> None:
    card_pool = load_card_pool()
    logger.info("Loaded %d cards.", len(card_pool))
    deck = build_basic_mono_deck(card_pool, EnergyType.FIRE)
    violations = validate_deck(deck, card_pool)
    if violations:
        for v in violations:
            logger.warning("Deck violation: %s", v)
    else:
        logger.info("Deck is legal.")


if __name__ == "__main__":
    main()
