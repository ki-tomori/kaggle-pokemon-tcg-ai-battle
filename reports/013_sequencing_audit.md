# Experiment 013 — Sequencing Audit on meta_v1's Fuller Option Space (neutral result, honestly reported)

## Goal

Experiment 010 found and fixed one specific turn-sequencing bug: a MAIN select
can legally offer `ATTACK` alongside setup actions (`ATTACH`/`EVOLVE`/`PLAY`/
`ABILITY`), and the agent was always attacking as soon as it was legal,
throwing away free setup value. That fix was never generalized — it covered
exactly one `OptionType` pair, found via a one-off throwaway script. `meta_v1`
(exp011) exercises a much richer option space (evolution lines, multiple
Supporters, a Tool, a Stadium) than the deck exp010 was validated against, so
this experiment built a reusable diagnostic and re-ran the audit against it.

## Diagnostic tool

`src/diagnose_sequencing.py` adds a `select_observer` hook to
`arena.py::play_match`/`play_n_matches` (a reusable extension point, not a
one-off script) that logs, at every select of a chosen `SelectType`, which
`OptionType`s were simultaneously legal — building a co-occurrence matrix
(marginal frequency + conditional co-occurrence + top combos) instead of
checking one pair by hand.

## Finding: RETREAT-vs-ATTACK is the highest untested pairing

Ran 300 self-play matches (`heuristic_v2_agent` vs itself, `meta_v1` deck both
sides), sampling 26,254 MAIN selects:

| OptionType | Share of MAIN selects offering it |
|---|---|
| END | 100% (always present) |
| ABILITY | 63.1% |
| PLAY | 55.8% |
| RETREAT | 47.4% |
| ATTACK | 22.7% |
| ATTACH | 19.3% |
| EVOLVE | 12.0% |

Conditional on `ATTACK` being offered, `RETREAT` is also offered **92.4%** of
the time — far above any setup-action pair (e.g. `ATTACH`-`ABILITY` 81.6%,
`PLAY`-`ABILITY` 77.7%). This is the pair exp010 never specifically measured.

Traced live matches to check whether `RETREAT` ends the turn the way `ATTACK`
does: it doesn't — the select immediately after an agent-chosen `RETREAT` is
an `ENERGY` select (paying the retreat cost), same turn and same player. But
retreating does foreclose that turn's `ATTACK` option, since attacks belong to
whichever Pokémon is currently active — once retreated, that specific attack
opportunity is gone for the turn.

The existing code (`_RETREAT_WHEN_CRITICAL_SCORE = 95`) always preferred
retreating a critical-HP (≤30% max HP) active over any non-lethal `ATTACK`,
regardless of how much damage the forgone attack would have dealt — a fixed
constant that ignored a damage estimate the agent already computes for every
`ATTACK` option.

## Fix

Lowered `_RETREAT_WHEN_CRITICAL_SCORE` from 95 to 50 — inside the existing
non-lethal-`ATTACK` scoring band (45–54) rather than above it. A weak attack
(low score, near 45) still loses to retreating; a strong one (near 54) now
wins. No new heuristic or threshold was added — this reuses the
weakness/resistance-adjusted damage score `_attack_damage` already computes.

## Result: statistically neutral, does not clear the submission bar

| Run | n | seed | win_rate (post-fix vs pre-fix) |
|---|---|---|---|
| 1 | 350 | 42 | 52.6% |
| 2 | 350 | 123 | 48.0% |
| 3 | 500 | 7 | 49.8% |
| **Combined** | **1200** | — | **51.45%** |

51.45% over 1200 games is well short of the 53–57% "mediocre improvement"
range exp010 established as the noise floor for real changes, and is not
distinguishable from a coin flip at this sample size. vs `random_agent`: 83.5%
(n=200) — no regression there.

**Why the effect is likely just small, not necessarily absent**: a follow-up
measurement found the exact decision this fix touches (active critical **and**
both `ATTACK` and `RETREAT` simultaneously offered) occurs in only **2.6%** of
MAIN selects (200 matches, 16,852 MAIN selects sampled). A rare decision point
diluted across ~150+ actions per mirror-self-play game is plausibly too small
a signal to separate from noise at n=1200, even if the underlying logic is an
improvement in the specific matchups where it fires.

## Decision

**Kept the code change** (sound logic, no measured harm, replaces an
unconditional constant with one the existing damage score can arbitrate
against) but **did not submit to Kaggle** — the result does not clear this
project's submission bar (only submit a candidate that clearly beats the
53–57% mediocre-tweak range).

## Lessons

- A high co-occurrence frequency for an `OptionType` **pair** doesn't mean the
  specific **sub-condition** a fix changes (here, critical HP within that
  pair) is itself frequent — measure the narrower condition too before
  expecting a large aggregate win-rate signal.
- Generalizing exp010's one-off diagnostic into a reusable tool
  (`select_observer` on `arena.play_match`) paid for itself immediately and
  should be reused for the still-open ordering questions (`ABILITY` vs `PLAY`,
  multiple-Supporter priority) queued as later proposals — those involve
  actions that don't end the turn and can likely just be sequenced in either
  order without cost, unlike the RETREAT/ATTACK case, which is worth checking
  explicitly before assuming they matter.
