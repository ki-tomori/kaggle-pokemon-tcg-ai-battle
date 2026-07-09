# EXP-005: Search-Based Lookahead Agent

## Objective

Third of three parallel measures tried after EXP-002. Uses the engine-provided
`cg.api.search_begin`/`search_step` hypothetical-search API instead of only
static heuristics, for the MAIN-menu decision.

## Hypothesis

A 1-ply lookahead search over the engine's own hypothetical-state evaluation
should outperform (or at least match) the purely static v2 heuristic.

## Implementation

- **Agent**: `agents.search_agent` — for each legal MAIN option, takes one
  `search_step` from a `search_begin` root and evaluates the resulting
  hypothetical `State` (prize progress dominates the score; total remaining HP
  is the tiebreak). Falls back to `heuristic_v2_agent`'s static scoring
  whenever search isn't offered or if the search call raises.
- **Deck**: `data/decks/optimized_v2.csv` (unchanged from EXP-002).
- **Evaluation setup**: `src/arena.py`, search agent vs. random and vs. the v2
  agent, same deck both sides.
- **Number of matches**: 200
- **Seed**: 42
- **Main changes**: new `agents/search_agent.py` using `search_begin`/
  `search_step`.

## Result

| Matchup | Win rate (A) | 95% CI |
|---|---|---|
| search agent vs. random | 86.5% | 81.1–90.6% |
| search agent vs. v2 agent, same deck | 53.0% | 46.1–59.8% |

Draws: 0. Aborted: 0. One full match wall-clock time: ~0.147s (no per-move
timeout concern observed at this scale; the competition's exact timeout limit
was still unconfirmed at this point). Kaggle public score: 348.0.

## Discussion

Essentially a wash: 86.5% vs. random matches EXP-002/003's numbers almost
exactly, and 53.0% vs. v2 is barely above 50% (CI still straddles it). The
1-ply lookahead's main theoretical advantage — anticipating what happens after
an action — is undermined by a key limitation: `search_begin` requires a guess
for hidden information (our own remaining deck/prizes is grounded in the known
decklist, but the opponent's entire deck/prize/hand is a uniform sample over
the ~1267-card pool, i.e. completely uninformed). With almost no accurate
information about the opponent's hidden cards, the lookahead's guess is wrong
most of the time, and the evaluation function (prize progress + HP) is close
to what v2's damage-based scoring already approximates for a single attack
decision — leaving little room for the extra machinery to pay off at 1 ply.

## Next Action

- Deeper search (2+ ply) or many-sample averaging over the hidden-information
  guess would likely help more than search depth alone, since guess quality
  (not the lookahead mechanism) is the bottleneck.
- A learned or frequency-based opponent-deck model would make the
  opponent-hand guess far less uninformed than uniform-random sampling.

## Reproducibility

- **Command**: TBD — exact CLI invocation not preserved as a single command in
  this repo's current history; `agents/search_agent.py` and `src/arena.py` on
  `exp/005-agent-search` reproduce the setup.
- **Config**: `experiments/005-agent-search/config.yaml` (on
  `exp/005-agent-search`)
- **Raw result**: `experiments/005-agent-search/results.json` (same branch)
- **Full write-up**: `reports/005_writeup.md` (same branch)
- **Commit**: `82df6347a0957867630756be70f05e8cd3d06504`
- **Data dependency**: competition data (see EXP-001).

## Related Branch or Commit

- Legacy development branch: `exp/005-agent-search` (sibling branch off
  EXP-002's commit)
- Base commit: `82df6347a0957867630756be70f05e8cd3d06504`

## Status

Completed. Submitted to Kaggle (`exp005-search-agent`, public score 348.0).
