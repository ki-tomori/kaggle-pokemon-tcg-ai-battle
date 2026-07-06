"""
Greedy heuristic agent v2: adds lethal detection and damage-aware attack scoring
(including a crude weakness/resistance adjustment) on top of heuristic_agent's
fixed action-type priority. Still no multi-turn lookahead.

Kaggle-portable: only stdlib + `cg.api` imports. This file is copied verbatim into
a submission's main.py by src/package_submission.py — do not import from `src`.
"""

import os

from cg.api import Observation, Option, OptionType, all_attack, all_card_data, to_observation_class

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


def _score(option: Option, obs: Observation) -> float:
    if option.type == OptionType.ATTACK:
        damage = _attack_damage(option, obs)
        opp_hp = _opponent_active_hp(obs)
        if opp_hp is not None and damage >= opp_hp:
            return _LETHAL_BONUS + damage
        return 100.0 + damage
    return _PRIORITY.get(option.type, _DEFAULT_SCORE)


def agent(obs_dict: dict) -> list[int]:
    """Implement a Pokémon TCG agent that prefers lethal attacks, then the highest-
    damage attack available, then developing the board, over passing.
    """
    obs: Observation = to_observation_class(obs_dict)
    if obs.select is None:
        return _read_deck_csv()

    select = obs.select
    ranked = sorted(range(len(select.option)), key=lambda i: _score(select.option[i], obs), reverse=True)
    k = max(select.minCount, min(select.maxCount, 1))
    return ranked[:k]
