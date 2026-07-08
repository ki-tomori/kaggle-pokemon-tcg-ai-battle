## Summary

<!-- 1-3 sentences: what changed and why. Link the experiment report if this
     PR corresponds to one (reports/0NN_*.md). -->

## Experiment reference

- Branch: `exp/0NN-...`
- Report: `reports/0NN_*.md`
- Experiment record: `experiments/0NN-.../{config.yaml,results.json}`

## Local validation

- [ ] `pytest` passes
- [ ] `black` / `flake8` clean
- [ ] `python src/evaluate_baseline.py` (or `arena.py`) run, results recorded
      in `experiments.csv` and the linked report
- Win rate vs. random: `__%` (n=`__`)
- Win rate vs. prior best (head-to-head, same deck if applicable): `__%` (n=`__`)

## Kaggle submission

- [ ] Not submitted — local result doesn't clear the confidence bar yet
      (see README § Submission Policy)
- [ ] Submitted — archive format: `.tar.gz` / `.zip`, slot(s): `__`, public
      score (once available): `__`

## Docs updated

- [ ] `docs/strategy.md` (if this changes the current best agent/deck or a
      known assumption)
- [ ] `improvement/roadmap.md` (remove what this PR did, add what it surfaced)
- [ ] `improvement/lessons_learned.md` (if something generalizable was learned)
- [ ] Root `README.md` Experiments table

## Notes for reviewers

<!-- Anything a reviewer should specifically sanity-check — a surprising
     result, a heuristic that looked right but needs a second opinion, an
     open question from the report's "Next steps." -->
