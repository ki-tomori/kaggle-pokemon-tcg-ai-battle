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

### Evaluate baseline_423 locally (regression harness for future changes)

`baseline_423` is the frozen reference point for future improvement work —
the best-scoring submission so far (`agents.heuristic_v2_agent` +
`data/decks/optimized_v2.csv`, exp002-heuristic-v2). See
`experiments/baseline_423/manifest.yaml` and
`reports/baseline_423_overview.md` for what it is and why it was recorded.

```bash
python src/evaluate_baseline.py --n-matches 200 --seed 42
```

Writes three files under `outputs/` (overwritten on each run):

- `eval_results.csv` — one row per match (outcome, reason code, action count, who went first)
- `loss_cases.csv` — just the losing matches, same columns
- `loss_summary.md` — loss-reason breakdown and win rate

Override the agent/deck/opponent to evaluate a candidate change against the
same harness before deciding whether to promote it:

```bash
python src/evaluate_baseline.py \
  --agent agents.my_candidate_agent --deck data/decks/my_candidate.csv \
  --opponent agents.heuristic_v2_agent --opponent-deck data/decks/optimized_v2.csv \
  --n-matches 200
```

Record the result as a new row in `experiments.csv` (repo root) — a running
log of every local evaluation, independent of the more detailed per-experiment
folders under `experiments/NNN-.../`.

### Package a submission

```bash
python src/package_submission.py \
  --agent src/agents/heuristic_agent.py --deck data/decks/baseline_v1.csv --name exp001-heuristic
```

Also writes `submissions/<name>.tar.gz` by default (`--archive zip` for the
`.zip` format used by early experiments, `--archive none` to skip archiving).
A competitor's public write-up of this competition documents the expected
upload shape as `submission.tar.gz` with `main.py`/`deck.csv`/`cg/` at the top
level — see `experiments/008-targz-packaging/`.

### Run tests

```bash
pytest
```

## Experiments

| # | Description | Win Rate vs Random | Kaggle Public Score | Branch |
|---|---|---|---|---|
| 001 | Baseline greedy heuristic agent | 41.5% | 135.0 | `exp/001-baseline-arena` |
| 002 | Efficiency-picked deck + draw support + lethal-aware agent (v2) | 86.5% | 423.3 | `exp/002-heuristic-v2` |
| 003 | Auto-selected Water deck (round-robin search) | 85.0% | 371.8 | `exp/003-deck-autoselect` |
| 004 | Defensive/energy-targeting agent (v3) | 89.0% | 320.0 | `exp/004-agent-defensive` |
| 005 | 1-ply search_begin/search_step lookahead agent | 86.5% | 348.0 | `exp/005-agent-search` |
| 007 | Retreat-when-critical fix on the v2 baseline | 92.0% | 304.2 | `exp/007-retreat-fix` |
| 008 | Same agent as 007, repackaged as `.tar.gz` | n/a | pending | `exp/008-targz-packaging` |

See `reports/*_writeup.md` and `experiments/*/` for full detail per experiment.

## Results

- **Best local win rate vs. random**: 92.0% (experiment 007)
- **Best Kaggle public score so far**: 423.3 (experiment 002) — every later experiment scored *lower* despite winning more locally (see below)
- **Real opponent win rate (from replay analysis)**: experiment 007 actually won only **6/20 (30%)** of its real Kaggle matches, despite 92% locally vs a random baseline — a large, now-confirmed gap between local self-play and the live ladder (see Submission Policy below and `reports/009_evolution_deck.md`)

## Submission Policy

Local self-play win rate (against our own agents/decks) turned out to be a
poor predictor of real Kaggle ladder performance — every experiment after 002
scored *lower* on the leaderboard despite beating 002 locally, and spot-checking
exp007's actual replays showed a 30% real win rate against a 92%-vs-random local
number. Two causes, both confirmed via the competition's Discussion forum and
direct replay inspection (`kaggle competitions replay <episode_id>`):

1. **Scoring is highly noisy.** A well-upvoted Discussion thread ("Leaderboard
   Scoring Inconsistency") documents identical agents scoring 150–400+ points
   apart purely from early-matchmaking luck. Only the **latest 2 submissions**
   stay active and keep playing games — submitting a new experiment stops the
   older one from accumulating any more games, effectively freezing its score
   wherever it happened to be.
2. **All local validation was self-referential.** Every local win-rate number
   in this repo came from our own agent playing our own (simple, Basic-only,
   no-evolution) decks or earlier variants of itself. Real opponents run
   evolution lines with Tools attached and hit far harder (one real loss ended
   from a single 170-damage attack) — a mechanically richer deck category this
   repo's decks never had to face locally.

Going forward: **don't resubmit for every small change.** Validate locally
with `src/evaluate_baseline.py` first; only submit a candidate once there's
real confidence in it, and prefer submitting the same candidate to both active
slots to average out matchmaking luck rather than treating a single score as
ground truth.

## Key Learnings

- The competition turned out to be an agent-battle simulation, not a tabular
  ML problem — confirmed only after downloading the actual data, not from the
  competition's landing page framing alone.
- A greedy, lookahead-free heuristic isn't automatically better than random
  when the deck itself (not agent decisions) dominates how matches end (see
  experiment 001) — deck design and agent policy need to be evaluated together.
- Confirmed in experiment 002: picking attackers by damage-per-energy and adding
  card-draw support closed almost the entire gap by itself (41.5% -> 82.5% with
  otherwise unchanged agent logic); a smarter attack-scoring agent added only a
  further +4pp on top. Deck quality dominated agent sophistication here, matching
  what the competition's community discussion says.

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
