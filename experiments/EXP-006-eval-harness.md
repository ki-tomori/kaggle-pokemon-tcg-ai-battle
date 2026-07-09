# EXP-006: Local Evaluation Harness + Frozen Baseline Snapshot

## Objective

Tooling-only experiment: build a repeatable local regression harness so future
agent/deck changes can be checked against a fixed reference point, instead of
comparing ad hoc against whatever the "current" agent happens to be.

## Hypothesis

N/A — this experiment does not test an agent or deck change. It adds
infrastructure the following experiments (EXP-007 onward) depend on.

## Implementation

- **Agent**: `agents.heuristic_v2_agent` (unchanged, EXP-002's version) — used
  only to exercise and validate the new harness, not modified.
- **Deck**: `data/decks/optimized_v2.csv` (unchanged).
- **Evaluation setup**: added `src/evaluate_baseline.py` (writes
  `outputs/eval_results.csv`, `outputs/loss_cases.csv`,
  `outputs/loss_summary.md`) and froze `experiments/baseline_423/` — a
  reproducible snapshot of EXP-002's exact agent code
  (`experiments/baseline_423/agent_snapshot.py`) and deck (exact 60 card IDs
  recorded in `experiments/baseline_423/manifest.yaml`), named for its 423.3
  Kaggle public score.
- **Number of matches**: 200 (harness smoke-test run)
- **Seed**: 42
- **Main changes**: `src/evaluate_baseline.py` (new),
  `experiments/baseline_423/` (new, frozen), `reports/baseline_423_overview.md`
  (new — documents the current code structure and the v2 agent's exact
  scoring table at this point in the project, for future reference).

## Result

- **Win rate**: 88% (v2 agent vs. random, same-seed harness smoke test —
  consistent with EXP-002/003's ~86% range; not a new finding, just confirming
  the harness reproduces known behavior)
- **Confidence interval**: TBD (not recorded separately for this smoke test)
- **Draws**: TBD
- **Aborted matches**: TBD
- **Other metrics**: N/A — no agent/deck change to evaluate

## Discussion

No agent or deck logic changed. This experiment exists so later experiments
have (a) a fixed, reproducible comparison point that does not silently drift
as the "live" agent keeps changing, and (b) a documented breakdown of exactly
what the current best agent does and does not do (see
`reports/baseline_423_overview.md`'s scoring-table breakdown), which directly
informed the loss-pattern analysis that motivated EXP-007.

## Next Action

- Use `src/evaluate_baseline.py` as the standard check before promoting any
  candidate change (this became the project's standing practice from EXP-007
  onward).
- Record a new `baseline_*` snapshot if a future agent/deck clearly supersedes
  this one, rather than editing this snapshot in place.

## Reproducibility

- **Command**:
  ```bash
  python src/evaluate_baseline.py --n-matches 200 --seed 42
  ```
- **Config**: N/A (no `experiments/006-.../config.yaml` was recorded — this
  experiment's artifacts are the harness script and the frozen snapshot
  itself, not a config/results pair)
- **Raw result**: `outputs/eval_results.csv`, `outputs/loss_cases.csv`,
  `outputs/loss_summary.md` (regenerated on each run, not committed)
- **Full write-up**: `reports/baseline_423_overview.md`
- **Commit**: `04840dbd8321832731ef990041a7bafbb06456d9`
- **Data dependency**: competition data (see EXP-001).

## Related Branch or Commit

- Legacy development branch: `exp/006-eval-harness`
- Base commit: `04840dbd8321832731ef990041a7bafbb06456d9`

## Status

Completed (tooling). Not applicable for Kaggle submission — no agent/deck
change was made.
