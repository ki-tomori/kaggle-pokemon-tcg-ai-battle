# EXP-003: Automated Energy-Type Selection

## Objective

First of three parallel measures tried after EXP-002 (86.5% vs. random
locally, but a still-modest Kaggle ladder score). Asks: is Fire actually the
best energy type for this deck shape, or was it just picked first?

## Hypothesis

An empirical round-robin across all 8 standard energy types (rather than a
static per-card efficiency score) will surface a stronger deck than the Fire
deck used in EXP-002, or confirm Fire was already the right choice.

## Implementation

- **Agent**: `agents.heuristic_v2_agent` (unchanged from EXP-002) — isolates a
  deck-only change.
- **Deck**: `data/decks/best_v3.csv`, energy type chosen by
  `select_best_energy_type_by_selfplay()` — builds a deck per energy type (8
  types) via `build_optimized_mono_deck()`, round-robins all pairs, ranks by
  aggregate win rate.
- **Evaluation setup**: round-robin (40 matches/pair) across 8 energy types,
  then a direct 150-match head-to-head between the top two, then 200 matches
  vs. random for the final choice.
- **Number of matches**: 40/pair (round-robin), 150 (head-to-head), 200 (vs.
  random)
- **Seed**: 99 (round-robin, head-to-head), 42 (final vs.-random run)
- **Main changes**: `select_best_energy_type_by_selfplay()` /
  `build_best_mono_deck()` added to `src/deck.py`.

## Result

| Energy Type | Round-robin win rate |
|---|---|
| **Fire** | **70.8%** |
| Water | 57.9% |
| Metal | 54.2% |
| Grass | 49.2% |
| Psychic | 42.9% |
| Fighting | 37.5% |
| Darkness | 37.5% |
| Lightning | N/A — every match failed at `battle_start` (unresolved) |

Fire ranked highest in the aggregate round-robin — but a direct 150-match
Fire-vs-Water match found **Water wins 57.3%** head-to-head. Final submitted
deck (Water): **85.0%** vs. random (200 matches), draws: 1, aborted: 0.
Kaggle public score: 371.8.

## Discussion

Deck strength is not a single transitive ranking: Water ranks lower than Fire
in the aggregate round-robin but beats Fire specifically, a real
rock-paper-scissors-style intransitivity. Since resubmitting the unchanged
Fire deck would be redundant, Water was submitted as the genuinely new,
locally-validated variant. Separately, every Lightning-deck match failed at
engine `battle_start` (`errorType=2`) despite `validate_deck()` reporting no
violations — an undocumented deck-construction rule or a build-specific issue,
not resolved in this experiment.

## Next Action

- Investigate the Lightning `battle_start` failure (undocumented rule or
  `validate_deck()` gap).
- Test against a wider, more realistic pool of opponent archetypes rather than
  only this repo's own 6 mono-types, for a more decision-relevant ranking.

## Reproducibility

- **Command**: TBD — the exact CLI invocation for
  `select_best_energy_type_by_selfplay()` was run ad hoc on the
  `exp/003-deck-autoselect` branch; not preserved as a single reproducible
  command in this repo's current history. `src/deck.py` contains the function.
- **Config**: `experiments/003-deck-autoselect/config.yaml` (on
  `exp/003-deck-autoselect`, not on this repo's current default branch history
  — see Related Branch below)
- **Raw result**: `experiments/003-deck-autoselect/results.json` (same branch)
- **Full write-up**: `reports/003_writeup.md` (same branch)
- **Commit**: `82df6347a0957867630756be70f05e8cd3d06504`
- **Data dependency**: competition data (see EXP-001).

## Related Branch or Commit

- Legacy development branch: `exp/003-deck-autoselect` (sibling branch off
  EXP-002's commit; its `experiments/`/`reports/` files are not present on
  every later branch — see `docs/git-workflow.md` for why the legacy branch
  model diverged this way)
- Base commit: `82df6347a0957867630756be70f05e8cd3d06504`

## Status

Completed. Submitted to Kaggle (`exp003-water-deck`, public score 371.8).
