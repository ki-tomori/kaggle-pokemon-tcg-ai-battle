<!--
Copy this file to reports/0NN_short_description.md and fill it in.
Keep sections that don't apply short ("N/A — no deck change this round")
rather than deleting them — a reader scanning many reports benefits from a
consistent shape more than from a "clean" doc.

See existing reports/*.md for real examples of this structure in practice,
and experiments/README.md for the full experiment lifecycle this fits into.
-->

# Experiment 0NN — <Short Title>

## Goal

What question is this experiment answering, and why now? Link back to the
specific finding, Discussion thread, or roadmap item that motivated it
(`improvement/roadmap.md`, a prior report, or a user request).

## Method

- **Agent**: which module, and what changed (if anything) vs. the prior best.
- **Deck**: which file, and what changed (if anything).
- **Opponent(s)** tested against, and why those specifically.
- Anything about the experimental design worth flagging up front — e.g. "this
  isolates the deck from the agent by holding the agent fixed."

## Results

Table or short list of the actual numbers — win rate, n, seed, and any
diagnostic breakdown (loss reasons, ablation results). Prefer a table over
prose here; save interpretation for the next section.

| Matchup | Win rate | n | Seed |
|---|---|---|---|
| | | | |

## Reading the result

What does this number mean? Is it a real signal or within noise for this N
(see `improvement/lessons_learned.md` on revalidating close results)? Does it
confirm or contradict something in `docs/strategy.md`? If the result is
negative or mixed, say so plainly — this repo's history has more value from
honest negative results than from reframing them as wins.

## Submission decision

- Was this submitted to Kaggle? If yes: archive format, submission
  description used, which slot(s).
- If not submitted: what's the specific bar it didn't clear (see the root
  README's Submission Policy), and what would need to be true to submit it.

## Next steps

Concrete, actionable follow-ups this experiment surfaced — these should feed
directly into `improvement/roadmap.md` (add them there, don't just leave them
buried in this file).
