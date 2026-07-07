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

from cg_bridge import Attack, CardData, CardType, EnergyType
from config import DECK_SIZE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MAX_COPIES_PER_CARD = 4
N_DRAW_SUPPORT_SLOTS = 8


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


def load_attack_pool() -> dict[int, Attack]:
    """Load every attack the engine knows about, keyed by attack ID."""
    from cg_bridge import all_attack

    return {atk.attackId: atk for atk in all_attack()}


def _attack_efficiency(card: CardData, attack_pool: dict[int, Attack]) -> float:
    """Best damage-per-energy across a card's attacks; 0 if it has none we can price."""
    best = 0.0
    for attack_id in card.attacks:
        atk = attack_pool.get(attack_id)
        if atk is None or not atk.energies:
            continue
        best = max(best, atk.damage / len(atk.energies))
    return best


def build_optimized_mono_deck(
    card_pool: dict[int, CardData],
    attack_pool: dict[int, Attack],
    energy_type: EnergyType,
    n_lines: int = 6,
    n_draw_slots: int = N_DRAW_SUPPORT_SLOTS,
) -> list[int]:
    """Build a mono-energy deck like build_basic_mono_deck(), but pick Basic Pokémon
    by damage-per-energy efficiency (best first) instead of arbitrary pool order, and
    add a handful of card-draw Item/Supporter cards to reduce decking out.

    Experiment 001 found >50% of matches were decided by decking out rather than
    combat — this targets that directly, on top of picking stronger attackers.
    """
    basics = [
        card
        for card in card_pool.values()
        if card.basic and card.energyType == energy_type and card.cardType == CardType.POKEMON
    ]
    if not basics:
        raise ValueError(f"No Basic Pokémon found for energy type {energy_type!r}.")
    basics.sort(key=lambda c: (_attack_efficiency(c, attack_pool), -c.retreatCost, c.hp), reverse=True)
    chosen = basics[:n_lines]

    deck: list[int] = []
    for card in chosen:
        deck.extend([card.cardId] * MAX_COPIES_PER_CARD)

    return _fill_draw_and_energy(deck, card_pool, energy_type, n_draw_slots)


def _draw_support_cards(card_pool: dict[int, CardData]) -> list[CardData]:
    """Item/Supporter cards whose text mentions "draw", excluding ACE SPEC (its
    1-per-deck-total limit doesn't mix cleanly with picking several distinct cards)."""
    return [
        card
        for card in card_pool.values()
        if card.cardType in (CardType.ITEM, CardType.SUPPORTER)
        and not card.aceSpec
        and any("draw" in skill.text.lower() for skill in card.skills)
    ]


