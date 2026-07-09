# EXP-012: Gust / Tool / Damage Targeting (mixed result, honestly reported)

## Objective

Per Discussion thread 721338 (Boss's Orders / Ultra Ball usage advice) and
EXP-011's finding that `meta_v1`'s richer trainer package exercises `CARD`
selects the agent had never handled with anything but a flat default score,
add dedicated targeting logic for gust effects, damage-target selection, and
energy/Tool attach targeting.

## Hypothesis

Adding target-aware scoring for these three option categories (instead of a
flat default that effectively picks whichever option is listed first) will
improve win rate over the pre-change agent on `meta_v1`.

## Implementation

- **Agent**: `agents.heuristic_v2_agent`, patched in place — three additions:
  (1) gust-target scoring (forcing an opponent's benched Pokémon active):
  prefer low HP, still-Basic, already-energized, or high retreat cost targets;
  (2) damage-target scoring: prefer the opponent's lowest-HP Pokémon when a
  card effect lets us choose who takes damage; (3) attach-target scoring
  (ported from EXP-004's validated logic, not previously in this agent):
  prefer powering up the active attacker.
- **Deck**: `data/decks/meta_v1.csv` (unchanged from EXP-011).
- **Evaluation setup**: ablation testing — isolate each of the three
  heuristics individually, head-to-head vs. the pre-change agent, at two
  sample sizes to check for noise.
- **Number of matches**: 150 (initial ablation), 350 (revalidation), 300 (all
  three combined), 200 (final vs. random / vs. `optimized_v2`)
- **Seed**: 42 (initial ablation), 7 (revalidation), 99 (final head-to-head)
- **Main changes**: `_gust_target_score`, `_attach_target_score` added and
  kept; `_damage_target_score` added and then removed after ablation.

## Result

All three changes together: 42% head-to-head vs. the pre-change agent (n=200)
— a regression, not a gain. Isolated:

| Heuristic (isolated) | vs. pre-fix, n=150 | vs. pre-fix, n=350 (revalidated) |
|---|---|---|
| Attach-targeting only | 46.0% | 51.1% |
| Gust-targeting only | 47.3% | 49.1% |
| Damage-targeting only | 39.3% | not revalidated — signal was already clear |

Final agent (attach + gust only, damage-targeting removed): 52.0% vs.
pre-fix agent (n=300, statistically neutral); 80.5% vs. random (n=200); 73.0%
vs. `optimized_v2`, same agent (n=200). Not submitted to Kaggle at time of
writing.

## Discussion

The n=150 reads for attach/gust looked like a real (if small) regression;
re-running at n=350 showed both are statistically indistinguishable from 50%
— **noise, not signal**, exactly the "hill-climbing below the noise floor"
trap flagged in Discussion thread 713608. Damage-targeting's negative signal
held up and was clearly the dominant cause of the combined regression.
**Damage-targeting was removed** — preferring the opponent's lowest-HP Pokémon
as a damage target sounds reasonable but measurably hurt play in this deck,
possibly because the `DAMAGE` context here isn't cleanly "assign to whoever's
weakest" in every case this deck encounters. Rather than keep a
plausible-sounding but empirically-negative heuristic, it was cut.
**Attach- and gust-targeting were kept**, since neither showed real harm at a
properly-sized sample, both are principled (attach-targeting was already
validated positively on a different deck in EXP-004), and both replace an
arbitrary "first in list" fallback with a reasoned choice — but this
experiment does not claim they're a proven win; they're neutral-to-plausible,
not validated gains. With this updated agent, `meta_v1` still clearly beats
`optimized_v2` head-to-head (73.0%, matching EXP-011's 72.0% finding with the
pre-update agent) — the deck remains the strongest, most reliable lever found
in the project so far, stronger than any single agent-logic tweak tried.

## Next Action

- The gust/attach targeting additions aren't a demonstrated win on their own,
  so they don't meet the submission bar by themselves. The
  **agent (EXP-010's sequencing fix + these neutral-but-harmless additions) +
  `meta_v1` deck** combination is validated twice at ~72–73% head-to-head
  against the previous best submitted deck — a legitimate candidate for the
  next submission, pending confidence and user go-ahead.
- Any close result from now on should be revalidated at N≥300 before being
  trusted (this became a standing project practice, applied again in
  EXP-013).

## Reproducibility

- **Command**:
  ```bash
  python src/arena.py \
    --agent-a agents.heuristic_v2_agent --agent-b agents.heuristic_v2_agent \
    --deck-a data/decks/meta_v1.csv --deck-b data/decks/meta_v1.csv \
    --n-matches 300 --seed 99
  ```
  (agent-b run from a pre-change checkout of `heuristic_v2_agent.py`; see
  `src/diagnose_sequencing.py`'s approach in EXP-013 for the general pattern
  of comparing against a `git show <commit>:path` snapshot.)
- **Config**: N/A — no `config.yaml` was recorded for this experiment
- **Raw result**: `experiments/012-gust-tool-targeting/results.json`
- **Full write-up**: `reports/012_gust_tool_targeting.md`
- **Commit**: `2783c861487c73d361caf95ef5a4e8a198f353e9` (base), `8b624e9`
  (this experiment's own tip)
- **Data dependency**: competition data (see EXP-001).

## Related Branch or Commit

- Legacy development branch: `exp/012-gust-tool-targeting`
- Base commit: `2783c861487c73d361caf95ef5a4e8a198f353e9`

## Status

Completed — mixed result, honestly reported. Not submitted to Kaggle at time
of writing (the kept changes are neutral-to-harmless, not a validated win by
themselves; the deck+agent combination as a whole remains a candidate).
