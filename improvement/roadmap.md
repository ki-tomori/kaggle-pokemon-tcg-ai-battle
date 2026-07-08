# Roadmap

Prioritized backlog, consolidated from every experiment report's "Next
steps" section. Re-prioritize this file whenever a new experiment lands —
don't let it drift out of sync with `reports/`. Check
[lessons_learned.md](lessons_learned.md) before starting any of these, since
several are directly informed by past mistakes.

## High priority (strong evidence, clear next action)

- [ ] **Merge validated branches toward `main`.** `main` is still the
  original scaffold commit — every experiment (001-012) lives on an
  unmerged sibling branch. For portfolio visibility and to give Claude Code
  (and any human) a single source of truth, promote the current best
  combination (exp010's sequencing-fixed agent + exp012's targeting logic +
  `meta_v1` deck) into `main` via a real PR, once exp012's Kaggle score
  confirms it's a genuine improvement over exp002's 423.3.
- [ ] **Per-Supporter and Item-specific logic.** All Supporter/Item cards
  currently share one flat `PLAY` priority. Discussion thread 721338's central
  ask (when to hold vs. use a Boss's-Orders-style gust effect; what to
  discard for an Ultra-Ball-style search) has concrete, quotable community
  advice not yet implemented — see `docs/strategy.md`'s "Known gaps."
- [ ] **Re-run experiment 009's evolution-line decks with the sequencing fix
  applied.** exp009's negative result was measured against the *pre-*
  sequencing-fix agent (exp007-era); exp010 alone was the single largest
  win-rate jump found in the project, and evolution decks have *more* setup
  actions per turn (attach *and* evolve) to sequence correctly than the
  simple Basic-only deck did. The conclusion "evolution decks don't help"
  may not hold anymore.
- [ ] **Apply the "does this MAIN select offer ATTACK simultaneously with a
  free action?" diagnostic elsewhere.** exp010 found and fixed one instance
  of this bug class (~45% of decisions affected). Check for the equivalent
  pattern around RETREAT vs. ATTACH/EVOLVE ordering, and any other option
  pair that might be legally simultaneous but scored as if mutually exclusive.

## Medium priority (plausible, not yet validated)

- [ ] **Sample more days/episodes from the top-episode dataset** rather than
  relying on the single mirror match `meta_v1` came from, to confirm that
  deck shape is representative of the current meta and not a one-day
  snapshot artifact.
- [ ] **Confirm exact deck-building legality rules** (copy limits, ACE SPEC,
  any competition-specific adjustments) against the official Rules page —
  `src/deck.py`'s `validate_deck()` is explicitly best-effort standard-TCG
  rules, never confirmed against this competition directly. Use the
  `competition-researcher` subagent (`.claude/agents/`) for this.
- [ ] **Confirm the actual per-move/per-match time budget.** Community
  sources suggest a 10-minute whole-match chess clock, not a per-move limit,
  but this was never confirmed directly from the competition's own Rules
  page. Matters more once/if a deeper-search agent is attempted.
- [ ] **Threshold sweep** on `heuristic_v2_agent`'s hand-picked constants
  (critical-HP retreat threshold, gust-target low-HP threshold) using
  `src/evaluate_baseline.py` as the harness, now that it exists — these were
  chosen by judgment, not tuned.

## Lower priority / exploratory

- [ ] **Deeper search or better opponent-hand modeling.** Experiment 005's
  1-ply `search_begin`/`search_step` agent was a statistical wash against the
  static heuristic, likely because the opponent's hidden hand is guessed
  uniformly at random — a frequency-informed guess (e.g. from the top-episode
  dataset's card usage) might make search actually pay off where a uniform
  guess didn't.
- [ ] **Hybrid Basic + evolution-line deck** (a few reliable Basic-only lines
  for consistency, one or two strong evolution lines layered on top) instead
  of committing fully to either extreme — a middle ground neither exp009 nor
  exp011 tried directly.
- [ ] **Independent tuning of `n_lines` vs. `n_draw_slots`** in
  `build_evolution_line_deck()` — exp009 changed both at once between its
  2/4/5-line variants, confounding which knob actually mattered.

## Explicitly not planned

- **Reverse-engineering or redistributing the `cg` engine / card database.**
  Out of scope per the competition's licensing terms (see README's
  Data & License Notice) regardless of any technical feasibility.
