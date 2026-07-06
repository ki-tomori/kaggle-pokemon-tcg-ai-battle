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


# The 8 standard TCG energy types; excludes COLORLESS/RAINBOW/TEAM_ROCKET, which
# aren't attacker-defining types in the same sense (no "mono-Colorless" archetype).
_STANDARD_ENERGY_TYPES = [
    EnergyType.GRASS,
    EnergyType.FIRE,
    EnergyType.WATER,
    EnergyType.LIGHTNING,
    EnergyType.PSYCHIC,
    EnergyType.FIGHTING,
    EnergyType.DARKNESS,
    EnergyType.METAL,
]


def select_best_energy_type(
    card_pool: dict[int, CardData],
    attack_pool: dict[int, Attack],
    n_lines: int = 6,
) -> EnergyType:
    """Pick whichever standard energy type has the strongest available Basic
    Pokémon lines, by summing the top n_lines basics' damage-per-energy efficiency.
    Requires at least n_lines Basic Pokémon and a Basic Energy card of that type."""
    best_type: EnergyType | None = None
    best_score = -1.0
    for energy_type in _STANDARD_ENERGY_TYPES:
        basics = [
            card
            for card in card_pool.values()
            if card.basic and card.energyType == energy_type and card.cardType == CardType.POKEMON
        ]
        if len(basics) < n_lines:
            continue
        has_energy_card = any(
            card.cardType == CardType.BASIC_ENERGY and card.energyType == energy_type
            for card in card_pool.values()
        )
        if not has_energy_card:
            continue

        top_effs = sorted((_attack_efficiency(c, attack_pool) for c in basics), reverse=True)[:n_lines]
        score = sum(top_effs)
        if score > best_score:
            best_score = score
            best_type = energy_type

    if best_type is None:
        raise ValueError("No standard energy type has enough Basic Pokémon + a Basic Energy card.")
    logger.info("Best energy type by static efficiency score: %s (score=%.2f)", best_type, best_score)
    return best_type


def select_best_energy_type_by_selfplay(
    card_pool: dict[int, CardData],
    attack_pool: dict[int, Attack],
    agent_fn,
    n_lines: int = 6,
    n_matches: int = 40,
    seed: int = 0,
) -> EnergyType:
    """Pick the energy type empirically: build a mono deck per standard type and
    round-robin them against each other with agent_fn on both sides, picking the
    type with the best overall win rate.

    select_best_energy_type()'s static damage-per-energy score is a poor proxy —
    on this card pool it picked Fighting as "best," but Fighting lost ~70-80% of
    self-play matches against a Fire or Water deck. Empirical self-play is slower
    (a few seconds for ~30 matchups at n_matches=40) but doesn't have that failure mode.
    """
    from arena import play_n_matches  # deferred: arena imports deck, avoid a circular import

    decks: dict[EnergyType, list[int]] = {}
    for energy_type in _STANDARD_ENERGY_TYPES:
        try:
            deck = build_optimized_mono_deck(card_pool, attack_pool, energy_type, n_lines)
        except ValueError:
            continue
        if validate_deck(deck, card_pool):
            continue
        decks[energy_type] = deck

    if not decks:
        raise ValueError("No standard energy type produced a legal deck.")

    win_counts = {et: 0 for et in decks}
    match_counts = {et: 0 for et in decks}
    types = list(decks)
    for i, type_a in enumerate(types):
        for type_b in types[i + 1 :]:
            stats = play_n_matches(agent_fn, agent_fn, decks[type_a], decks[type_b], n=n_matches, seed=seed)
            decided = stats.wins_a + stats.wins_b + stats.draws
            win_counts[type_a] += stats.wins_a
            win_counts[type_b] += stats.wins_b
            match_counts[type_a] += decided
            match_counts[type_b] += decided

    win_rates = {et: (win_counts[et] / match_counts[et] if match_counts[et] else 0.0) for et in decks}
    logger.info("Round-robin win rates by energy type: %s", win_rates)
    return max(win_rates, key=win_rates.get)


def build_best_mono_deck(
    card_pool: dict[int, CardData],
    attack_pool: dict[int, Attack],
    agent_fn,
    n_lines: int = 6,
    n_draw_slots: int = N_DRAW_SUPPORT_SLOTS,
    n_matches: int = 40,
    seed: int = 0,
) -> list[int]:
    """build_optimized_mono_deck(), but auto-picks the energy type via empirical
    self-play round-robin instead of the caller specifying one — see
    select_best_energy_type_by_selfplay()."""
    energy_type = select_best_energy_type_by_selfplay(
        card_pool, attack_pool, agent_fn, n_lines, n_matches, seed
    )
    return build_optimized_mono_deck(card_pool, attack_pool, energy_type, n_lines, n_draw_slots)


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

    # Excludes ACE SPEC cards: the ACE SPEC limit is 1 total across the whole deck
    # (not 1 per card ID), which doesn't mix cleanly with picking several distinct
    # draw cards below — simplest to just not rely on ACE SPEC draw support here.
    draw_cards = [
        card
        for card in card_pool.values()
        if card.cardType in (CardType.ITEM, CardType.SUPPORTER)
        and not card.aceSpec
        and any("draw" in skill.text.lower() for skill in card.skills)
    ]

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

    remaining_for_draw = min(n_draw_slots, DECK_SIZE - len(deck))
    n_draw_cards = max(1, len(draw_cards[: (remaining_for_draw // MAX_COPIES_PER_CARD) or 1]))
    per_card = max(1, remaining_for_draw // n_draw_cards) if draw_cards else 0
    for card in draw_cards[:n_draw_cards]:
        take = 1 if card.aceSpec else min(MAX_COPIES_PER_CARD, per_card, DECK_SIZE - len(deck))
        deck.extend([card.cardId] * take)

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
