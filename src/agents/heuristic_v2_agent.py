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
    """When choosing which bench Pokemon becomes active, prefer the healthiest."""
    state = obs.current
    me = state.players[state.yourIndex]
    if option.area == AreaType.BENCH and option.index is not None and 0 <= option.index < len(me.bench):
        pokemon = me.bench[option.index]
        if pokemon is not None and pokemon.maxHp:
            return pokemon.hp / pokemon.maxHp * 100
    return _DEFAULT_SCORE


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
    if option.type == OptionType.CARD and obs.select.context in (
        SelectContext.SWITCH,
        SelectContext.TO_ACTIVE,
    ):
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
