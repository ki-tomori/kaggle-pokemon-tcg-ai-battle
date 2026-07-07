# Pokemon TCG AI Battle — Kaggle Portfolio

> Kaggle competition solution developed as a data science / ML engineering portfolio project.

## Overview

This project is a solution to the [Pokemon TCG AI Battle competition](https://www.kaggle.com/competitions/pokemon-tcg-ai-battle)
on Kaggle. Unlike a classic tabular competition, this is an **agent-battle
simulation** (in the spirit of Kaggle Simulations competitions like Halite/Kore/Lux
AI): a submission is a Python function that plays real matches of the Pokémon
Trading Card Game against an opponent's submission, via a C-extension engine
the competition provides.

## Competition Format

- **Goal**: implement `agent(obs_dict: dict) -> list[int]`. On the very first
  call (`obs.select is None`) it must return a 60-card deck (a list of card
  IDs). On every later call it must return a list of indices into
  `obs.select.option`, with length between `obs.select.minCount` and
  `obs.select.maxCount`, no duplicates.
- **Metric**: win rate / ranking across matches against other competitors'
  agents (exact leaderboard mechanics — TBD, confirm against the official
  Rules tab).
- **Baseline**: win rate vs. this repo's own legal-random agent
  (`src/agents/random_agent.py`).

## Environment & Data

The competition ships a C-extension battle engine (`cg`) with a Python ctypes
wrapper, plus card/attack reference data. None of this is training data in the
classic ML sense — it's runtime infrastructure and a card database used for
deck-building and agent decision logic, not something you fit a model to.

- `cg.api.Observation` (via `cg.api.to_observation_class(obs_dict)`): the
  decision the engine is asking for (`select`), the log of events since your
  last move (`logs`), and the full game state (`current`).
- `cg.game`: a local match runner (`battle_start`/`battle_select`/`battle_finish`) —
  used here to build a self-play evaluation harness, see `src/arena.py`.
- `cg.api.all_card_data()` / `all_attack()`: the engine's own card/attack
  database, used by `src/deck.py` for deck construction.

See [data/README.md](data/README.md) for download instructions — the data
(and the `cg` SDK/engine binaries) are never bundled in this repository; see
**Data & License Notice** below for why.

## Approach

1. **Deck construction**: build a legal 60-card deck (`src/deck.py`).
2. **Baseline agents**: a legal-random agent and a greedy heuristic agent that
   ranks legal options by a fixed priority table (`src/agents/`).
3. **Local self-play arena**: run N matches between two agents and compute a
   win rate with a confidence interval, without touching Kaggle's simulation
   environment (`src/arena.py`, `src/evaluate.py`).
4. **(Stretch) search-based lookahead**: the engine exposes a hypothetical
   game-tree search API (`cg.api.search_begin/search_step`) for in-agent
   lookahead over hidden information — not yet used.
5. **Packaging**: assemble a submission folder from the same `src/` code, no
   duplicated logic (`src/package_submission.py`).

## Repository Structure

```
.
├── data/                    # Raw competition data + vendored cg SDK (not tracked by git)
│   ├── raw/                 # kaggle competitions download output
│   └── decks/               # Our own deck CSVs (not tracked by git)
├── notebooks/               # Exploratory notebooks
│   ├── 01_card_pool_eda.ipynb
│   └── 02_observation_walkthrough.ipynb
├── src/
│   ├── config.py            # Paths, constants, SEED
│   ├── cg_bridge.py         # sys.path bridge to the vendored `cg` SDK
│   ├── deck.py               # Deck construction and legality validation
│   ├── agents/               # Agent policies (Kaggle-portable: stdlib + cg.api only)
│   │   ├── random_agent.py
│   │   └── heuristic_agent.py
│   ├── arena.py              # Local self-play match runner + win-rate stats
│   ├── evaluate.py           # Win-rate summary (Wilson CI) + plotting
│   └── package_submission.py # Assemble a submissions/<name>/ folder
├── tests/                    # pytest — skips SDK-dependent cases if data/ isn't downloaded
├── experiments/               # Experiment configs + results (one folder per experiment id)
├── reports/                   # Write-ups + figures
│   └── figures/
├── submissions/                # Packaged submissions (not tracked by git)
└── requirements.txt
```

## How to Run

### Setup

```bash
git clone <this-repo>
cd kaggle-pokemon-tcg-ai-battle

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Requires Python 3.10+ — the competition's `cg` SDK uses `X | None` type-hint
syntax that isn't valid on 3.9.

### Download Data

```bash
kaggle competitions download -c pokemon-tcg-ai-battle -p data/raw/
unzip -o data/raw/pokemon-tcg-ai-battle.zip -d data/raw/
```

### Run a local match / evaluation

```bash
python src/deck.py                                    # sanity-check deck construction
python src/arena.py \
  --agent-a agents.heuristic_agent --agent-b agents.random_agent \
  --deck-a data/decks/baseline_v1.csv --deck-b data/decks/baseline_v1.csv \
  --n-matches 200
python src/evaluate.py --results experiments/001-baseline/results.json --name 001_win_rate
```

### Package a submission

```bash
python src/package_submission.py \
  --agent src/agents/heuristic_agent.py --deck data/decks/baseline_v1.csv --name exp001-heuristic
```

### Run tests

```bash
pytest
```

## Experiments

| # | Description | Win Rate vs Random | Branch | Notes |
|---|---|---|---|---|
| 001 | Baseline greedy heuristic agent | 41.5% (95% CI 34.9–48.4%) | `exp/001-baseline-arena` | See [reports/001_baseline_writeup.md](reports/001_baseline_writeup.md) — did not beat random; most matches decided by deck-out, not combat |

## Results

- **Best win rate vs. random**: 41.5% (experiment 001 — not yet beating the baseline)
- **Leaderboard ranking**: —

## Key Learnings

- The competition turned out to be an agent-battle simulation, not a tabular
  ML problem — confirmed only after downloading the actual data, not from the
  competition's landing page framing alone.
- A greedy, lookahead-free heuristic isn't automatically better than random
  when the deck itself (not agent decisions) dominates how matches end (see
  experiment 001) — deck design and agent policy need to be evaluated together.

## Data & License Notice

The card database, reference PDFs, the `ptcg_engine` C++ engine source, and
the `cg` Python SDK (including its compiled binaries) are downloaded via the
Kaggle API into the gitignored `data/` directory. They are governed by
Kaggle's competition rules and the bundled
`LicenseRef-PTCG-ABC-Competition-Use-Only.txt`: competition-use only, not for
redistribution, and to be deleted once the competition ends. This repository
never commits any of it — only the download command is given above. Packaged
submissions under `submissions/` (which include a copy of the `cg` SDK) are
likewise gitignored for the same reason.
