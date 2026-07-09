# Git Workflow

## Target branch model

This project uses three branch categories going forward:

| Branch | Purpose |
|---|---|
| `main` | Stable, reviewable snapshot of the project. TBD / To be verified: `main` has not yet been updated to include the code and history developed on the legacy `exp/*` branches (see below) — this is a known, open item, not yet executed as part of this documentation pass. |
| `feature/*` | Active development: a new capability, refactor, or (per this repository's convention) a piece of documentation/tooling work. Example: `feature/experiment-portfolio-docs`, the branch this restructuring itself was done on. |
| `release/*` | TBD / To be verified — not yet used in this project's history. Reserved for tagging a stable point intended for external use (e.g. a specific Kaggle submission snapshot), if that becomes useful later. |

Experiment history itself is **not** tracked via long-lived branches under
this model — see `../experiments/README.md`'s Experiment Management Policy.
An experiment is recorded as a markdown file under `experiments/`, not as a
branch that has to stay alive to preserve its history.

## Why this changed

Early in this project (EXP-001 through EXP-013), each experiment was
developed on its own dedicated branch (`exp/001-baseline-arena`,
`exp/002-heuristic-v2`, ... `exp/013-sequencing-audit-meta-deck`), usually
branched from whichever prior experiment's branch was the strongest at the
time (a "sibling branching" model, not a linear chain off `main`). This was
convenient for iterative, exploratory work, but it left `main` itself
un-updated (still at the initial scaffold commit) and produced a long, hard-to
scan branch list — not a good first impression for a portfolio reviewer
opening the repository on GitHub.

Going forward, active work happens on `feature/*` branches, and experiment
*history* (as opposed to in-progress *development*) is recorded as files
under `experiments/`, independent of whatever branch happened to host the
work.

## Legacy branches

The following branches represent this project's actual development history
and are **kept, not deleted**, per this restructuring's constraints:

```
exp/001-baseline-arena
exp/002-heuristic-v2
exp/003-deck-autoselect
exp/004-agent-defensive
exp/005-agent-search
exp/006-eval-harness
exp/007-retreat-fix
exp/008-targz-packaging
exp/009-evolution-deck
exp/010-attack-sequencing
exp/011-meta-deck
exp/012-gust-tool-targeting
exp/013-sequencing-audit-meta-deck
docs/portfolio-and-memory
```

Each experiment's `EXP-XXX-*.md` file under `experiments/` links back to its
originating branch and base commit in a **Related Branch or Commit** section,
so the branch remains available for exact reproduction without needing to be
part of the everyday branch list a reviewer sees first. No branch listed above
was deleted, renamed, rebased, or force-pushed as part of this restructuring.

## Open items (not executed by this documentation pass)

See `../cleanup-plan.md` for the full list of follow-up steps (e.g. bringing
`main` up to date, deciding whether/when to archive the legacy `exp/*`
branches) that are intentionally **not** performed here — this pass only adds
documentation, per its own constraints.
