"""
Greedy heuristic agent: ranks legal options by a fixed priority table and picks
the top-ranked ones. No lookahead — a step above random, not a strong player.

Kaggle-portable: only stdlib + `cg.api` imports. This file is copied verbatim into
a submission's main.py by src/package_submission.py — do not import from `src`.
"""

import os

from cg.api import Observation, Option, OptionType, to_observation_class

# Higher score = preferred. Options not listed fall back to a neutral default.
_PRIORITY: dict[OptionType, float] = {
    OptionType.ATTACK: 100,
    OptionType.EVOLVE: 80,
    OptionType.ATTACH: 70,
    OptionType.PLAY: 60,
    OptionType.ABILITY: 50,
    OptionType.YES: 40,
    OptionType.NO: 30,
    OptionType.RETREAT: 10,
    OptionType.END: 0,
}
_DEFAULT_SCORE = 20.0


def _read_deck_csv() -> list[int]:
    """Read deck.csv. Returns a list of 60 card IDs in the deck."""
    file_path = "deck.csv"
    if not os.path.exists(file_path):
        file_path = "/kaggle_simulations/agent/deck.csv"
    with open(file_path) as f:
        lines = f.read().splitlines()
    return [int(line) for line in lines[:60]]


def _score(option: Option) -> float:
    return _PRIORITY.get(option.type, _DEFAULT_SCORE)


def agent(obs_dict: dict) -> list[int]:
    """Implement a Pokémon TCG agent that greedily prefers attacking and developing
    the board over passing, with no lookahead into future turns.
    """
    obs: Observation = to_observation_class(obs_dict)
    if obs.select is None:
        return _read_deck_csv()

    select = obs.select
    ranked = sorted(range(len(select.option)), key=lambda i: _score(select.option[i]), reverse=True)
    # Always legal: minCount <= k <= maxCount, since k is clamped into that range.
    k = max(select.minCount, min(select.maxCount, 1))
    return ranked[:k]
