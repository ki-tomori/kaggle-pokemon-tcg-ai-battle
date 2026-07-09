# EXP-010: Turn-Sequencing Fix (Setup Actions Before Non-Lethal Attack)

## Objective

Strengthen the agent's own resource-planning logic instead of continuing to
tune the deck after EXP-009's mixed results. Look for a concrete, checkable
inefficiency in `heuristic_v2_agent`'s turn logic rather than another deck
variant.

## Hypothesis

If a single MAIN select can legally offer `ATTACK` at the same time as
setup actions (`ATTACH`/`EVOLVE`/`PLAY`/`ABILITY`), and attacking ends the
turn, then always scoring non-lethal `ATTACK` above every setup action is
throwing away free setup value that could still be taken before attacking.

## Implementation

- **Agent**: `agents.heuristic_v2_agent`, patched in place (on top of
  EXP-007's retreat-fix).
- **Deck**: `data/decks/optimized_v2.csv` (unchanged).
- **Evaluation setup**: `src/arena.py`, patched agent vs. random, and patched
  agent vs. the pre-fix (EXP-007) agent on the identical deck. A one-off
  diagnostic script (predecessor to EXP-013's reusable
  `src/diagnose_sequencing.py`) measured how often `ATTACK` co-occurred with a
  setup action in the agent's own MAIN decisions.
- **Number of matches**: 200
- **Seed**: 42
- **Main changes**: one-line scoring change — non-lethal `ATTACK`'s score
  changed from `100 + damage` (always above every setup action) to
  `45 + min(damage, 90) / 10` (always below `EVOLVE`=90/`ATTACH`=70/`PLAY`=65/
  `ABILITY`=55, still above `YES`=40/`NO`=30/`RETREAT`=5/`END`=0). Lethal
  `ATTACK` unchanged (`1000 + damage`, always top priority).

## Result

**Diagnostic**: `ATTACK` was offered alongside a setup action in 432 of 965
(44.8%) of this agent's own MAIN decisions in self-play — not a rare edge
case, close to half of all turns.

| Matchup | Win rate |
|---|---|
| patched vs. random | **97.0%** (up from 92.0% in EXP-007) |
| patched vs. EXP-007 (pre-fix), same deck | **70.0%** |

Draws: 0. Aborted: 0. This is the largest single-change improvement found in
the project to date — every previous change (EXP-003/004/005/007) landed in
the 53–57% head-to-head range; this one reached 70%. Losses vs. random dropped
from 24/200 (EXP-001-era baseline) → 15/200 (EXP-007) → **6/200** here. Kaggle
public score: pending at time of last recorded update (submitted to both
active slots).

## Discussion

This was not a deck problem or a scoring-weight problem — it was a
**sequencing** problem: the agent had all the right pieces (lethal detection,
damage scoring, retreat timing) but was ending its own turns early by
attacking before using its other actions. Fixing the order of operations, not
adding a new capability, produced the biggest single gain in the project so
far, confirming the hypothesis that agent-side resource/turn planning had more
room than further deck tuning at this point.

## Next Action

- Apply the same "does this MAIN select offer `ATTACK` simultaneously with a
  free action?" diagnostic to check for other overlooked sequencing gaps (e.g.
  `RETREAT` vs. `ATTACH` ordering) — done later, generalized into a reusable
  tool, in EXP-013.
- Re-check EXP-009's evolution-line decks with this sequencing fix applied —
  evolution decks may benefit more from correct sequencing (more setup actions
  per turn) than the simpler Basic-only deck did. (TBD — not yet re-tested as
  of this writing.)

## Reproducibility

- **Command**:
  ```bash
  python src/evaluate_baseline.py --n-matches 200 --seed 42
  ```
- **Config**: `experiments/010-attack-sequencing/config.yaml`
- **Raw result**: `experiments/010-attack-sequencing/results.json`
- **Full write-up**: `reports/010_attack_sequencing.md`
- **Commit**: `a7c70db829af864c0a70cc8b466016f5cbbd6c90`
- **Data dependency**: competition data (see EXP-001).

## Related Branch or Commit

- Legacy development branch: `exp/010-attack-sequencing`
- Base commit: `a7c70db829af864c0a70cc8b466016f5cbbd6c90`

## Status

Completed. Submitted to Kaggle, both active submission slots
(`exp010-attack-sequencing`), per the project's Submission Policy of averaging
out matchmaking-luck variance. Public score: pending at time of last recorded
update — confirm current status against the live Kaggle submissions page.
