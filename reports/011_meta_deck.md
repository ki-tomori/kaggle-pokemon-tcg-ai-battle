# Experiment 011 — Real Meta Deck (from official top-episode data)

## Goal

Deeper Discussion research (see README's Submission Policy update) surfaced
two things worth acting on before more deck-tuning guesswork:

1. A community post ("What We Tried, What Ceilinged...") claims the engine
   enumerates legal options in a strong best→worst order — enough that just
   returning index 0 ("B1") beats random ~88-90%, and that a *naive*
   type-priority re-scoring can actually lose to B1. Worth checking whether
   our own heuristic overrides are the "good" kind or the "fighting the
   engine" kind.
2. Kaggle publishes a CC0-licensed dataset of top-rated daily episodes
   (`kaggle/pokemon-tcg-ai-battle-episodes-index`), explicitly "to help in
   reviewing replays as well as training agents." Sampling it shows real top
   decks are structurally nothing like this repo's prior decks.

## Part 1 — Sanity check: are our overrides fighting the engine's ordering?

Built `agents/first_index_agent.py` (always returns `[0]`, or the first
`minCount` indices). Results on `optimized_v2` (200 matches, seed 42):

| Matchup | Win rate |
|---|---|
| B1 vs random | 91% (matches the Discussion post's reported ~88-90%) |
| exp010 agent vs B1 | **70%** |

Our agent clearly beats the trivial baseline by a wide margin — unlike the
Discussion poster's "naive reorder," our overrides (lethal detection, damage
scoring, retreat timing, setup-before-attack sequencing) are net-positive, not
fighting the engine's own ordering.

## Part 2 — What real top decks actually look like

Downloaded 5 sample episodes from `kaggle/pokemon-tcg-ai-battle-episodes-2026-07-04`
(the manifest also revealed top/median *real* leaderboard scores run
1250-1400 / 1000-1180 — our best submission, 423.3, sits well below the
*median* of the actively-competitive population, not just below "800").
All 5 sampled episodes happened to be mirror matches; the 5 distinct 60-card
lists share a consistent shape:

| Category | Count in the sampled deck |
|---|---|
| Pokémon (main evolution line) | Basic(70hp) → Stage1(100hp) → **Stage2 ex(320hp)** |
| Pokémon (secondary line) | Basic(70hp) → Stage1(90hp), different energy type |
| Supporter | 4 distinct cards |
| Item | 5 distinct cards |
| Tool | 1 |
| Stadium | 1 |
| Basic Energy | mostly 1 type |

This repo's best prior deck (`optimized_v2`) has **9 distinct cards total**
(6 Basic attackers + 2 generic "draw" Items + 1 Energy) — no evolution, no
Tool, no Stadium, no Supporter beyond generic draw. Real decks invest far more
of their 60 cards in trainer infrastructure than in attackers.

## What was built

`deck.load_deck_from_episode_replay(replay_json_path, agent_index)`: extracts
a 60-card deck straight from a downloaded episode JSON's deck-selection step
(`steps[1][agent_index]["action"]`). Used to pull episode 83709252's deck
(agent_index=0) as `data/decks/meta_v1.csv` — a **real, played, legal deck**
rather than another guess from our own efficiency formulas. `heuristic_v2_agent`
(exp010's version, unchanged) piloted it without modification.

## Results (agent unchanged — exp010's sequencing-fixed heuristic)

| Matchup | Win rate |
|---|---|
| meta deck vs random | 84.7% (150 matches) |
| meta deck **vs** `optimized_v2`, same agent both sides | **72.0%** (150 matches) |

The vs-random number (84.7%) is *lower* than `optimized_v2`'s own 97% —
but per this project's own established lesson (exp007: 92% vs random was only
30% vs real opponents), vs-random is a weak predictor of real strength. The
head-to-head result is the more meaningful signal here, and it's decisive:
the real meta deck beats our best prior deck **72-28** when piloted by the
identical agent. Loss reasons vs random are 68% real combat outcomes (prize
race), only 1.7% deck-out — the deck is structurally sound; the vs-random gap
most likely reflects the agent under-using the richer trainer package
(Tool/Stadium/multi-Supporter decisions still fall back to a flat default
score) rather than any flaw in the deck itself.

## Not yet submitted

This is a promising, evidence-based candidate, but the agent doesn't yet have
any dedicated logic for the option types this deck actually exercises for the
first time (multi-Supporter choice, Tool attachment targeting, Stadium play,
gust-style forced-switch effects) — it's winning on raw deck power despite,
not because of, informed play in those areas. Per the Submission Policy,
holding this for one more round to add that agent-side logic (the
Boss's-Orders-style targeting rules from Discussion thread 721338) before
submitting is likely to compound the gain rather than submit a still-partial
improvement now.

## Next steps

- Add scoring logic for gust/forced-switch Supporters (target the best KO,
  or a benched pre-evolution threat, or an already-energized attacker — the
  concrete rules from Discussion 721338) and Tool-attachment targeting.
- Re-run this same head-to-head once that lands, to see how much of the 72%
  gap was "better deck" vs. "better deck, imperfectly piloted."
- Sample more episodes / days from the dataset rather than relying on one
  mirror match, to confirm this deck shape is representative and not an
  artifact of a single day's meta snapshot.
