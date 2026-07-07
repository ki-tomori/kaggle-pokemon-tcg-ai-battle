"""
Local evaluation harness for baseline_423 (agents.heuristic_v2_agent + the
optimized_v2 deck — see experiments/baseline_423/manifest.yaml). Runs N local
self-play matches against a configurable opponent and writes:
  - outputs/eval_results.csv   one row per match
  - outputs/loss_cases.csv     subset: only matches the agent lost
  - outputs/loss_summary.md    aggregated breakdown of how/why it lost

This is evaluation-only tooling — it does not modify any agent's logic.
"""

import argparse
import csv
import importlib
import logging
from pathlib import Path

import numpy as np

from arena import play_match
from config import DEFAULT_N_MATCHES, ROOT_DIR, SEED
from deck import load_deck_csv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

OUTPUTS_DIR = ROOT_DIR / "outputs"
BASELINE_AGENT_MODULE = "agents.heuristic_v2_agent"
BASELINE_DECK_PATH = ROOT_DIR / "data" / "decks" / "optimized_v2.csv"

# LogType.RESULT.reason values, per the cg SDK's own comment on that enum member.
_REASON_LABELS = {
    1: "prize_race (0 prize cards)",
    2: "deck_out (0 deck cards at draw)",
    3: "no_pokemon_in_play",
    4: "card_effect",
}


def _load_agent(dotted_path: str):
    return importlib.import_module(dotted_path).agent


def run_evaluation(
    agent_module: str = BASELINE_AGENT_MODULE,
    deck_path: Path = BASELINE_DECK_PATH,
    opponent_module: str = "agents.random_agent",
    opponent_deck_path: Path | None = None,
    n_matches: int = DEFAULT_N_MATCHES,
    seed: int = SEED,
) -> list[dict]:
    """Play n_matches between agent_module and opponent_module, alternating who
    goes first each match. Returns one result dict per match."""
    agent_fn = _load_agent(agent_module)
    opponent_fn = _load_agent(opponent_module)
    deck = load_deck_csv(deck_path)
    opponent_deck = load_deck_csv(opponent_deck_path) if opponent_deck_path else deck

    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n_matches):
        agent_goes_first = bool(rng.integers(0, 2))
        if agent_goes_first:
            result = play_match(agent_fn, opponent_fn, deck, opponent_deck)
            agent_index = 0
        else:
            result = play_match(opponent_fn, agent_fn, opponent_deck, deck)
            agent_index = 1

        if result.aborted:
            outcome = "aborted"
        elif result.winner == 2:
            outcome = "draw"
        elif result.winner == agent_index:
            outcome = "win"
        else:
            outcome = "loss"

        rows.append(
            {
                "match_id": i,
                "agent_module": agent_module,
                "opponent_module": opponent_module,
                "agent_went_first": agent_goes_first,
                "outcome": outcome,
                "winner_index": result.winner,
                "agent_index": agent_index,
                "reason": result.reason,
                "n_actions": result.n_actions,
                "aborted": result.aborted,
            }
        )
        logger.info(
            "Match %d/%d: %s (reason=%s, actions=%d)",
            i + 1,
            n_matches,
            outcome,
            result.reason,
            result.n_actions,
        )

    return rows


def write_eval_results(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Wrote %d rows to %s", len(rows), path)


def write_loss_cases(rows: list[dict], path: Path) -> list[dict]:
    losses = [r for r in rows if r["outcome"] == "loss"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        fieldnames = list(rows[0].keys()) if rows else []
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(losses)
    logger.info("Wrote %d loss cases to %s", len(losses), path)
    return losses


def write_loss_summary(rows: list[dict], losses: list[dict], path: Path) -> None:
    n = len(rows)
    n_losses = len(losses)
    n_wins = sum(1 for r in rows if r["outcome"] == "win")
    n_draws = sum(1 for r in rows if r["outcome"] == "draw")
    n_aborted = sum(1 for r in rows if r["outcome"] == "aborted")

    reason_counts: dict[str, int] = {}
    for r in losses:
        label = _REASON_LABELS.get(r["reason"], f"unknown ({r['reason']})")
        reason_counts[label] = reason_counts.get(label, 0) + 1

    avg_actions_loss = sum(r["n_actions"] for r in losses) / n_losses if n_losses else 0.0
    avg_actions_win = sum(r["n_actions"] for r in rows if r["outcome"] == "win") / n_wins if n_wins else 0.0
    first_player_losses = sum(1 for r in losses if r["agent_went_first"])

    lines = [
        "# Loss Summary — baseline_423",
        "",
        f"- Matches: {n} (wins={n_wins}, losses={n_losses}, draws={n_draws}, aborted={n_aborted})",
        f"- Win rate: {n_wins / n:.3f}" if n else "- Win rate: n/a",
        "",
        "## Loss reasons",
        "",
        "| Reason | Count | Share of losses |",
        "|---|---|---|",
    ]
    for label, count in sorted(reason_counts.items(), key=lambda kv: -kv[1]):
        share = count / n_losses if n_losses else 0.0
        lines.append(f"| {label} | {count} | {share:.1%} |")

    lines += [
        "",
        "## Other patterns",
        "",
        f"- Average match length: {avg_actions_loss:.1f} actions in losses vs {avg_actions_win:.1f} in wins",
    ]
    if n_losses:
        lines.append(f"- Losses where the agent went first: {first_player_losses}/{n_losses}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    logger.info("Wrote loss summary to %s", path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate baseline_423 (agents.heuristic_v2_agent) locally against an opponent."
    )
    parser.add_argument("--agent", default=BASELINE_AGENT_MODULE)
    parser.add_argument("--deck", default=str(BASELINE_DECK_PATH))
    parser.add_argument("--opponent", default="agents.random_agent")
    parser.add_argument("--opponent-deck", default=None)
    parser.add_argument("--n-matches", type=int, default=DEFAULT_N_MATCHES)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--outputs-dir", default=str(OUTPUTS_DIR))
    args = parser.parse_args()

    outputs_dir = Path(args.outputs_dir)
    rows = run_evaluation(
        agent_module=args.agent,
        deck_path=Path(args.deck),
        opponent_module=args.opponent,
        opponent_deck_path=Path(args.opponent_deck) if args.opponent_deck else None,
        n_matches=args.n_matches,
        seed=args.seed,
    )
    write_eval_results(rows, outputs_dir / "eval_results.csv")
    losses = write_loss_cases(rows, outputs_dir / "loss_cases.csv")
    write_loss_summary(rows, losses, outputs_dir / "loss_summary.md")

    n_wins = sum(1 for r in rows if r["outcome"] == "win")
    logger.info("Done. Win rate: %.3f (%d/%d)", n_wins / len(rows), n_wins, len(rows))


if __name__ == "__main__":
    main()
