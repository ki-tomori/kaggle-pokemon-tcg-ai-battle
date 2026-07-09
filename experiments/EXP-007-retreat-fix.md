# EXP-007: Retreat-Timing Fix on baseline_423

## Objective

Test whether `baseline_423`'s most common loss pattern (per
`outputs/loss_summary.md`: `prize_race`, 50% of losses) is driven by the agent
never retreating a critically-damaged active Pokémon, letting it soak
avoidable hits over a long, grindy game (losses averaged 175.5 actions vs.
99.1 in wins).

## Hypothesis

Porting the retreat-timing and healthiest-bench-switch logic already
validated in EXP-004's `heuristic_v3_agent` directly into the actual baseline
agent (`heuristic_v2_agent`) will reduce the `prize_race` loss share and
improve win rate over the frozen `baseline_423` snapshot.

## Implementation

- **Agent**: `agents.heuristic_v2_agent`, patched in place (not a new agent
  file) with exactly two additions: (1) `RETREAT` scores high (95) when the
  active Pokémon's HP is ≤30% of max and a healthy bench Pokémon exists,
  otherwise unchanged; (2) when choosing which bench Pokémon becomes active,
  score by HP fraction instead of falling back to "first option."
- **Deck**: `data/decks/optimized_v2.csv` (unchanged).
- **Evaluation setup**: `src/arena.py`, patched agent vs. the frozen
  `baseline_423` snapshot, and patched agent vs. random.
- **Number of matches**: 200
- **Seed**: 42
- **Main changes**: two scoring additions in `heuristic_v2_agent.py` (ported
  from EXP-004, not new logic).

## Result

| Matchup | Win rate |
|---|---|
| patched agent vs. frozen `baseline_423` | **53.5%** |
| patched agent vs. random | **92.0%** (up from 88.0% same-seed, 86.5% originally recorded in EXP-002) |

Draws: 0. Aborted: 0.

Loss-reason share (out of all losses vs. random), before → after:

| Reason | Before | After |
|---|---|---|
| prize_race | 50.0% | 33.3% |
| deck_out | 41.7% | 46.7% |
| no_pokemon_in_play | 8.3% | 20.0% |

Total losses out of 200 matches vs. random: 24 → 15. Kaggle public score:
304.2.

## Discussion

The fix worked as hypothesized: `prize_race`'s share of losses dropped
substantially (50% → 33.3%), and overall losses vs. random dropped by more
than a third (24 → 15). The head-to-head win rate against frozen
`baseline_423` (53.5%) is modest but consistent with EXP-004's finding (54.5%
for the same logic, there packaged as a separate agent) — a real, if not
dramatic, edge. `deck_out` and `no_pokemon_in_play` are unaffected in absolute
terms (this fix doesn't touch card-draw or Pokémon-count issues); their
*share* of losses rose only because the total number of losses shrank.

Despite the strong local numbers, this submission's real Kaggle ladder
performance (confirmed later via `kaggle competitions replay`) was only 6/20
(30%) real wins — a large gap from the 92%-vs-random local figure. This gap
became the motivating finding for the project's Submission Policy (see root
README) and for EXP-009's deck research.

## Next Action

- `deck_out` is now the largest single loss reason (46.7% of a smaller pool) —
  the next highest-leverage fix is probably still card-draw/resource related,
  not further agent-logic tuning.
- The 0.3 critical-HP threshold and the flat 95/5 RETREAT scores are
  hand-picked; a small threshold sweep using `evaluate_baseline.py` would be
  cheap to run before investing further.
- (Later, informed by replay analysis): investigate why local self-play
  overstates real ladder performance — see EXP-009.

## Reproducibility

- **Command**:
  ```bash
  python src/evaluate_baseline.py --n-matches 200 --seed 42
  ```
- **Config**: `experiments/007-retreat-fix/config.yaml`
- **Raw result**: `experiments/007-retreat-fix/results.json`
- **Full write-up**: `reports/007_writeup.md`
- **Commit**: `04840dbd8321832731ef990041a7bafbb06456d9`
- **Data dependency**: competition data (see EXP-001).

## Related Branch or Commit

- Legacy development branch: `exp/007-retreat-fix`
- Base commit: `04840dbd8321832731ef990041a7bafbb06456d9`

## Status

Completed. Submitted to Kaggle (`exp007-retreat-fix`, public score 304.2).
Real-ladder replay analysis later showed only 30% actual win rate despite 92%
locally vs. random — see EXP-009 and the root README's Submission Policy.
