# Strategy

Living document: what we currently know about winning this competition, what
our agent actually does, and where the known gaps are. Update this whenever
an experiment changes the picture — this is the file to read before
proposing a new experiment, not the individual `reports/*.md` write-ups
(those are historical records; this is the current synthesis).

## The competition, in one paragraph

"Pokémon TCG AI Battle" is a Kaggle Simulations-category competition (like
Halite/Kore/Lux AI): a submission is a Python `agent(obs_dict) -> list[int]`
function plus a fixed 60-card deck, playing continuous matches against other
competitors' submissions on a live ladder. Score is a Gaussian skill rating
(TrueSkill-style) that resets on every resubmission and only the **latest two**
submissions per team stay active. See
[README.md § Submission Policy](../README.md#submission-policy) for the
operational consequences of that.

## What actually moves the score, ranked by evidence strength

1. **Deck quality dominates agent sophistication.** Confirmed independently
   three times: our own experiment 002 (a deck swap alone closed 41.5% →
   82.5%, agent logic added only +4pp on top), a Discussion post analyzing
   nine failed agent architectures against a fixed deck ("Deck was the
   lever, not the pilot"), and experiment 011 (a real top-player deck beat
   our best hand-built deck 72-73% head-to-head with the *same* agent).
2. **Turn-sequencing bugs are cheap to have and expensive to keep.**
   Experiment 010 found the agent was ending its own turns early ~45% of the
   time (attacking instead of using free setup actions first) and fixed it
   for the single largest win-rate jump in the project (70% head-to-head,
   vs. 53-57% for every other tweak). Worth auditing for *other* instances of
   "is this option-type priority actually forced, or could a free action
   happen first" before assuming a scoring-weight change is the next lever.
3. **Vs-random win rate is a weak predictor of real strength.** Experiment
   007's agent won 92% locally vs. `random_agent` but only 30% (6/20) of its
   actual Kaggle matches (confirmed via `kaggle competitions replay`). Every
   number in this repo's local reports should be read as "beats our own
   agents/decks by X%", not "will score X% for real."
4. **Plausible-sounding heuristics don't all survive contact with the
   engine.** Experiment 012 found that "target the opponent's lowest-HP
   Pokémon for damage-choice effects" — the most intuitively obvious of three
   targeting heuristics added that round — was the one that clearly
   regressed (39.3% isolated, confirmed at two sample sizes), while the two
   effects with less obvious payoff (gust-targeting, attach-targeting) turned
   out statistically neutral. Ship based on measurement, not plausibility.

## Current best agent: what it actually does

`src/agents/heuristic_v2_agent.py` (no lookahead, pure static scoring per
legal option):

1. **Lethal attack** always wins immediately, regardless of anything else
   offered (`damage >= opponent's active HP`).
2. Otherwise, **setup actions first**: EVOLVE > ATTACH > PLAY > ABILITY all
   outrank a non-lethal ATTACK, because attacking ends the turn (experiment
   010). ATTACH targets whichever of our own Pokémon most needs energy to
   attack, preferring the active attacker over redirecting to the bench
   (experiment 004's logic, ported in experiment 012).
3. **RETREAT** is conditional: only preferred when the active Pokémon is
   critically damaged (≤30% max HP) and a healthy bench Pokémon exists
   (experiment 007); otherwise deprioritized.
4. **Switch-in choice** (forced or voluntary) prefers our own healthiest
   bench Pokémon; a **gust effect** targeting the *opponent's* bench (e.g. a
   Boss's-Orders-style Supporter) prefers a low-HP / still-Basic / already-
   energized / high-retreat-cost target instead (experiment 012, statistically
   neutral so far — see lessons_learned.md).
5. Everything else (attack-damage estimate) applies a crude weakness (×2) /
   resistance (−20) adjustment using only the two active Pokémon — no
   bench, no pre-evolution, no multi-turn planning.

## Current best deck

`data/decks/meta_v1.csv` — extracted directly from a real, played, top-rated
match via Kaggle's official CC0 `pokemon-tcg-ai-battle-episodes-*` dataset
(not hand-derived). 18 distinct cards: a 3-stage evolution line
(Basic 70hp → Stage1 100hp → Stage2 *ex* 320hp), a secondary partial
evolution line, 4 Supporters, 5 Items, 1 Tool, 1 Stadium, and mostly one
Basic Energy type. This is structurally unlike every earlier hand-built deck
in this repo (which topped out at ~9 distinct cards with no evolution, Tool,
or Stadium at all) — see `reports/011_meta_deck.md`.

## Known gaps (things the agent doesn't do yet)

- **No lookahead beyond the current legal-options menu.** A 1-ply
  `search_begin`/`search_step` variant (experiment 005) was statistically a
  wash against the static heuristic — likely because the opponent's hidden
  hand/deck has to be guessed uniformly at random, which limits how much a
  1-ply search can actually see.
- **No per-Supporter distinction.** Multiple different Supporter cards in
  hand all score under the same flat `PLAY` priority; the agent can't yet
  reason about e.g. holding a gust effect for the turn it swings the game
  vs. playing a draw Supporter immediately (Discussion thread 721338's
  central point about Boss's Orders usage).
- **No card-specific Item logic** (e.g. an Ultra-Ball-style "search 1, discard
  2" decision) — Item plays are also flat-scored.
- **No evolution-line awareness in deck construction beyond a single metric.**
  `build_evolution_line_deck()` (experiment 009) picks lines by attack
  efficiency only and found a real Pokémon-count vs. energy-count tradeoff
  it couldn't resolve with a fixed copy-count split; `meta_v1` sidesteps this
  by using a real deck instead of solving the tradeoff algorithmically.
- **Exact deck-building legality rules are still best-effort**, not confirmed
  against the competition's own rules page (`src/deck.py`'s module docstring
  flags this explicitly).

For what to do about any of this next, see
[improvement/roadmap.md](../improvement/roadmap.md).