def _fill_draw_and_energy(
    deck: list[int],
    card_pool: dict[int, CardData],
    energy_type: EnergyType,
    n_draw_slots: int,
) -> list[int]:
    """Top up a partially-built deck (Pokémon lines already added) with draw
    support first, then Basic Energy, up to DECK_SIZE."""
    draw_cards = _draw_support_cards(card_pool)
    remaining_for_draw = min(n_draw_slots, DECK_SIZE - len(deck))
    n_draw_cards = max(1, len(draw_cards[: (remaining_for_draw // MAX_COPIES_PER_CARD) or 1]))
    per_card = max(1, remaining_for_draw // n_draw_cards) if draw_cards else 0
    for card in draw_cards[:n_draw_cards]:
        take = min(MAX_COPIES_PER_CARD, per_card, DECK_SIZE - len(deck))
        deck.extend([card.cardId] * take)

    energy_cards = [
        card
        for card in card_pool.values()
        if card.cardType == CardType.BASIC_ENERGY and card.energyType == energy_type
    ]
    if not energy_cards:
        raise ValueError(f"No Basic Energy card found for energy type {energy_type!r}.")
    deck.extend([energy_cards[0].cardId] * (DECK_SIZE - len(deck)))
    return deck[:DECK_SIZE]


def _evolution_lines(
    card_pool: dict[int, CardData],
    attack_pool: dict[int, Attack],
    energy_type: EnergyType,
) -> list[tuple[CardData, CardData]]:
    """(basic, stage1) pairs of the given energy type where the Stage1's
    evolvesFrom matches a Basic actually present in the card pool, ranked by
    the Stage1's damage-per-energy efficiency (best first).

    Real opponents observed via Kaggle replay analysis (experiment 007) run
    evolved, Tool-equipped Pokémon dealing far more damage per turn than a
    Basic-only deck can match (e.g. a single 170-damage hit) -- Stage1
    attackers here reach 2-4x the efficiency of the best Basic attackers.
    """
    basics_by_name = {
        c.name: c
        for c in card_pool.values()
        if c.basic and c.cardType == CardType.POKEMON and c.energyType == energy_type
    }
    stage1s = [
        c
        for c in card_pool.values()
        if c.stage1
        and c.cardType == CardType.POKEMON
        and c.energyType == energy_type
        and c.evolvesFrom in basics_by_name
    ]
    lines = [(basics_by_name[c.evolvesFrom], c) for c in stage1s]
    lines.sort(key=lambda pair: _attack_efficiency(pair[1], attack_pool), reverse=True)
    return lines


def build_evolution_line_deck(
    card_pool: dict[int, CardData],
    attack_pool: dict[int, Attack],
    energy_type: EnergyType,
    n_lines: int = 2,
    n_draw_slots: int = N_DRAW_SUPPORT_SLOTS,
) -> list[int]:
    """Build a mono-energy deck around n_lines distinct Basic->Stage1 evolution
    lines (4 copies of each stage), picked by the Stage1 attack's damage-per-
    energy efficiency, padded with draw support then Basic Energy.

    Unlike build_optimized_mono_deck() (Basic-only), this can actually compete
    with the evolved, Tool-equipped decks real opponents use — see
    reports/009_evolution_deck.md. Requires the agent to handle EVOLVE options,
    which the engine presents fully-specified (source + target already chosen)
    within the same MAIN select, so no extra agent-side lookup is needed.
    """
    lines = _evolution_lines(card_pool, attack_pool, energy_type)
    if not lines:
        raise ValueError(f"No Basic->Stage1 evolution line found for energy type {energy_type!r}.")

    # A Basic can be the pre-evolution of more than one Stage1 card (reprints/
    # alternate forms sharing a name); skip lines that would reuse a Basic
    # already chosen, since 4+4 copies of the same Basic ID would break the
    # per-card copy limit.
    chosen: list[tuple[CardData, CardData]] = []
    used_basic_ids: set[int] = set()
    for basic, stage1 in lines:
        if basic.cardId in used_basic_ids:
            continue
        chosen.append((basic, stage1))
        used_basic_ids.add(basic.cardId)
        if len(chosen) == n_lines:
            break

    deck: list[int] = []
    for basic, stage1 in chosen:
        deck.extend([basic.cardId] * MAX_COPIES_PER_CARD)
        deck.extend([stage1.cardId] * MAX_COPIES_PER_CARD)

    return _fill_draw_and_energy(deck, card_pool, energy_type, n_draw_slots)


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

    total_ace_spec = 0
    for card_id, count in counts.items():
        card = card_pool.get(card_id)
        if card is None:
            continue
        if card.aceSpec:
            total_ace_spec += count
        if card.cardType == CardType.BASIC_ENERGY:
            continue
        if not card.aceSpec and count > MAX_COPIES_PER_CARD:
            violations.append(
                f"Card {card_id} ({card.name}) appears {count} times, max {MAX_COPIES_PER_CARD}."
            )

    # The ACE SPEC limit is 1 card total across the whole deck, not 1 per card ID.
    if total_ace_spec > 1:
        violations.append(f"Deck has {total_ace_spec} ACE SPEC cards total, max 1 across the whole deck.")

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


def load_deck_from_episode_replay(replay_json_path: Path | str, agent_index: int = 0) -> list[int]:
    """Extract a real 60-card deck list from a downloaded top-episode replay
    JSON (Kaggle's official CC0-licensed `pokemon-tcg-ai-battle-episodes-*`
    datasets — see experiments/011-meta-deck/config.yaml for the exact episode
    used). The deck-selection action (60 card IDs) is the `action` field of
    the *second* step (index 1); the first step is the initial `select: None`
    observation with an empty action, before either player has submitted a deck.
    """
    import json

    with open(replay_json_path) as f:
        replay = json.load(f)
    deck = replay["steps"][1][agent_index]["action"]
    if len(deck) != DECK_SIZE:
        raise ValueError(f"Expected a {DECK_SIZE}-card deck action, got {len(deck)} cards.")
    return deck


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
