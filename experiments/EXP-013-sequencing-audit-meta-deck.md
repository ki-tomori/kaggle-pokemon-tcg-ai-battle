# EXP-013: Sequencing Audit on meta_v1's Fuller Option Space (neutral result)

## Objective

EXP-010 found and fixed one specific turn-sequencing bug (`ATTACK` vs. setup
actions) via a one-off, throwaway diagnostic script. That fix was never
generalized or re-run against `meta_v1`'s much richer option space (evolution
lines, multiple Supporters, a Tool, a Stadium). This experiment builds a
reusable diagnostic and re-audits option-type sequencing on `meta_v1`.

## Hypothesis

Some other `OptionType` pair — not just `ATTACK` vs. setup actions — is
frequently co-offered in the same MAIN select and may have an unexamined,
sub-optimal fixed priority ordering.

## Implementation

- **Agent**: `agents.heuristic_v2_agent`, patched in place.
- **Deck**: `data/decks/meta_v1.csv` (unchanged from EXP-011/012).
- **Evaluation setup**: new `select_observer` hook on
  `arena.py::play_match`/`play_n_matches`, and a new reusable diagnostic
  (`src/diagnose_sequencing.py`) that logs, at every select of a chosen
  `SelectType`, which `OptionType`s were simultaneously legal — building a
  co-occurrence matrix instead of checking one pair by hand.
- **Number of matches**: 300 (co-occurrence audit), 200 (scope check), 1200
  across 3 seeds (validation), 200 (vs. random sanity check)
- **Seed**: 42, 123, 7 (validation seeds)
- **Main changes**: `_RETREAT_WHEN_CRITICAL_SCORE` lowered from 95 to 50 (into
  the existing non-lethal-`ATTACK` scoring band of 45–54).

## Result

Co-occurrence audit (300 matches, 26,254 MAIN selects sampled): `RETREAT` is
offered alongside `ATTACK` in **92.4%** of selects that offer `ATTACK` at
all — far above any setup-action pair (e.g. `ATTACH`-`ABILITY` 81.6%). Traced
live matches: `RETREAT` does not end the turn, but does forfeit that turn's
`ATTACK` option (attacks belong to whichever Pokémon is currently active).

| Run | n | seed | win_rate (post-fix vs. pre-fix) |
|---|---|---|---|
| 1 | 350 | 42 | 52.6% |
| 2 | 350 | 123 | 48.0% |
| 3 | 500 | 7 | 49.8% |
| **Combined** | **1200** | — | **51.45%** |

vs. random (sanity check): 83.5% (n=200), no regression. Scope check: the
decision this fix changes (active critical **and** both `ATTACK` and
`RETREAT` offered) fires in only 2.6% of MAIN selects (200 matches, 16,852
MAIN selects sampled). Not submitted to Kaggle.

## Discussion

51.45% over n=1200 is well short of the 53–57% "mediocre improvement" range
EXP-010 established as a real-change noise floor, and is not statistically
distinguishable from a coin flip at this sample size. The scope-check finding
offers a plausible, non-contradictory explanation: the specific sub-condition
this fix changes (critical HP *and* both options offered) is rare enough
(2.6% of MAIN selects) that any real effect is likely too small to separate
from noise in mirror self-play at n=1200, even if the underlying logic is
sound. The change was kept (no measured harm, reuses the existing damage
score rather than adding a new heuristic) but does not meet this project's
submission bar.

## Next Action

- The still-open ordering questions queued from this and prior experiments
  (`ABILITY` vs. `PLAY` ordering, multiple-Supporter `PLAY` priority) likely
  involve actions that don't end the turn and can probably be sequenced in
  either order without cost — check the narrower "does this ordering actually
  matter" question explicitly (as this experiment did for `RETREAT`) before
  assuming it does.
- A high co-occurrence frequency for an `OptionType` pair does not imply the
  narrower sub-condition a candidate fix changes is itself frequent — measure
  the narrower condition before expecting a large aggregate win-rate signal.

## Reproducibility

- **Command**:
  ```bash
  python src/diagnose_sequencing.py \
    --agent agents.heuristic_v2_agent --deck data/decks/meta_v1.csv \
    --n-matches 300 --seed 42 --output experiments/013-sequencing-audit-meta-deck/diagnostics.json
  ```
- **Config**: N/A — no `config.yaml` recorded (this experiment used
  `results.json`/`diagnostics.json` directly; see EXP-xxx-template for the
  recommended format going forward)
- **Raw result**: `experiments/013-sequencing-audit-meta-deck/results.json`,
  `experiments/013-sequencing-audit-meta-deck/diagnostics.json`
- **Full write-up**: `reports/013_sequencing_audit.md`
- **Commit**: `8b624e95fcb1d8a4f905d696d5c7725c1e76febf` (base, pre-fix)
- **Data dependency**: competition data (see EXP-001).

## Related Branch or Commit

- Legacy development branch: `exp/013-sequencing-audit-meta-deck`
- Base commit: `8b624e95fcb1d8a4f905d696d5c7725c1e76febf`

## Status

Completed — neutral result, honestly reported. Not submitted to Kaggle.
