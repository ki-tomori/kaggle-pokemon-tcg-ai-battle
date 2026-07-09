"""
Reusable diagnostic: which OptionTypes are simultaneously legal at the same
select decision, during self-play.

Experiment 010 found (via a throwaway one-off script) that MAIN selects often
offer ATTACK alongside setup actions (ATTACH/EVOLVE/PLAY/ABILITY) at the same
decision point -- the agent's fixed _PRIORITY ordering was implicitly making a
sequencing call every time that happened, but only the ATTACK-vs-setup case had
ever been measured. This script generalizes that measurement to every OptionType
pair, for any agent/deck/select-type, via arena.py's `select_observer` hook, so
future experiments can audit other option-ordering decisions without writing a
new throwaway script each time.
"""

import argparse
import json
import logging
from collections import Counter
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

from arena import play_n_matches
from cg_bridge import Observation, OptionType, SelectType
from config import DEFAULT_N_MATCHES, SEED
from deck import load_deck_csv

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class CooccurrenceTracker:
    """Collects, over many selects, which OptionTypes appear together in one select.option list."""

    def __init__(self, select_type: SelectType | None = None) -> None:
        self.select_type = select_type
        self.n_selects = 0
        self.marginal: Counter[str] = Counter()
        self.pair: Counter[tuple[str, str]] = Counter()
        self.combo: Counter[tuple[str, ...]] = Counter()

    def observe(self, obs: Observation) -> None:
        select = obs.select
        if select is None:
            return
        if self.select_type is not None and select.type != self.select_type:
            return

        names = sorted({OptionType(option.type).name for option in select.option})
        if not names:
            return

        self.n_selects += 1
        self.marginal.update(names)
        self.combo[tuple(names)] += 1
        for a, b in combinations(names, 2):
            self.pair[(a, b)] += 1

    def to_report(self, top_n_combos: int = 15) -> dict:
        marginal_share = {
            name: {"count": count, "share": round(count / self.n_selects, 4)}
            for name, count in self.marginal.most_common()
        }
        # Conditional co-occurrence: given A is offered, how often is B also offered?
        conditional: dict[str, dict[str, float]] = {}
        for (a, b), both_count in self.pair.items():
            conditional.setdefault(a, {})[b] = round(both_count / self.marginal[a], 4)
            conditional.setdefault(b, {})[a] = round(both_count / self.marginal[b], 4)

        top_combos = [
            {
                "option_types": list(combo),
                "count": count,
                "share": round(count / self.n_selects, 4),
            }
            for combo, count in self.combo.most_common(top_n_combos)
        ]

        return {
            "select_type_filter": self.select_type.name if self.select_type else None,
            "n_selects_sampled": self.n_selects,
            "marginal_frequency": marginal_share,
            "conditional_cooccurrence": conditional,
            "top_combos": top_combos,
        }


def _load_agent(dotted_path: str):
    import importlib

    return importlib.import_module(dotted_path).agent


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Measure OptionType co-occurrence at select decisions during self-play."
    )
    parser.add_argument(
        "--agent", default="agents.heuristic_v2_agent", help="Dotted module path"
    )
    parser.add_argument(
        "--deck",
        required=True,
        help="Path to a deck CSV, played by the agent against itself",
    )
    parser.add_argument("--n-matches", type=int, default=DEFAULT_N_MATCHES)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument(
        "--select-type",
        default="MAIN",
        help="Restrict to one cg.api.SelectType name (e.g. MAIN, CARD), or 'ALL' for no filter.",
    )
    parser.add_argument(
        "--output", default=None, help="Output JSON path (default: stdout summary only)"
    )
    args = parser.parse_args()

    agent = _load_agent(args.agent)
    deck = load_deck_csv(args.deck)
    select_type = None if args.select_type == "ALL" else SelectType[args.select_type]

    tracker = CooccurrenceTracker(select_type=select_type)
    stats = play_n_matches(
        agent,
        agent,
        deck,
        deck,
        n=args.n_matches,
        seed=args.seed,
        select_observer=tracker.observe,
    )
    logger.info(
        "Self-play done: %d matches (aborted=%d). Sampled %d selects (filter=%s).",
        stats.n_matches,
        stats.aborted,
        tracker.n_selects,
        args.select_type,
    )

    report = tracker.to_report()
    report["agent"] = args.agent
    report["deck"] = args.deck
    report["n_matches"] = args.n_matches
    report["seed"] = args.seed
    report["recorded_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    logger.info("Marginal OptionType frequency (share of sampled selects offering it):")
    for name, stat in report["marginal_frequency"].items():
        logger.info("  %-12s count=%-5d share=%.3f", name, stat["count"], stat["share"])

    logger.info("Top co-occurring option-type combos:")
    for combo in report["top_combos"]:
        logger.info(
            "  %-60s count=%-5d share=%.3f",
            combo["option_types"],
            combo["count"],
            combo["share"],
        )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2))
        logger.info("Wrote %s", output_path)


if __name__ == "__main__":
    main()
