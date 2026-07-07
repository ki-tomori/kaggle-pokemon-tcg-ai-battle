"""
Greedy heuristic agent v2: adds lethal detection and damage-aware attack scoring
(including a crude weakness/resistance adjustment) on top of heuristic_agent's
fixed action-type priority. Still no multi-turn lookahead.

Sequencing note: a MAIN select can legally offer ATTACK alongside setup actions
(ATTACH/EVOLVE/PLAY/ABILITY) at the same decision point when energy was already
attached in a prior turn -- attacking ends the turn, so taking a setup action
first and attacking afterward is free value an earlier version of this agent
was leaving on the table by always attacking as soon as it was legal. Measured
at ~45% of this agent's own MAIN decisions in self-play. Non-lethal ATTACK is
scored below the setup-action tier for this reason; a lethal attack always
still wins immediately regardless of what else is offered.

Targeting note: richer decks (evolution lines, gust-style Supporters) present
CARD selects where we choose an opponent's Pokemon, not just our own -- e.g.
forcing a benched Pokemon active (SWITCH/TO_ACTIVE with the option's
playerIndex pointing at the opponent). This previously fell back to a flat
default score (picking whichever option happened to be listed first); see
_gust_target_score. Energy/Tool attachment (_attach_target_score) similarly
targets whichever of our own Pokemon most needs it, instead of scoring every
ATTACH option identically. A DAMAGE-context targeting heuristic (prefer the
opponent's lowest-HP Pokemon when a card effect lets us choose who takes
damage) was also tried and measurably lost to the version without it
(experiment 012) -- removed rather than kept on a plausible-sounding but
empirically-negative rationale.

Kaggle-portable: only stdlib + `cg.api` imports. This file is copied verbatim into
a submission's main.py by src/package_submission.py — do not import from `src`.
"""

import os

from cg.api import (
    AreaType,
    Observation,
    Option,
    OptionType,
    SelectContext,
    all_attack,
    all_card_data,
    to_observation_class,
)

_ATTACKS = {atk.attackId: atk for atk in all_attack()}
_CARDS = {card.cardId: card for card in all_card_data()}

# Higher score = preferred. Options not listed fall back to a neutral default.
_PRIORITY: dict[OptionType, float] = {
    OptionType.EVOLVE: 90,
    OptionType.ATTACH: 70,
    OptionType.PLAY: 65,
    OptionType.ABILITY: 55,
    OptionType.YES: 40,
    OptionType.NO: 30,
    OptionType.RETREAT: 5,
    OptionType.END: 0,
}
_DEFAULT_SCORE = 20.0
_LETHAL_BONUS = 1000.0
_CRITICAL_HP_FRACTION = 0.3
_RETREAT_WHEN_CRITICAL_SCORE = 95.0
# Non-lethal ATTACK sits just below ABILITY (55) so setup actions this turn
# (EVOLVE/ATTACH/PLAY/ABILITY) all happen before attacking ends the turn.
_NONLETHAL_ATTACK_BASE = 45.0
_NONLETHAL_ATTACK_DAMAGE_CAP = 90


def _read_deck_csv() -> list[int]:
    """Read deck.csv. Returns a list of 60 card IDs in the deck."""
    file_path = "deck.csv"
    if not os.path.exists(file_path):
        file_path = "/kaggle_simulations/agent/deck.csv"
    with open(file_path) as f:
        lines = f.read().splitlines()
    return [int(line) for line in lines[:60]]


def _opponent_active_hp(obs: Observation) -> int | None:
    state = obs.current
    opponent = state.players[1 - state.yourIndex]
    if not opponent.active or opponent.active[0] is None:
        return None
    return opponent.active[0].hp


def _attack_damage(option: Option, obs: Observation) -> int:
    """Estimated damage for an ATTACK option, with a crude weakness/resistance bump."""
    attack = _ATTACKS.get(option.attackId)
    if attack is None:
        return 0
    damage = attack.damage

    state = obs.current
    my_active = state.players[state.yourIndex].active
    opp_active = state.players[1 - state.yourIndex].active
    if not my_active or my_active[0] is None or not opp_active or opp_active[0] is None:
        return damage

    my_card = _CARDS.get(my_active[0].id)
    opp_card = _CARDS.get(opp_active[0].id)
    if my_card is None or opp_card is None:
        return damage

    if opp_card.weakness is not None and opp_card.weakness == my_card.energyType:
        damage *= 2
    if opp_card.resistance is not None and opp_card.resistance == my_card.energyType:
        damage = max(0, damage - 20)
    return damage


def _active_is_critical(obs: Observation) -> bool:
    state = obs.current
    active = state.players[state.yourIndex].active
    if not active or active[0] is None or not active[0].maxHp:
        return False
    return active[0].hp / active[0].maxHp <= _CRITICAL_HP_FRACTION


def _healthiest_bench_available(obs: Observation) -> bool:
    state = obs.current
    bench = state.players[state.yourIndex].bench
    return any(p is not None and p.hp > 0 for p in bench)


