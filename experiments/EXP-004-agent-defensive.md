# EXP-004: Defensive / Resource-Targeting Agent (v3)

## Objective

Second of three parallel measures tried after EXP-002. Holds the deck fixed
(EXP-002's Fire deck, `optimized_v2.csv`) and changes only agent logic, adding
a defensive dimension v2 didn't have.

## Hypothesis

Adding retreat-when-critical logic, healthiest-bench-switch targeting, and
energy-attach targeting will improve win rate over the v2 agent on an
identical deck.

## Implementation

- **Agent**: `agents.heuristic_v3_agent` — adds (1) retreat when the active
  Pokémon is ≤30% max HP and a healthy bench Pokémon is available, (2)
  healthiest-bench preference when choosing a new active Pokémon, (3) energy
  attachment targeted at whichever Pokémon most needs it to attack.
- **Deck**: `data/decks/optimized_v2.csv` (unchanged from EXP-002) — isolates
  an agent-only change.
- **Evaluation setup**: `src/arena.py`, v3 vs. random and v3 vs. v2 on the
  identical deck.
- **Number of matches**: 200
- **Seed**: 42
- **Main changes**: retreat-timing, switch-target, and attach-target scoring
  added to a new agent file (`heuristic_v3_agent.py`).

## Result

| Matchup | Win rate (A) | 95% CI |
|---|---|---|
| v3 agent vs. random (same deck as EXP-002) | **89.0%** | 83.9–92.6% |
| v3 agent vs. v2 agent, same deck | **54.5%** | 47.6–61.3% |
| (first version, before a fix) v3 vs. v2 | 39.5% | — |

Draws: 0. Aborted: 0. Kaggle public score: 320.0.

## Discussion

The first version of the energy-attach targeting scored attach targets purely
by "fewest additional energy needed to attack," regardless of whether the
target was the active Pokémon or a bench Pokémon. This **lost 39.5%**
head-to-head against the v2 agent — worse than not having the logic at all.
Redirecting energy off the active attacker toward a bench Pokémon closer to
its own readiness slows the active attacker's own race to knock out the
opponent first, which matters more than efficient resource allocation in a
fast KO-race meta. Fixed by keeping the active attacker as the default energy
target, only redirecting to the bench once the active no longer needs more
energy. After the fix: +2.5pp vs. random (86.5% → 89.0%) and a modest
head-to-head edge (54.5%, CI still straddles 50%, so "probably slightly
better," not conclusively so at n=200).

Key generalizable lesson: a heuristic that looks intuitively reasonable
(efficient resource allocation) can be a real regression once tested against
the current best agent rather than only against random — random is too weak
an opponent to reveal tempo trade-offs.

## Next Action

- The 0.3 critical-HP threshold and the flat retreat scores are hand-picked
  constants — a small threshold sweep (once a reliable local proxy for real
  ladder performance exists) would be cheap to run.
- Combine with EXP-003's Water deck once both are compared on the real
  leaderboard.

## Reproducibility

- **Command**: TBD — exact CLI invocation not preserved as a single command in
  this repo's current history; `agents/heuristic_v3_agent.py` and
  `src/arena.py` on `exp/004-agent-defensive` reproduce the setup.
- **Config**: `experiments/004-agent-defensive/config.yaml` (on
  `exp/004-agent-defensive`)
- **Raw result**: `experiments/004-agent-defensive/results.json` (same branch)
- **Full write-up**: `reports/004_writeup.md` (same branch)
- **Commit**: `82df6347a0957867630756be70f05e8cd3d06504`
- **Data dependency**: competition data (see EXP-001).

## Related Branch or Commit

- Legacy development branch: `exp/004-agent-defensive` (sibling branch off
  EXP-002's commit)
- Base commit: `82df6347a0957867630756be70f05e8cd3d06504`

## Status

Completed. Submitted to Kaggle (`exp004-defensive-v3`, public score 320.0).
