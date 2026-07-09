# EXP-002: Deck Optimization + Lethal-Aware Heuristic (v2)

## Objective

Improve on EXP-001's result (heuristic lost to random, 41.5%) toward a
stronger Kaggle ladder rating. Community discussion on this competition
consistently claims deck quality matters more than agent sophistication,
especially early on — this experiment tests deck and agent changes together
but separates their individual contributions.

## Hypothesis

Fixing EXP-001's deck-out problem (card-draw support) and adding
lethal-detection/damage-aware attack scoring will both improve win rate, but
the deck change is expected to matter more than the agent change, per
community discussion.

## Implementation

- **Agent**: `agents.heuristic_v2_agent` — adds lethal-attack detection
  (does this attack's damage, with a crude weakness ×2 / resistance −20
  adjustment, meet or exceed the opponent's active Pokémon's current HP?) and
  ranks non-lethal attacks by estimated damage instead of treating all
  `ATTACK` options as equally preferred.
- **Deck**: `data/decks/optimized_v2.csv` — Basic Pokémon chosen by
  damage-per-energy efficiency instead of arbitrary pool order, tie-broken by
  lower retreat cost / higher HP, plus card-draw Item/Supporter cards added to
  cut the deck-out rate found in EXP-001.
- **Evaluation setup**: three `src/arena.py` runs isolating deck vs. agent
  contribution (v2 agent + new deck vs. random; v1 agent + new deck vs.
  random; v2 agent vs. v1 agent, same new deck).
- **Number of matches**: 200 per run
- **Seed**: 42
- **Main changes**: `deck.build_optimized_mono_deck()` (new), lethal detection
  + damage scoring added to the agent.

## Result

| Matchup | Win rate (A) | 95% CI |
|---|---|---|
| v2 agent + new deck vs. random + new deck | **86.5%** | 81.1–90.6% |
| v1 agent (EXP-001 logic) + new deck vs. random + new deck | 82.5% | 76.6–87.1% |
| v2 agent vs. v1 agent, both on the new deck | 49.0% | 42.2–55.9% |

Draws: 0. Aborted matches: 0. Kaggle public score: **423.3** — the best score
recorded in this project to date (recorded as the frozen reference snapshot
`baseline_423`; see `reports/baseline_423_overview.md`).

## Discussion

The new deck alone (with EXP-001's simple agent logic) already reaches 82.5%
vs. random — almost all of the total gain. Swapping in the v2 agent's
lethal-detection/damage-scoring on top of the same deck adds only ~4 points
(86.5% vs. 82.5%), and head-to-head v2 vs. v1 on identical decks is
statistically even (49%, CI straddles 50%). This confirms the community's
claim: **deck quality dominated agent sophistication at this stage.** The
end-reason breakdown backs this up — matches decided by an actual KO race
jumped from 33% (EXP-001) to 82.5% here; decking out dropped from >50% to
~10%. The draw-support cards fixed the structural problem EXP-001 identified,
rather than smarter attack-scoring doing the work.

## Next Action

- The v2-vs-v1 near-tie suggests the next real gain is elsewhere: more
  distinct attacker lines, evolution-line decks (deliberately avoided here —
  the agent has no evolve-timing logic yet), or more draw/search support.
- Confirm the actual per-move time budget before investing in
  `cg.api.search_begin/search_step` lookahead (unconfirmed at this point).
- Track real leaderboard rating once Kaggle reports it, not just local
  win rate vs. this repo's own baselines.

## Reproducibility

- **Command**:
  ```bash
  python src/arena.py \
    --agent-a agents.heuristic_v2_agent --agent-b agents.random_agent \
    --deck-a data/decks/optimized_v2.csv --deck-b data/decks/optimized_v2.csv \
    --n-matches 200 --seed 42
  ```
- **Config**: `experiments/002-heuristic-v2/config.yaml`
- **Raw result**: `experiments/002-heuristic-v2/results.json`
- **Full write-up**: `reports/002_baseline_writeup.md`
- **Frozen reference snapshot**: `experiments/baseline_423/` (this exact
  agent+deck combination, recorded for future regression comparisons via
  `src/evaluate_baseline.py`)
- **Commit**: `4740d31cdf7133c262d45c3d9df030310b7cfb83`
- **Data dependency**: competition data (see EXP-001).

## Related Branch or Commit

- Legacy development branch: `exp/002-heuristic-v2`
- Base commit: `4740d31cdf7133c262d45c3d9df030310b7cfb83`

## Status

Completed. Submitted to Kaggle (`exp002-heuristic-v2`, public score 423.3 —
best score in this project as of this writing; recorded as `baseline_423`,
the standing regression-comparison reference).
