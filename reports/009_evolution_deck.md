# Experiment 009 — Evolution-Line Deck (design + local results, not submitted)

## Motivation

Replay analysis of exp007's 21 real Kaggle matches (see the Submission Policy
section of the README) found only a 30% real win rate, despite 92% locally
vs. a random baseline. Inspecting a loss replay showed the opponent using an
evolved, Tool-equipped Pokémon dealing a single 170-damage hit — something
our Basic-only `optimized_v2` deck has no analogue for. This experiment
designs and tests a deck built around real Basic→Stage1 evolution lines
instead of Basic attackers alone.

## What was built

`deck.build_evolution_line_deck(card_pool, attack_pool, energy_type, n_lines, n_draw_slots)`:
picks `n_lines` distinct Basic→Stage1 pairs (matched via the Stage1's
`evolvesFrom` name field), ranked by the Stage1 attack's damage-per-energy,
4 copies of each stage, then pads with draw support and Basic Energy — same
shape as `build_optimized_mono_deck()` but with evolution lines instead of
Basics alone. Card pool check: Stage1 attacks reach up to **250 damage/energy**
(Water) and 220 (Fire), vs. the low-60s/70s ceiling for the best Basic
attackers found in experiment 002/003 — evolution is a real power increase
*if* the deck can reliably field it.

A real bug was caught and fixed during this: some Basics are the
`evolvesFrom` target of more than one Stage1 card (reprints/alternate forms
sharing a name), so naively taking the top-N Stage1s by efficiency could pick
two different Stage1s that evolve from the *same* Basic — 4+4 copies of that
Basic ID would then violate the per-card copy limit. `build_evolution_line_deck`
now dedupes by the Basic's card ID while selecting lines (`tests/test_deck.py::test_build_evolution_line_deck_no_duplicate_basic_across_lines`).

The existing agent (`agents.heuristic_v2_agent`, unchanged) handles `EVOLVE`
without modification — the engine presents each EVOLVE option fully specified
(source card + target Pokémon already resolved) within the same MAIN select,
so no second decision step or agent-side card-matching logic was needed.
Confirmed empirically: it evolves during real matches (10/20 test games).

## Results (100-150 matches/cell, seed 42)

| Deck | Lines | vs random | vs old Basic-only (optimized_v2, Fire) |
|---|---|---|---|
| Fire | 2 | 27% | 4% |
| Grass | 2 | 37% | 1% |
| Psychic | 2 | 56% | 43% |
| Water | 2 | 62% | 30% |
| Water | 4 | 72% | 49% |
| Water | 5 | 58% | 45.3% |

**No variant tried beats the old Basic-only deck.** Water/4-lines came
closest (49%, essentially a coin flip) but didn't clear it.

## Why: loss-reason breakdown tells a clear story

| Deck | no_pokemon_in_play | prize_race (real combat) | deck_out |
|---|---|---|---|
| Fire, 2 lines | 57/60 (95%) | 3/60 | 0 |
| Water, 4 lines | 32/60 (53%) | 23/60 | 5/60 |
| Water, 5 lines | 13/60 (22%) | 33/60 | 14/60 |

With only 2 lines (16 Pokémon cards), the deck runs out of Pokémon almost
every loss — the same failure mode experiment 001 had with too few Basic
lines. Unlike a Basic-only deck, each evolution "attacker" costs *two* cards
(a Basic **and** its Stage1) instead of one, so the same card budget buys far
fewer independently-usable attackers. Going to 4-5 lines fixes most of the
Pokémon-count problem, but then eats into the energy/draw budget instead —
5 lines' `deck_out` share roughly triples vs. 4 lines. This is a genuine
three-way resource tradeoff (Pokémon count vs. energy count vs. draw support)
that a naive fixed split (4 copies of each stage, fixed draw slots) can't
resolve well, and `heuristic_v2_agent` has no energy-sequencing intelligence
to make the most of whatever it draws.

## Conclusion — not submitted

None of these are a clear win over the current best (exp007, still the
active reference), so per the new Submission Policy this was **not**
submitted to Kaggle. This is a genuine negative/mixed result, not a dead end:
it confirms evolution attacks hit far harder in principle (the card-pool data
backs that up), but shows that swapping in evolution lines without also
addressing deck-consistency tradeoffs and the agent's lack of resource-timing
logic doesn't pay off on its own.

## Next steps

- Try a **hybrid** deck: a few reliable Basic-only lines (always usable, no
  evolution dependency) plus one or two strong evolution lines layered on top,
  rather than going all-in on evolution.
- Revisit `n_draw_slots` independently of `n_lines` — the current tests
  changed both at once between the 2/4/5-line variants, confounding which
  knob mattered.
- The agent doesn't reason about *when* to attach energy toward evolving vs.
  attacking now; some of the gap may be closeable with agent-side changes
  rather than deck changes.
