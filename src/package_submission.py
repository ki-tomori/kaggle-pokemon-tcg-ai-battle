"""
Assemble a Kaggle submission folder: the chosen agent file copied verbatim as
main.py, its deck.csv, and the vendored `cg` SDK folder — matching the shape of
the official sample_submission/ so it can plausibly run under Kaggle's harness.

The output under submissions/ is never committed to git (gitignored already);
this script only assembles it locally for a real `kaggle competitions submit`.
"""

import argparse
import logging
import shutil
from pathlib import Path

from config import SDK_DIR, SUBMISSIONS_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def package_submission(
    agent_file: Path,
    deck_csv: Path,
    out_name: str,
    sdk_dir: Path = SDK_DIR,
) -> Path:
    """Copy agent_file -> main.py, deck_csv -> deck.csv, and sdk_dir/cg -> cg/
    into submissions/<out_name>/. Returns the output directory."""
    out_dir = SUBMISSIONS_DIR / out_name
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    shutil.copy2(agent_file, out_dir / "main.py")
    shutil.copy2(deck_csv, out_dir / "deck.csv")
    shutil.copytree(sdk_dir / "cg", out_dir / "cg", ignore=shutil.ignore_patterns("__pycache__"))

    logger.info("Packaged submission at %s", out_dir)
    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Package an agent into a Kaggle submission folder.")
    parser.add_argument(
        "--agent", required=True, help="Path to the agent .py file (e.g. src/agents/heuristic_agent.py)"
    )
    parser.add_argument("--deck", required=True, help="Path to a deck CSV")
    parser.add_argument("--name", required=True, help="Output folder name under submissions/")
    args = parser.parse_args()

    out_dir = package_submission(Path(args.agent), Path(args.deck), args.name)
    logger.info("Contents: %s", sorted(p.name for p in out_dir.iterdir()))


if __name__ == "__main__":
    main()
