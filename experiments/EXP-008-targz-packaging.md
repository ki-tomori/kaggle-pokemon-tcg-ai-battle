# EXP-008: Submission Archive Format (.tar.gz vs. .zip)

## Objective

Not a strategy change. Tests whether the submission archive format matters:
every prior submission (EXP-002/003/004/005/007) was a `.zip`, but a
competitor's public repository documents the expected format as
`submission.tar.gz` containing `main.py`/`deck.csv`/`cg/` at the top level.

## Hypothesis

Repackaging the exact same agent+deck as EXP-007, but as `.tar.gz` instead of
`.zip`, will submit successfully and (if `.zip` was ever silently mishandled)
may change scoring behavior. If both formats work identically, this is a
confounded, inconclusive test given known matchmaking-luck variance.

## Implementation

- **Agent**: `agents.heuristic_v2_agent` — identical to EXP-007, unchanged.
- **Deck**: `data/decks/optimized_v2.csv` — identical to EXP-007, unchanged.
- **Evaluation setup**: N/A — no new local win-rate evaluation; this is a
  packaging-format test only.
- **Number of matches**: N/A
- **Seed**: N/A
- **Main changes**: added `--archive gztar` option to
  `src/package_submission.py`; resubmitted the identical EXP-007 agent/deck as
  `.tar.gz`.

## Result

- **Win rate**: N/A — no strategy change, no new local evaluation
- **Confidence interval**: N/A
- **Draws**: N/A
- **Aborted matches**: N/A
- **Other metrics**: Kaggle public score — pending at time of last recorded
  update in this repository (TBD — confirm current status against the Kaggle
  submissions page)

## Discussion

This is an explicitly confounded test: the competition's own "Leaderboard
Scoring Inconsistency" discussion documents identical agents scoring
150–400+ points apart purely from matchmaking luck, so a different score here
vs. EXP-007 would not be strong evidence either way on its own. The one clear
signal this test could have produced — an outright submission failure
(never scores / errors) — would have indicated the `.zip` format was the
problem; that did not happen (TBD — confirm final status).

## Next Action

- Confirm the final Kaggle status of this submission (score or persistent
  failure) and record it here.
- Treat archive format as settled (either format works) once confirmed, and
  stop re-testing it for future submissions.

## Reproducibility

- **Command**:
  ```bash
  python src/package_submission.py \
    --agent src/agents/heuristic_v2_agent.py --deck data/decks/optimized_v2.csv \
    --name exp008-targz-retest --archive gztar
  ```
- **Config**: `experiments/008-targz-packaging/config.yaml`
- **Raw result**: N/A — no `results.json` was recorded for this experiment
  (packaging-only, no new win-rate run)
- **Full write-up**: TBD — no dedicated `reports/008_*.md` write-up exists in
  this repository's history
- **Commit**: `99f550d44e43a5728ab3f42cf0a65aa7e6994855`
- **Data dependency**: competition data (see EXP-001).

## Related Branch or Commit

- Legacy development branch: `exp/008-targz-packaging`
- Base commit: `99f550d44e43a5728ab3f42cf0a65aa7e6994855`

## Status

Completed (packaging change only). Kaggle submission status: TBD — confirm
current score/status against the live Kaggle submissions page.
