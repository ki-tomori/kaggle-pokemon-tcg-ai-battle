"""
"B1" baseline: always return the engine's first-listed legal option(s).
A community Discussion post claims the engine enumerates options in a strong
best->worst order, so this trivial baseline is a stronger sanity check than
random -- and reportedly hard for naive re-scoring to beat. Used to validate
that heuristic_v2_agent's overrides genuinely help rather than fight the
engine's own ordering.

Kaggle-portable: only stdlib + `cg.api` imports.
"""

import os

from cg.api import to_observation_class


def _read_deck_csv() -> list[int]:
    file_path = "deck.csv"
    if not os.path.exists(file_path):
        file_path = "/kaggle_simulations/agent/deck.csv"
    with open(file_path) as f:
        lines = f.read().splitlines()
    return [int(line) for line in lines[:60]]


def agent(obs_dict: dict) -> list[int]:
    obs = to_observation_class(obs_dict)
    if obs.select is None:
        return _read_deck_csv()
    select = obs.select
    k = max(select.minCount, min(select.maxCount, 1))
    return list(range(k))
