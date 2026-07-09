"""
Local self-play harness: run matches between two agent functions using the
competition's `cg.game` engine, without touching Kaggle's simulation environment.
"""

import argparse
import importlib
import logging
from dataclasses import dataclass
from typing import Callable

import numpy as np
from agents import AgentFn
from cg_bridge import (
    LogType,
    Observation,
    battle_finish,
    battle_select,
    battle_start,
    to_observation_class,
)
from config import DEFAULT_N_MATCHES, MAX_ACTIONS_PER_MATCH, SEED
from deck import load_deck_csv

SelectObserver = Callable[[Observation], None]

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    winner: int  # 0 or 1 (player index), 2 = draw, -1 = aborted
    reason: int | None
    n_actions: int
    aborted: bool


@dataclass
class ArenaStats:
    wins_a: int = 0
    wins_b: int = 0
    draws: int = 0
    aborted: int = 0

    @property
    def n_matches(self) -> int:
        return self.wins_a + self.wins_b + self.draws + self.aborted

    @property
    def win_rate_a(self) -> float:
        decided = self.wins_a + self.wins_b + self.draws
        return self.wins_a / decided if decided else 0.0


def play_match(
    agent0: AgentFn,
    agent1: AgentFn,
    deck0: list[int],
    deck1: list[int],
    max_actions: int = MAX_ACTIONS_PER_MATCH,
    select_observer: SelectObserver | None = None,
) -> MatchResult:
    """Play one match between agent0 (player 0) and agent1 (player 1).

    `select_observer`, if given, is called with the `Observation` at every select
    decision before the acting agent picks — a hook for diagnostics (e.g. logging
    which OptionTypes are simultaneously legal) without duplicating the match loop.
    """
    obs_dict, start_data = battle_start(deck0, deck1)
    if obs_dict is None:
        logger.warning(
            "battle_start failed (errorPlayer=%s, errorType=%s)",
            start_data.errorPlayer,
            start_data.errorType,
        )
        return MatchResult(winner=-1, reason=None, n_actions=0, aborted=True)

    agents = [agent0, agent1]
    n_actions = 0
    try:
        while True:
            obs = to_observation_class(obs_dict)
            if obs.current.result != -1:
                reason = next(
                    (log.reason for log in obs.logs if log.type == LogType.RESULT),
                    None,
                )
                return MatchResult(
                    winner=obs.current.result,
                    reason=reason,
                    n_actions=n_actions,
                    aborted=False,
                )

            if n_actions >= max_actions:
                logger.warning(
                    "Match aborted after hitting max_actions=%d.", max_actions
                )
                return MatchResult(
                    winner=-1, reason=None, n_actions=n_actions, aborted=True
                )

            if select_observer is not None:
                select_observer(obs)

            turn_idx = obs.current.yourIndex
            selection = agents[turn_idx](obs_dict)
            obs_dict = battle_select(selection)
            n_actions += 1
    except (IndexError, ValueError) as exc:
        logger.warning("Match aborted due to an illegal selection: %s", exc)
        return MatchResult(winner=-1, reason=None, n_actions=n_actions, aborted=True)
    finally:
        battle_finish()


def play_n_matches(
    agent_a: AgentFn,
    agent_b: AgentFn,
    deck_a: list[int],
    deck_b: list[int],
    n: int = DEFAULT_N_MATCHES,
    seed: int = SEED,
    select_observer: SelectObserver | None = None,
) -> ArenaStats:
    """Play n matches, alternating who plays first to cancel first-move advantage."""
    rng = np.random.default_rng(seed)
    stats = ArenaStats()

    for i in range(n):
        a_goes_first = bool(rng.integers(0, 2))
        if a_goes_first:
            result = play_match(
                agent_a, agent_b, deck_a, deck_b, select_observer=select_observer
            )
            a_index = 0
        else:
            result = play_match(
                agent_b, agent_a, deck_b, deck_a, select_observer=select_observer
            )
            a_index = 1

        if result.aborted:
            stats.aborted += 1
        elif result.winner == 2:
            stats.draws += 1
        elif result.winner == a_index:
            stats.wins_a += 1
        else:
            stats.wins_b += 1

        logger.info(
            "Match %d/%d: winner=%s aborted=%s actions=%d",
            i + 1,
            n,
            result.winner,
            result.aborted,
            result.n_actions,
        )

    return stats


def _load_agent(dotted_path: str) -> AgentFn:
    """Import an agent module (e.g. 'agents.heuristic_agent') and return its `agent` function."""
    module = importlib.import_module(dotted_path)
    return module.agent


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run local self-play matches between two agents."
    )
    parser.add_argument(
        "--agent-a",
        required=True,
        help="Dotted module path, e.g. agents.heuristic_agent",
    )
    parser.add_argument(
        "--agent-b", required=True, help="Dotted module path, e.g. agents.random_agent"
    )
    parser.add_argument(
        "--deck-a", required=True, help="Path to a deck CSV for agent A"
    )
    parser.add_argument(
        "--deck-b", required=True, help="Path to a deck CSV for agent B"
    )
    parser.add_argument("--n-matches", type=int, default=DEFAULT_N_MATCHES)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    agent_a = _load_agent(args.agent_a)
    agent_b = _load_agent(args.agent_b)
    deck_a = load_deck_csv(args.deck_a)
    deck_b = load_deck_csv(args.deck_b)

    stats = play_n_matches(
        agent_a, agent_b, deck_a, deck_b, n=args.n_matches, seed=args.seed
    )
    logger.info(
        "Result: A wins=%d B wins=%d draws=%d aborted=%d win_rate_a=%.3f",
        stats.wins_a,
        stats.wins_b,
        stats.draws,
        stats.aborted,
        stats.win_rate_a,
    )


if __name__ == "__main__":
    main()
