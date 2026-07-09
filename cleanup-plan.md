# Repository Cleanup Plan (Not Yet Executed)

This file tracks the remaining steps to reach the target Git/portfolio
structure described in `docs/git-workflow.md`. **Nothing in this file has been
executed** — it is a plan, written during the `feature/experiment-portfolio-docs`
documentation pass, which was scoped to adding documentation only (no branch
deletion, rename, rebase, or force-push; no code changes). Each item below is
a candidate for a future, separate, explicitly-approved change.

## Status of this pass

Done in this pass (documentation/index only, no code or branch changes):

- [x] `experiments/EXP-001-baseline.md` through `EXP-013-sequencing-audit-meta-deck.md`
- [x] `experiments/EXP-xxx-template.md`
- [x] `experiments/README.md` (experiment index + management policy)
- [x] `docs/git-workflow.md` (target branch model + rationale)
- [x] Root `README.md` reorganized as a concise portfolio entry point
- [x] This file (`cleanup-plan.md`)

## Open items (TBD / To be verified — not executed here)

1. **Bring `main` up to date.**
   `main` is currently at its original initial-scaffold commit
   (`4801cfba4314ca0a123bee84917608204774bcea`) and does not contain any of
   the `src/`, `experiments/`, or `reports/` work developed across
   EXP-001–013. Reviewers currently need to look at
   `feature/experiment-portfolio-docs` (or one of the legacy `exp/*`
   branches) to see the actual code. Decide and execute, in a separate,
   explicit step: which branch's code state should become the new `main` tip,
   and via what mechanism (a reviewed merge/PR is the safe default; nothing
   destructive like a forced branch replacement should be used without
   explicit sign-off).

2. **Decide the fate of the legacy `exp/*` branches.**
   Options, none executed here: (a) leave them as permanent historical
   records (lowest risk, matches this pass's "don't delete branches"
   constraint); (b) archive them (e.g. tag then delete, if the hosting
   platform's tooling makes old branches hard to browse) once their content is
   confirmed fully captured in `experiments/EXP-XXX-*.md` and no longer needed
   as live branches; (c) protect them as read-only. This project currently
   leans toward (a) for safety — no branch has been deleted, and this plan
   does not recommend deletion without an explicit, separate decision.

3. **Confirm `release/*` is actually needed.**
   Not used anywhere in this project's history yet. TBD whether a tagged
   release process (e.g. per Kaggle submission) would add value, or whether
   `experiments/EXP-XXX-*.md`'s existing "Related Branch or Commit" pointers
   already serve that purpose well enough.

4. **Fill remaining TBD fields.**
   A few experiment files have fields marked `TBD` where the source data
   available in this repository's history didn't contain a confirmed value
   (e.g. EXP-008's final Kaggle status, EXP-003/004/005's exact reproduction
   commands, EXP-010's Kaggle public score). Confirm these against the live
   Kaggle submissions page / any remaining local artifacts and update the
   corresponding `experiments/EXP-XXX-*.md` file directly — do not guess.

5. **Decide whether to reconcile with `docs/portfolio-and-memory`.**
   A separate, pre-existing branch (`docs/portfolio-and-memory`) contains an
   earlier, independent documentation pass (`docs/architecture.md`,
   `docs/strategy.md`, `improvement/`, a PR template, a win-rate figure, a
   LICENSE file) that was never merged with the `exp/*` experiment lineage.
   This restructuring did not attempt to merge or reconcile that branch — its
   content may overlap or conflict with the files added here (e.g. this pass
   also adds `docs/git-workflow.md`, a new file under `docs/`, but that branch
   already has its own `docs/` directory with different contents). Reconcile
   deliberately in a future step, not as a side effect of either pass.
