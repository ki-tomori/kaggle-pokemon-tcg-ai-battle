"""
Greedy heuristic agent v3: adds defensive/resource-targeting logic on top of v2's
lethal-detection and damage-aware attack scoring:
  - retreats the active Pokemon when it's critically damaged and a healthier
    bench Pokemon is available, instead of always deprioritizing RETREAT;
  - when switching in a new active Pokemon (after a retreat or a knockout),
    prefers the healthiest bench Pokemon;
  - when choosing which Pokemon to attach energy to, prefers whichever one
    (active or bench) needs the fewest additional energy to use its best attack.
Still no multi-turn lookahead.

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

_PRIORITY: dict[OptionType, float] = {
    OptionType.EVOLVE: 90,
    OptionType.PLAY: 65,
    OptionType.ABILITY: 55,
    OptionType.YES: 40,
    OptionType.NO: 30,
    OptionType.END: 0,
}
_DEFAULT_SCORE = 20.0
_LETHAL_BONUS = 1000.0
_CRITICAL_HP_FRACTION = 0.3


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
    redirect to a bench Pokemon once the active no longer needs more energy."""
    state = obs.current
    me = state.players[state.yourIndex]
    target = None
    is_active = option.inPlayArea == AreaType.ACTIVE
    if is_active:
        target = me.active[0] if me.active else None
    elif option.inPlayArea == AreaType.BENCH and option.inPlayIndex is not None:
        if 0 <= option.inPlayIndex < len(me.bench):
            target = me.bench[option.inPlayIndex]
    if target is None:
        return _PRIORITY_ATTACH_DEFAULT
    shortfall = _energy_shortfall(target.id, len(target.energies))
    if is_active:
        # Still investing in the active attacker's own next attack is the default,
        # race-preserving choice; once it's already ready, redirecting is fine too.
        return _PRIORITY_ATTACH_DEFAULT + (5 if shortfall > 0 else 0)
    # Bench Pokemon: only worth redirecting energy there once it's close to ready.
    if shortfall == 0:
        return _PRIORITY_ATTACH_DEFAULT - 10
    return _PRIORITY_ATTACH_DEFAULT - 5 + max(0, 5 - shortfall)


_PRIORITY_ATTACH_DEFAULT = 70.0


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
        return 100.0 + damage
    if option.type == OptionType.RETREAT:
        if _active_is_critical(obs) and _healthiest_bench_available(obs):
            return 95.0
        return 5.0
    if option.type == OptionType.ATTACH:
        return _attach_target_score(option, obs)
    if option.type == OptionType.CARD and obs.select.context in (
        SelectContext.SWITCH,
        SelectContext.TO_ACTIVE,
    ):
        return _switch_target_score(option, obs)
    return _PRIORITY.get(option.type, _DEFAULT_SCORE)


def agent(obs_dict: dict) -> list[int]:
    """Implement a Pokémon TCG agent that adds defensive retreat timing and
    energy-attachment targeting on top of heuristic_v2_agent's offense-only logic.
    """
    obs: Observation = to_observation_class(obs_dict)
    if obs.select is None:
        return _read_deck_csv()

    select = obs.select
    ranked = sorted(range(len(select.option)), key=lambda i: _score(select.option[i], obs), reverse=True)
    k = max(select.minCount, min(select.maxCount, 1))
    return ranked[:k]
