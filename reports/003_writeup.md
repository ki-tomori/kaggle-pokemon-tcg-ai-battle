# Experiment 003 — Measure 1: Automated Energy-Type Selection

## Goal

One of three parallel measures tried after 002 (86.5% vs random locally, but
still a low observed Kaggle ladder score). This one asks: is Fire actually the
best energy type for this deck shape, or did we just get lucky picking it first?

## Method

`select_best_energy_type()` (a static score — sum of the top-6 basics' damage-per-
energy) was tried first and picked **Fighting**. That turned out to be wrong in
practice: Fighting lost ~62-70% of self-play matches against Fire or Water. A
static per-card efficiency number ignores HP, retreat cost interactions, and
weakness/resistance matchups between whole decks, so it's a poor proxy.

Replaced it with `select_best_energy_type_by_selfplay()`: build a deck per
standard energy type (8 types), round-robin all pairs (40 matches/pair,
`agents.heuristic_v2_agent` on both sides), and rank by aggregate win rate.

## Results

| Energy Type | Round-robin win rate |
|---|---|
| **Fire** | **70.8%** |
| Water | 57.9% |
| Metal | 54.2% |
| Grass | 49.2% |
| Psychic | 42.9% |
| Fighting | 37.5% |
| Darkness | 37.5% |
| Lightning | — (every match failed to start; see below) |

Fire — the type already used in experiment 002 — actually has the best
*aggregate* record. But a direct 150-match Fire-vs-Water match found **Water
wins 57.3% of the time head-to-head**, despite ranking lower in the aggregate
table. This is a real rock-paper-scissors-style intransitivity: Water's matchup
against Fire specifically is favorable even though Water does worse on average
against the full field of 6 other types.

Since resubmitting the unchanged Fire deck would be redundant, **submitted
Water** as the genuinely new variant — locally validated as better than 002's
deck in direct competition, at the cost of being weaker in aggregate against
the wider field.

vs. random (200 matches): **85.0%** win rate — essentially matching 002's 86.5%,
consistent with 002's own finding that deck changes beyond the initial
Fire pick don't move the needle much against a legal-random opponent; the
Water-vs-Fire head-to-head is the more informative comparison for this experiment.

## Known issue (unresolved)

Every attempted match with the auto-built **Lightning** deck failed at
`battle_start` (`errorType=2` for both player slots, no documented meaning in
the SDK). `validate_deck()` reported no violations, so this is either an
undocumented deck-construction rule our validator doesn't check, or specific to
the particular Lightning basics/draw cards this build picked. Not investigated
further given time — flagged for a follow-up experiment.

## Takeaway

Deck selection has real intransitivity — "best deck" depends on what you're
optimizing (beat one specific opponent vs. do well against a broad field), so
a single scalar ranking isn't the whole story. For the next iteration, matching
against a wider, more realistic pool of opponent archetypes (not just our own
6 mono-types) would give a more decision-relevant signal than either metric used here.
