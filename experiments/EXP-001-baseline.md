# EXP-001: Baseline Arena — Heuristic vs. Random

## Objective

Prove the full pipeline end-to-end before attempting a strong agent: deck
construction → local self-play → win-rate evaluation → packaged Kaggle
submission. Establish the first measured baseline, not a competitive result.

## Hypothesis

A greedy, no-lookahead heuristic agent (fixed action-type priority table)
should beat a legal-random agent, even without any deck or scoring
sophistication.

## Implementation

- **Agent A**: `agents.heuristic_agent` — ranks legal options by a fixed
  priority (`ATTACK > EVOLVE > ATTACH > PLAY > ABILITY > YES > NO > RETREAT >
  END`), no lookahead.
- **Agent B**: `agents.random_agent` — picks uniformly among legal options.
- **Deck**: `data/decks/baseline_v1.csv` — mono-Fire, 6 distinct Basic Pokémon
  x4 copies + Fire Energy filler, identical deck for both sides.
- **Evaluation setup**: `src/arena.py` self-play, first player alternated per
  match to cancel first-move advantage.
- **Number of matches**: 200
- **Seed**: 42
- **Main changes**: N/A — this is the first experiment.

## Result

| Metric | Value |
|---|---|
| Win rate (heuristic vs. random) | **41.5%** |
| 95% Wilson CI | 34.9%–48.4% |
| Draws | 0 |
| Aborted matches | 0 |
| Kaggle public score | 135.0 |

Match-ending breakdown (supplementary run, same setup): ~53% deck-out, ~13%
no-Pokémon-in-play, ~33% decided by an actual KO race.

## Discussion

The heuristic agent did **not** beat random — its win rate sits below 50% and
the confidence interval does not clearly clear even odds. Over half of all
matches were decided by deck-out (running out of cards to draw) rather than
combat decisions, meaning the deck itself is a weak signal for comparing agent
quality here: with this deck, "who plays better" barely matters if the game is
mostly decided by which side decks out first. It is plausible the heuristic's
fixed priority order is simply noise at this n rather than actively harmful,
but it is equally possible the greedy order itself is suboptimal (e.g.
attacking without regard to trade quality). Both explanations were carried
into EXP-002.

Pipeline verification succeeded regardless of the win-rate result: 0 aborted
matches across 200 games, full pytest coverage passed, and a packaged
submission (`submissions/exp001-heuristic/`) matched the official
`sample_submission/` layout.

## Next Action

- Track *why* the heuristic loses (match-ending reason, not just win/loss).
- Add real card-draw/resource support to the deck so combat decisions (not
  deck-out timing) dominate outcomes.
- Revisit the fixed priority table (e.g. attack-quality awareness,
  de-prioritize RETREAT less bluntly).
- Confirm exact deck-building rules (copy limits, ACE SPEC) against the
  competition's official rules — `validate_deck()` used a best-effort default
  at this point.

## Reproducibility

- **Command**:
  ```bash
  python src/arena.py \
    --agent-a agents.heuristic_agent --agent-b agents.random_agent \
    --deck-a data/decks/baseline_v1.csv --deck-b data/decks/baseline_v1.csv \
    --n-matches 200 --seed 42
  ```
- **Config**: `experiments/001-baseline/config.yaml`
- **Raw result**: `experiments/001-baseline/results.json`
- **Full write-up**: `reports/001_baseline_writeup.md`
- **Commit**: `4801cfba4314ca0a123bee84917608204774bcea`
- **Data dependency**: competition data downloaded via `kaggle competitions
  download -c pokemon-tcg-ai-battle` (see root README) — required to
  regenerate the deck/agent behavior; not bundled in this repository.

## Related Branch or Commit

- Legacy development branch: `exp/001-baseline-arena`
- Base commit: `4801cfba4314ca0a123bee84917608204774bcea`

## Status

Completed. Submitted to Kaggle (`exp001-heuristic`, public score 135.0).
