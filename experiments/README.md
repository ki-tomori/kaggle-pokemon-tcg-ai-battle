# Experiments

Every experiment gets a numbered folder here (`NNN-short-description/`) plus
a matching write-up in `../reports/NNN_*.md`. This README explains the
convention; use [exp_template.md](exp_template.md) when starting a new one.

## Layout

```
experiments/
├── 001-baseline/
│   ├── config.yaml      # what was run: agent, deck, opponent, n_matches, seed
│   └── results.json     # what happened: win/loss counts, derived metrics
├── baseline_423/
│   ├── manifest.yaml     # frozen reference-point metadata (see below)
│   └── agent_snapshot.py # frozen copy of the agent's source at that point
└── ...
```

- **`config.yaml`**: the experiment's inputs. Should be enough to *reproduce*
  the run — agent module path, deck path (or the exact recipe/source if it's
  a generated or extracted deck), opponent, `n_matches`, `seed`, git branch
  and base commit.
- **`results.json`**: the experiment's outputs — win/loss/draw/aborted counts,
  win rate, and any diagnostic breakdown (loss reasons, ablation results,
  etc.) worth keeping in a machine-readable form. Prose interpretation goes
  in the matching `reports/NNN_*.md`, not here.
- Frozen snapshots (like `baseline_423/`) are the exception to the
  numbered-folder pattern: they capture a *fixed reference point* for
  regression comparisons, not a one-off experiment. Don't edit a frozen
  snapshot in place if the live code later changes — record a new one.

## The lightweight running log: `../experiments.csv`

A single flat CSV at the repo root, one row per experiment, meant to be
skimmed in seconds (date, experiment_id, agent, deck, opponent, n_matches,
win_rate, kaggle_submission, notes). This is *not* a replacement for the
per-experiment folders above — it's an index into them. Append a row every
time you finish an experiment, even a negative one.

## Branching convention

Each experiment is its own git branch, `exp/NNN-short-description`, usually
branched from the strongest prior experiment's tip (not always the
immediately-preceding number — see `docs/architecture.md`'s "Branching
model"). This keeps independent measures (e.g. a deck change vs. an agent
change) comparable without one experiment's code changes leaking into
another's.

## Before you start a new experiment

1. Read [`../docs/strategy.md`](../docs/strategy.md) for the current
   synthesis of what's known to work.
2. Check [`../improvement/roadmap.md`](../improvement/roadmap.md) — is this
   idea already queued, or does it contradict a lesson in
   [`../improvement/lessons_learned.md`](../improvement/lessons_learned.md)?
3. Branch: `git checkout -b exp/0NN-description` from the right base tip.
4. Validate locally with `python src/evaluate_baseline.py` (or `arena.py`
   directly for a custom matchup) before touching Kaggle at all — see the
   Submission Policy in the root README.

## After you finish one

1. Write `experiments/0NN-description/config.yaml` + `results.json`.
2. Write `reports/0NN_description.md` using [exp_template.md](exp_template.md).
3. Append a row to `../experiments.csv`.
4. Update `../docs/strategy.md` if the finding changes the current best
   agent/deck or contradicts a prior assumption there.
5. Update `../improvement/roadmap.md` (remove what you just did, add
   whatever new "next steps" the write-up surfaced) and
   `../improvement/lessons_learned.md` if something generalizable was learned.
6. Update the Experiments table in the root `README.md`.
7. Commit, push the branch. Only submit to Kaggle if the result clears the
   confidence bar in the Submission Policy — most experiments shouldn't.
