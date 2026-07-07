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


def archive_submission(out_dir: Path, archive_format: str = "gztar") -> Path:
    """Archive out_dir's contents (main.py/deck.csv/cg/ at the top level) into
    submissions/<out_dir.name>.<ext> — default gztar (.tar.gz), matching the
    format documented in a competitor's public write-up of this competition's
    expected submission shape (`submission.tar.gz`). We'd previously only ever
    submitted .zip; Kaggle accepting the upload doesn't confirm the judge can
    unpack it, so this makes it easy to try the documented format instead."""
    base_name = str(out_dir.parent / out_dir.name)
    archive_path = shutil.make_archive(base_name, archive_format, root_dir=out_dir)
    logger.info("Archived %s -> %s", out_dir, archive_path)
    return Path(archive_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Package an agent into a Kaggle submission folder.")
    parser.add_argument(
        "--agent", required=True, help="Path to the agent .py file (e.g. src/agents/heuristic_agent.py)"
    )
    parser.add_argument("--deck", required=True, help="Path to a deck CSV")
    parser.add_argument("--name", required=True, help="Output folder name under submissions/")
    parser.add_argument(
        "--archive",
        choices=["gztar", "zip", "none"],
        default="gztar",
        help="Archive format to also produce (gztar -> .tar.gz, matching the documented upload "
        "format; zip for the format used by earlier experiments; none to skip archiving)",
    )
    args = parser.parse_args()

    out_dir = package_submission(Path(args.agent), Path(args.deck), args.name)
    logger.info("Contents: %s", sorted(p.name for p in out_dir.iterdir()))

    if args.archive != "none":
        archive_submission(out_dir, args.archive)


if __name__ == "__main__":
    main()
