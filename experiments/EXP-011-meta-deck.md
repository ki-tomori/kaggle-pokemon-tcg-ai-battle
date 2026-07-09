# EXP-011: Real Meta Deck (Sourced From Official Top-Episode Data)

## Objective

Act on two findings from deeper Discussion-forum research rather than
continuing deck-tuning guesswork: (1) a community claim that the engine's own
option ordering is already strong, worth checking whether this project's
heuristic overrides are net-positive or "fighting the engine"; (2) Kaggle
publishes a CC0-licensed dataset of top-rated daily episodes explicitly for
training agents, and sampling it shows real top decks look structurally
nothing like this repo's prior decks.

## Hypothesis

A deck extracted directly from a real, played top episode will beat this
project's best hand-derived deck (`optimized_v2`) head-to-head, because real
decks invest far more of their 60 cards in trainer infrastructure
(Supporters/Items/Tools/Stadiums) than this repo's decks did.

## Implementation

- **Agent**: `agents.heuristic_v2_agent` (EXP-010's sequencing-fixed version,
  unchanged) — isolates a deck-only question.
- **Deck**: `data/decks/meta_v1.csv`, extracted via the new
  `deck.load_deck_from_episode_replay(replay_json_path, agent_index)` from
  episode 83709252 (agent_index=0), sourced from the official
  `kaggle/pokemon-tcg-ai-battle-episodes-2026-07-04` dataset — a real, played,
  legal 60-card, 18-distinct-card list, not another formula-derived guess.
- **Evaluation setup**: (part 1) a trivial `agents.first_index_agent` (always
  picks option 0) vs. random, and the EXP-010 agent vs. that trivial baseline,
  to sanity-check whether this project's heuristics add value or fight the
  engine's own ordering; (part 2) `meta_v1` vs. random, and `meta_v1` vs.
  `optimized_v2`, same agent both sides.
- **Number of matches**: 200 (part 1), 150 (part 2)
- **Seed**: 42
- **Main changes**: `deck.load_deck_from_episode_replay()` added to
  `src/deck.py`; new `agents/first_index_agent.py` (diagnostic only, not a
  candidate for submission).

## Result

**Part 1 (sanity check)**:

| Matchup | Win rate |
|---|---|
| first-index agent (B1) vs. random | 91% |
| EXP-010 agent vs. B1 | **70%** |

**Part 2 (meta deck)**:

| Matchup | Win rate |
|---|---|
| meta deck vs. random | 84.7% (150 matches) |
| meta deck vs. `optimized_v2`, same agent both sides | **72.0%** (150 matches) |

Meta deck composition: 18 distinct cards — 5 Pokémon (main line Basic 70hp →
Stage1 100hp → Stage2 ex 320hp, Darkness energy; secondary line Basic 70hp →
Stage1 90hp, Water energy), 4 Supporters, 5 Items, 1 Tool, 1 Stadium, 1 Basic
Energy, 1 Special Energy. Not submitted to Kaggle yet at time of writing.

## Discussion

Part 1 confirms this project's heuristic overrides (lethal detection, damage
scoring, retreat timing, setup-before-attack sequencing) clearly beat the
trivial "always pick index 0" baseline by a wide margin (70%) — the project's
agent logic is net-positive, not fighting the engine's own ordering, as one
Discussion post had warned could happen with a naive re-scoring.

Part 2's vs-random number (84.7%) is *lower* than `optimized_v2`'s own 97% —
but per this project's own established lesson (EXP-007: 92% vs. random turned
out to be only 30% vs. real opponents), vs-random is a weak predictor of real
strength. The head-to-head result is the more meaningful signal, and it's
decisive: the real meta deck beats the prior best deck 72–28 when piloted by
the identical agent. Loss reasons vs. random are 68% real combat outcomes,
only ~1.7% deck-out — the deck is structurally sound; the vs-random gap most
likely reflects the agent under-using the richer trainer package
(Tool/Stadium/multi-Supporter decisions still fell back to a flat default
score at this point) rather than any flaw in the deck itself.

## Next Action

- Add scoring logic for gust/forced-switch Supporters and Tool-attachment
  targeting (done in EXP-012).
- Re-run the head-to-head once that agent logic lands, to see how much of the
  72% gap was "better deck" vs. "better deck, imperfectly piloted."
- Sample more episodes/days from the dataset to confirm this deck shape is
  representative, not an artifact of one day's meta snapshot (queued as a
  later proposal, not yet executed as of this writing).

## Reproducibility

- **Command**:
  ```bash
  python src/arena.py \
    --agent-a agents.heuristic_v2_agent --agent-b agents.heuristic_v2_agent \
    --deck-a data/decks/meta_v1.csv --deck-b data/decks/optimized_v2.csv \
    --n-matches 150 --seed 42
  ```
- **Config**: `experiments/011-meta-deck/config.yaml`
- **Raw result**: `experiments/011-meta-deck/results.json`
- **Full write-up**: `reports/011_meta_deck.md`
- **Commit**: `956baa11af307e9461412540a723e8deab59428f`
- **Data dependency**: competition data (see EXP-001), plus the
  `kaggle/pokemon-tcg-ai-battle-episodes-2026-07-04` dataset (episode
  83709252) used to source `data/decks/meta_v1.csv` — not bundled in this
  repository.

## Related Branch or Commit

- Legacy development branch: `exp/011-meta-deck`
- Base commit: `956baa11af307e9461412540a723e8deab59428f`

## Status

Completed. Not submitted to Kaggle at time of writing — held pending
dedicated Supporter/Tool/Stadium agent logic (see EXP-012) so the submission
reflects informed play, not raw deck power alone.
