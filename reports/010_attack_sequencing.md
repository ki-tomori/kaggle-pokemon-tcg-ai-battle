# Experiment 010 — Fix Turn Sequencing (Setup Actions Before Attack)

## Goal

The user asked to strengthen the agent's own resource-planning logic instead
of continuing to tune the deck after exp009's mixed results. This looks for a
concrete, checkable inefficiency in `heuristic_v2_agent`'s turn logic rather
than another deck variant.

## Diagnosis

A single MAIN select can legally offer `ATTACK` **at the same time** as
`ATTACH`/`EVOLVE`/`PLAY`/`ABILITY` — this happens whenever a Pokémon already
has enough energy to attack from a previous turn, but this turn's energy
attachment, evolution, or trainer play hasn't happened yet. Attacking ends the
turn, so the previous version of `heuristic_v2_agent` (which always scored
non-lethal `ATTACK` at `100 + damage`, above every setup action) was throwing
away a full turn's worth of free setup value every time this happened —
attaching that turn's energy, evolving, or playing a trainer card would still
have been possible *before* attacking, at zero cost, but the agent never got
there because it attacked immediately instead.

Measured directly in self-play: **432 of 965 (44.8%)** of this agent's own
MAIN decisions offered `ATTACK` alongside a setup action. This is not a rare
edge case — it's close to half of all turns.

## Fix

One-line change in `agents/heuristic_v2_agent.py`: non-lethal `ATTACK`'s score
changed from `100 + damage` (always above every setup action) to
`45 + min(damage, 90) / 10` (always below EVOLVE=90/ATTACH=70/PLAY=65/ABILITY=55,
still above YES=40/NO=30/RETREAT=5/END=0). Lethal `ATTACK` is unchanged
(`1000 + damage`, still always the top priority — finishing the game now is
correct regardless of what else is legal).

## Results (200 matches, seed 42, deck unchanged)

| Matchup | Win rate |
|---|---|
| patched **vs** random | **97.0%** (up from 92.0% in exp007) |
| patched **vs** exp007 (pre-fix), same deck | **70.0%** |

This is by far the largest single-change improvement found in this project —
every previous change (003-005, 007) landed in the 53-57% head-to-head range;
this one reaches 70%. Losses vs random dropped from 24/200 (exp001-style
baseline) → 15/200 (exp007) → **6/200** here.

## Reading the result

This wasn't a deck problem or a scoring-weight problem — it was a **sequencing**
problem: the agent had all the right pieces (lethal detection, damage scoring,
retreat timing) but was ending its own turns early by attacking before using
its other actions. Fixing the order of operations, not adding a new capability,
produced the biggest single gain in the project so far. This matches the
user's hypothesis that agent-side resource/turn planning had more room than
further deck tuning at this point.

## Submission

Per the Submission Policy (README), this is the first candidate since exp002
confident enough to submit: it beats both random (97% vs 92%) and the
immediately-prior agent (70% head-to-head, well clear of the ~53-57% seen from
every earlier tweak) by a wide margin, not just a coin-flip edge. Submitted to
**both** currently-active slots to get two independent scores and average out
the matchmaking-luck variance documented in the Discussion forum, rather than
trusting a single submission's score.

## Next steps

- Apply the same "does this MAIN select offer ATTACK simultaneously with a
  free action?" diagnostic to check for other overlooked sequencing gaps
  (e.g. RETREAT vs ATTACH ordering).
- Re-check exp009's evolution-line decks with this sequencing fix applied —
  the earlier negative result was measured against the pre-fix agent, and
  evolution decks may benefit more from correct sequencing (more setup actions
  per turn: attach *and* evolve) than the simpler Basic-only deck did.
