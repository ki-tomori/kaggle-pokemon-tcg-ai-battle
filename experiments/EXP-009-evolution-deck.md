# EXP-009: Evolution-Line Deck (mixed/negative result, not submitted)

## Objective

Replay analysis of EXP-007's real Kaggle matches (21 games) found only a 30%
real win rate despite 92% locally vs. random. Inspecting a loss replay showed
the opponent using an evolved, Tool-equipped Pokémon dealing a single
170-damage hit — something the Basic-only `optimized_v2` deck has no analogue
for. This experiment designs and tests a deck built around real
Basic→Stage1 evolution lines instead of Basic attackers alone.

## Hypothesis

A deck built around evolution lines will out-damage the Basic-only deck
(Stage1 attacks reach up to 250 damage/energy vs. the low-60s/70s ceiling for
the best Basic attackers), and should beat the current best deck
(`optimized_v2`) once fielded reliably.

## Implementation

- **Agent**: `agents.heuristic_v2_agent` (unchanged, EXP-007's version) — no
  agent changes, isolates a deck-only question.
- **Deck**: `deck.build_evolution_line_deck(card_pool, attack_pool,
  energy_type, n_lines, n_draw_slots)` — picks `n_lines` distinct
  Basic→Stage1 pairs ranked by Stage1 attack damage-per-energy, 4 copies of
  each stage, padded with draw support and Basic Energy. A real bug was caught
  and fixed here: some Basics are the `evolvesFrom` target of more than one
  Stage1 (reprints), so naively taking the top-N Stage1s by efficiency could
  pick two Stage1s evolving from the same Basic, violating the copy limit —
  fixed by deduping on the Basic's card ID.
- **Evaluation setup**: `src/arena.py`, multiple deck variants (energy type ×
  number of evolution lines) vs. random and vs. the old Basic-only
  `optimized_v2` deck.
- **Number of matches**: 100 per cell (150 for the two Water 5-line rows)
- **Seed**: 42
- **Main changes**: `build_evolution_line_deck()` added to `src/deck.py`;
  duplicate-Basic bug fixed (covered by
  `tests/test_deck.py::test_build_evolution_line_deck_no_duplicate_basic_across_lines`).

## Result

| Deck | Lines | vs. random | vs. old Basic-only (`optimized_v2`, Fire) |
|---|---|---|---|
| Fire | 2 | 27% | 4% |
| Grass | 2 | 37% | 1% |
| Psychic | 2 | 56% | 43% |
| Water | 2 | 62% | 30% |
| Water | 4 | **72%** | **49%** |
| Water | 5 | 58% | 45.3% |

No variant beats the old Basic-only deck. Water/4-lines came closest (49%,
essentially a coin flip) but did not clear it. Not submitted to Kaggle.

## Discussion

Loss-reason breakdown explains why: with only 2 lines (16 Pokémon cards), the
deck runs out of Pokémon almost every loss (Fire/2-lines: 57/60 losses were
`no_pokemon_in_play`) — the same failure mode EXP-001 had with too few Basic
lines. Unlike a Basic-only deck, each evolution "attacker" costs *two* cards
(a Basic and its Stage1) instead of one, so the same 60-card budget buys far
fewer independently-usable attackers. Going to 4–5 lines fixes most of the
Pokémon-count problem but eats into the energy/draw budget instead (5 lines'
`deck_out` share roughly triples vs. 4 lines) — a genuine three-way resource
tradeoff (Pokémon count vs. energy count vs. draw support) that a naive fixed
split can't resolve well, especially since `heuristic_v2_agent` (at this
point) has no energy-sequencing intelligence to make the most of whatever it
draws. This is a genuine negative/mixed result: it confirms evolution attacks
hit far harder in principle, but shows that swapping in evolution lines
without addressing deck-consistency tradeoffs and agent resource-timing logic
doesn't pay off on its own.

## Next Action

- Try a hybrid deck: a few reliable Basic-only lines plus one or two strong
  evolution lines layered on top, rather than going all-in on evolution.
- Vary `n_draw_slots` independently of `n_lines` — this experiment changed
  both at once between the 2/4/5-line variants, confounding which knob
  mattered.
- Revisit the agent's lack of energy-attach sequencing logic (addressed later
  in EXP-010 and EXP-012).

## Reproducibility

- **Command**: TBD — the multi-variant sweep was run via ad hoc scripting on
  `exp/009-evolution-deck`, not preserved as a single reproducible CLI
  invocation.
- **Config**: N/A — no `config.yaml` was recorded for this experiment
- **Raw result**: `experiments/009-evolution-deck/results.json`
- **Full write-up**: `reports/009_evolution_deck.md`
- **Commit**: `a7c70db829af864c0a70cc8b466016f5cbbd6c90` (branch tip)
- **Data dependency**: competition data (see EXP-001).

## Related Branch or Commit

- Legacy development branch: `exp/009-evolution-deck`
- Base commit: `a7c70db829af864c0a70cc8b466016f5cbbd6c90`

## Status

Completed — mixed/negative result. Not submitted to Kaggle.
