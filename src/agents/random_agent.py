"""
Legal-random baseline agent.

Kaggle-portable: only stdlib + `cg.api` imports. This file is copied verbatim into
a submission's main.py by src/package_submission.py — do not import from `src`.
"""

import os
import random

from cg.api import to_observation_class


def _read_deck_csv() -> list[int]:
    """Read deck.csv. Returns a list of 60 card IDs in the deck."""
    file_path = "deck.csv"
    if not os.path.exists(file_path):
        file_path = "/kaggle_simulations/agent/deck.csv"
    with open(file_path) as f:
        lines = f.read().splitlines()
    return [int(line) for line in lines[:60]]


def agent(obs_dict: dict) -> list[int]:
    """Implement a Pokémon TCG agent that always picks legal options at random."""
    obs = to_observation_class(obs_dict)
    if obs.select is None:
        return _read_deck_csv()
    return random.sample(range(len(obs.select.option)), obs.select.maxCount)
