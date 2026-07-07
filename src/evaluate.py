"""
Evaluate self-play results and generate win-rate reports.
"""

import argparse
import json
import logging
import math

import matplotlib.pyplot as plt

from arena import ArenaStats
from config import FIGURES_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def wilson_ci(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a win rate — more reliable than a normal
    approximation when n is small or the rate is near 0/1."""
    if n == 0:
        return (0.0, 0.0)
    p = wins / n
    denom = 1 + z**2 / n
    centre = p + z**2 / (2 * n)
    spread = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    lo = (centre - spread) / denom
    hi = (centre + spread) / denom
    return (max(0.0, lo), min(1.0, hi))


def summarize(stats: ArenaStats) -> dict[str, float]:
    """Summarize an ArenaStats into win rate, confidence interval, draw rate, abort rate."""
    decided = stats.wins_a + stats.wins_b + stats.draws
    ci_lo, ci_hi = wilson_ci(stats.wins_a, decided) if decided else (0.0, 0.0)
    return {
        "n_matches": stats.n_matches,
        "win_rate_a": stats.win_rate_a,
        "win_rate_ci_low": ci_lo,
        "win_rate_ci_high": ci_hi,
        "draw_rate": stats.draws / decided if decided else 0.0,
        "abort_rate": stats.aborted / stats.n_matches if stats.n_matches else 0.0,
    }


def plot_win_rate(name: str, summary: dict[str, float], save: bool = True) -> None:
    """Bar chart of win rate with a Wilson CI error bar."""
    fig, ax = plt.subplots(figsize=(4, 5))
    rate = summary["win_rate_a"]
    err_low = rate - summary["win_rate_ci_low"]
    err_high = summary["win_rate_ci_high"] - rate
    ax.bar(["Agent A"], [rate], yerr=[[err_low], [err_high]], capsize=8, color="#4C72B0")
    ax.axhline(0.5, color="gray", linestyle="--", linewidth=1)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Win rate")
    ax.set_title(name)
    plt.tight_layout()

    if save:
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        path = FIGURES_DIR / f"{name}.png"
        fig.savefig(path, dpi=150)
        logger.info("Win-rate figure saved to %s", path)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize arena results from a JSON file.")
    parser.add_argument(
        "--results", required=True, help="Path to a results.json with wins_a/wins_b/draws/aborted"
    )
    parser.add_argument("--name", default="win_rate", help="Base name for the output figure")
    args = parser.parse_args()

    with open(args.results) as f:
        raw = json.load(f)
    stats = ArenaStats(wins_a=raw["wins_a"], wins_b=raw["wins_b"], draws=raw["draws"], aborted=raw["aborted"])
    summary = summarize(stats)
    for key, value in summary.items():
        logger.info("%s: %s", key, value)
    plot_win_rate(args.name, summary)


if __name__ == "__main__":
    main()