def _switch_target_score(option: Option, obs: Observation) -> float:
    """When choosing which of our own bench Pokemon becomes active, prefer the healthiest."""
    state = obs.current
    me = state.players[state.yourIndex]
    if option.area == AreaType.BENCH and option.index is not None and 0 <= option.index < len(me.bench):
        pokemon = me.bench[option.index]
        if pokemon is not None and pokemon.maxHp:
            return pokemon.hp / pokemon.maxHp * 100
    return _DEFAULT_SCORE


_GUST_LOW_HP_THRESHOLD = 60.0


def _gust_target_score(option: Option, obs: Observation) -> float:
    """When a card effect (e.g. a Boss's-Orders-style Supporter) lets us force
    one of the opponent's benched Pokemon into their Active Spot, prefer a
    target we can likely follow up on: low HP (near a knockout), still a
    Basic (denies a future evolution), already energized (denies their
    investment), or a high retreat cost (harder for them to swap back out).
    Per Discussion advice on this exact card category."""
    state = obs.current
    opponent = state.players[1 - state.yourIndex]
    if not (
        option.area == AreaType.BENCH and option.index is not None and 0 <= option.index < len(opponent.bench)
    ):
        return _DEFAULT_SCORE
    pokemon = opponent.bench[option.index]
    if pokemon is None:
        return _DEFAULT_SCORE

    score = 0.0
    if pokemon.hp <= _GUST_LOW_HP_THRESHOLD:
        score += 50.0
    if pokemon.energies:
        score += 20.0
    card = _CARDS.get(pokemon.id)
    if card is not None:
        if card.basic:
            score += 30.0
        score += card.retreatCost * 5.0
    score -= pokemon.hp * 0.1
    return score


def _energy_shortfall(pokemon_id: int, current_energy_count: int) -> int:
    """How many more energy units the card's cheapest attack needs, big number if unknown."""
    card = _CARDS.get(pokemon_id)
    if card is None or not card.attacks:
        return 999
    best_needed = 999
    for attack_id in card.attacks:
        attack = _ATTACKS.get(attack_id)
        if attack is None:
            continue
        needed = max(0, len(attack.energies) - current_energy_count)
        best_needed = min(best_needed, needed)
    return best_needed


def _attach_target_score(option: Option, obs: Observation) -> float:
    """Prefer powering up the active attacker (keeps the KO race tempo); only
    redirect a Tool/Energy attachment to a bench Pokemon once the active no
    longer needs more energy for its own attacks."""
    state = obs.current
    me = state.players[state.yourIndex]
    target = None
    is_active = option.inPlayArea == AreaType.ACTIVE
    if is_active:
        target = me.active[0] if me.active else None
    elif option.inPlayArea == AreaType.BENCH and option.inPlayIndex is not None:
        if 0 <= option.inPlayIndex < len(me.bench):
            target = me.bench[option.inPlayIndex]
    base = _PRIORITY[OptionType.ATTACH]
    if target is None:
        return base
    shortfall = _energy_shortfall(target.id, len(target.energies))
    if is_active:
        return base + (5 if shortfall > 0 else 0)
    if shortfall == 0:
        return base - 10
    return base - 5 + max(0, 5 - shortfall)


def _score(option: Option, obs: Observation) -> float:
    if option.type == OptionType.ATTACK:
        damage = _attack_damage(option, obs)
        opp_hp = _opponent_active_hp(obs)
        if opp_hp is not None and damage >= opp_hp:
            return _LETHAL_BONUS + damage
        return _NONLETHAL_ATTACK_BASE + min(damage, _NONLETHAL_ATTACK_DAMAGE_CAP) / 10.0
    if option.type == OptionType.RETREAT:
        if _active_is_critical(obs) and _healthiest_bench_available(obs):
            return _RETREAT_WHEN_CRITICAL_SCORE
        return _PRIORITY[OptionType.RETREAT]
    if option.type == OptionType.ATTACH:
        return _attach_target_score(option, obs)
    if option.type == OptionType.CARD:
        context = obs.select.context
        if context in (SelectContext.SWITCH, SelectContext.TO_ACTIVE):
            state = obs.current
            if option.playerIndex is not None and option.playerIndex != state.yourIndex:
                return _gust_target_score(option, obs)
            return _switch_target_score(option, obs)
    return _PRIORITY.get(option.type, _DEFAULT_SCORE)


def agent(obs_dict: dict) -> list[int]:
    """Implement a Pokémon TCG agent that always takes a lethal attack first,
    otherwise develops the board (evolve/attach/play/ability) before attacking
    non-lethally, and only ends the turn once nothing better is available.
    """
    obs: Observation = to_observation_class(obs_dict)
    if obs.select is None:
        return _read_deck_csv()

    select = obs.select
    ranked = sorted(range(len(select.option)), key=lambda i: _score(select.option[i], obs), reverse=True)
    k = max(select.minCount, min(select.maxCount, 1))
    return ranked[:k]
