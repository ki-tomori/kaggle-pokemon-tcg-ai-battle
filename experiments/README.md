# Experiment History

This is the experiment log for the Pokémon TCG AI Battle project. It is the
authoritative, human-readable record of what was tried, in order — read this
before the Git history if you want to understand how the project evolved.

| Experiment | Summary | Key Result | Status |
|---|---|---|---|
| [EXP-001](./EXP-001-baseline.md) | Baseline arena: heuristic vs. random, full pipeline smoke test | 41.5% win rate (heuristic lost to random) | Completed |
| [EXP-002](./EXP-002-heuristic-v2.md) | Deck optimization (draw support, efficiency picks) + lethal-aware agent | 86.5% vs. random; best Kaggle score so far (423.3) | Completed |
| [EXP-003](./EXP-003-auto-deck-selection.md) | Automated energy-type selection via round-robin self-play | Water deck beats Fire 57.3% head-to-head despite lower aggregate rank | Completed |
| [EXP-004](./EXP-004-agent-defensive.md) | Defensive agent: retreat timing, switch/attach targeting | 89.0% vs. random; 54.5% vs. v2 agent | Completed |
| [EXP-005](./EXP-005-agent-search.md) | 1-ply `search_begin`/`search_step` lookahead agent | 53.0% vs. v2 agent — near-even, uninformed opponent-hand guess limited the gain | Completed |
| [EXP-006](./EXP-006-eval-harness.md) | Local regression harness + frozen `baseline_423` snapshot | Tooling only — no agent/deck change | Completed (tooling) |
| [EXP-007](./EXP-007-retreat-fix.md) | Port retreat-timing fix into the actual baseline agent | 92.0% vs. random locally; only 30% on the real ladder (see Submission Policy) | Completed |
| [EXP-008](./EXP-008-targz-packaging.md) | Resubmit EXP-007 as `.tar.gz` instead of `.zip` | Packaging-format test, no strategy change | Completed |
| [EXP-009](./EXP-009-evolution-deck.md) | Evolution-line deck, motivated by real-opponent replay analysis | Best variant (Water, 4 lines) reached 49% vs. the old deck — did not clear it | Completed (negative/mixed) |
| [EXP-010](./EXP-010-attack-sequencing.md) | Fix: setup actions before non-lethal attack (turn-sequencing bug) | **70.0%** head-to-head — largest single-change gain in the project | Completed |
| [EXP-011](./EXP-011-meta-deck.md) | Deck sourced from a real top-episode replay (Kaggle's official dataset) | 72.0% head-to-head vs. the prior best deck | Completed |
| [EXP-012](./EXP-012-gust-tool-targeting.md) | Gust/attach/damage targeting for meta_v1's richer option space | Damage-targeting was a clear regression (removed); attach/gust kept as neutral | Completed (mixed) |
| [EXP-013](./EXP-013-sequencing-audit-meta-deck.md) | Reusable sequencing-audit tool + critical-retreat-vs-attack fix | 51.45% over n=1200 — statistically neutral, not submitted | Completed (neutral) |

Full experiment configs, raw results, and prior write-ups also exist under
`experiments/NNN-.../` (per-experiment config/results files) and
`reports/*.md` (narrative write-ups with figures) — the `EXP-XXX-*.md` files
above are the portfolio-facing summary layer on top of that raw data, not a
replacement for it. See each file's **Reproducibility** section for exact
pointers.

## Experiment Management Policy

- Experiment history is managed in this directory (`experiments/`), not by
  keeping a long-lived Git branch per experiment.
- Git branches are used only for active development (see
  `../docs/git-workflow.md`) — the legacy `exp/NNN-*` branches referenced in
  each experiment's **Related Branch or Commit** section are kept as
  historical development records and are not deleted, but they are no longer
  how experiment history is tracked or presented.
- Each experiment documents objective, hypothesis, implementation, result,
  discussion, and next action in a consistent format (see
  `EXP-xxx-template.md`).
- Experiment IDs (`EXP-001`, `EXP-002`, ...) are independent of Git branch
  names — an experiment's ID never changes even if its underlying branch is
  renamed, merged, or eventually archived.
- This structure is designed to keep the GitHub branch list clean and the
  project's experiment history readable as a portfolio artifact, without
  requiring a reader to check out branches to understand what was tried.
- Negative and neutral results (EXP-003's intransitivity, EXP-009's mixed
  deck result, EXP-012's partial regression, EXP-013's neutral finding) are
  recorded with the same rigor as positive ones — this is a decision log, not
  a highlight reel.
