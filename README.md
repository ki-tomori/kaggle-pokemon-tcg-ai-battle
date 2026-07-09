# Pokemon TCG AI Battle Portfolio

> Kaggle competition solution developed as a data science / ML engineering
> portfolio project.

## Overview

This repository is an AI agent development project for Kaggle's
[Pokemon TCG AI Battle](https://www.kaggle.com/competitions/pokemon-tcg-ai-battle)
competition. Unlike a classic tabular competition, this is an **agent-battle
simulation** (in the spirit of Kaggle Simulations competitions like
Halite/Kore/Lux AI): a submission is a Python function that plays real matches
of the Pokémon Trading Card Game against an opponent's submission, via a
C-extension engine the competition provides.

The project emphasizes:

- Local self-play environment
- Reproducible evaluation
- Win-rate analysis with confidence intervals
- Experiment tracking
- Agent improvement cycle
- Kaggle submission packaging
- Portfolio-friendly documentation

## Key Features

- Local arena (`src/arena.py`) for self-play evaluation between any two agents
- A legal-random baseline agent and a family of increasingly capable
  heuristic agents (`src/agents/`)
- Win-rate evaluation with Wilson confidence intervals (`src/evaluate.py`,
  `src/evaluate_baseline.py`)
- Pytest-based validation (deck legality, agent contract, arena smoke tests)
- Kaggle submission packaging workflow (`src/package_submission.py`)
- Experiment documentation under [`experiments/`](./experiments/README.md),
  independent of Git branch history — see `docs/git-workflow.md`

## Experiment History

This project has run 13 experiments so far — from a basic pipeline smoke test
through deck sourcing from real top-episode data and agent-side
turn-sequencing fixes. Full history, including negative and neutral results,
is tracked here:

**[→ experiments/README.md](./experiments/README.md)**

A few highlights:

| Experiment | Summary | Status |
|---|---|---|
| [EXP-001](./experiments/EXP-001-baseline.md) | Baseline heuristic vs. random evaluation (pipeline smoke test) | Completed |
| [EXP-002](./experiments/EXP-002-heuristic-v2.md) | Deck optimization + lethal-aware agent — best Kaggle score so far (423.3) | Completed |
| [EXP-010](./experiments/EXP-010-attack-sequencing.md) | Turn-sequencing fix — largest single-change local win-rate gain in the project (70.0% head-to-head) | Completed |

## Project Structure

```text
project/
├── src/
│   ├── agents/                  # Agent policies (Kaggle-portable: stdlib + cg.api only)
│   ├── arena.py                 # Local self-play match runner + win-rate stats
│   ├── deck.py                  # Deck construction and legality validation
│   ├── evaluate.py              # Win-rate summary (Wilson CI) + plotting
│   ├── evaluate_baseline.py     # Regression harness vs. the frozen baseline_423 snapshot
│   ├── diagnose_sequencing.py   # Reusable OptionType co-occurrence diagnostic
│   └── package_submission.py    # Assemble a submissions/<name>/ folder
├── notebooks/
│   ├── 01_card_pool_eda.ipynb
│   └── 02_observation_walkthrough.ipynb
├── experiments/
│   ├── README.md                 # Experiment index + management policy
│   ├── EXP-001-baseline.md
│   ├── ...
│   ├── EXP-013-sequencing-audit-meta-deck.md
│   ├── EXP-xxx-template.md
│   └── NNN-.../                  # Raw per-experiment config.yaml / results.json
├── reports/
│   └── figures/                  # Narrative write-ups + win-rate charts
├── tests/                        # pytest — skips SDK-dependent cases if data/ isn't downloaded
├── docs/
│   └── git-workflow.md           # Branch model (main / feature / release) and rationale
├── cleanup-plan.md               # Open, not-yet-executed follow-up steps
├── requirements.txt
└── README.md
```

`data/` (raw competition data + vendored `cg` SDK) and `submissions/`
(packaged agent archives) are not tracked by Git — see **Data & License
Notice** below.

## How to Run

```bash
git clone <this-repo>
cd kaggle-pokemon-tcg-ai-battle
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Download competition data (requires a Kaggle API token)
kaggle competitions download -c pokemon-tcg-ai-battle -p data/raw/
unzip -o data/raw/pokemon-tcg-ai-battle.zip -d data/raw/

# Run a local match / evaluation
python src/arena.py \
  --agent-a agents.heuristic_agent --agent-b agents.random_agent \
  --deck-a data/decks/baseline_v1.csv --deck-b data/decks/baseline_v1.csv \
  --n-matches 200

# Regression-check a candidate change against the frozen best-known agent
python src/evaluate_baseline.py --n-matches 200 --seed 42

# Package a submission
python src/package_submission.py \
  --agent src/agents/heuristic_agent.py --deck data/decks/baseline_v1.csv --name exp001-heuristic

# Run tests
pytest
```

Requires Python 3.10+ (the competition's `cg` SDK uses `X | None` type-hint
syntax). See [`experiments/README.md`](./experiments/README.md) for how each
command above maps to a specific experiment, and each `experiments/EXP-XXX-*.md`
file's **Reproducibility** section for the exact invocation used in that
experiment.

## Git Workflow

Active development uses `main` / `feature/*` / `release/*` branches.
Experiment history lives under `experiments/`, not in long-lived per-experiment
branches. See [`docs/git-workflow.md`](./docs/git-workflow.md) for the full
policy and the rationale for this project's branch model, and
[`cleanup-plan.md`](./cleanup-plan.md) for open, not-yet-executed follow-up
steps.

## Submission Policy

Local self-play win rate turned out to be a poor predictor of real Kaggle
ladder performance (see EXP-007/EXP-009), and the leaderboard itself is noisy
(scores can shift 150–400+ points between identical agents purely from
matchmaking luck). Working policy: validate locally with
`src/evaluate_baseline.py` first; only submit once there's real confidence in
a candidate; prefer submitting the same candidate to both active slots to
average out matchmaking luck. Full rationale: [EXP-007](./experiments/EXP-007-retreat-fix.md)
and [EXP-009](./experiments/EXP-009-evolution-deck.md).

## Data & License Notice

The card database, reference PDFs, the `ptcg_engine` C++ engine source, and
the `cg` Python SDK (including its compiled binaries) are downloaded via the
Kaggle API into the gitignored `data/` directory. They are governed by
Kaggle's competition rules and the bundled
`LicenseRef-PTCG-ABC-Competition-Use-Only.txt`: competition-use only, not for
redistribution, and to be deleted once the competition ends. This repository
never commits any of it — only the download command above is given.
Packaged submissions under `submissions/` (which include a copy of the `cg`
SDK) are likewise gitignored for the same reason.
