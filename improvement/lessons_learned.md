# Lessons Learned

This is the project's long-term memory. Read this before starting new work;
add to it whenever an experiment teaches something that would change how the
*next* experiment should be run. Organized by theme, not chronology — dates
and experiment numbers are given so you can trace a lesson back to its
report under `reports/`.

## Evaluation methodology

- **Vs-random win rate is a weak predictor of real strength.** Experiment 007
  won 92% locally vs. `random_agent` but only 30% (6/20) of its real Kaggle
  matches. Any local number in this repo should be read as "beats our own
  agents/decks by X%," never as a forecast of ladder performance. (exp007)
- **All-self-referential validation hides real weaknesses.** Every early
  local win-rate number came from our own agent playing our own decks or
  earlier versions of itself — a closed loop that can't reveal blind spots
  the opponent field actually has. Real opponents run mechanics (evolution,
  Tools, multi-Supporter play) this repo's own decks never exercised, so
  the agent's handling of those option types was completely untested until
  we deliberately sourced a real deck. (exp007 replay analysis → exp011)
- **Revalidate close results at higher N before trusting them.** An n=150
  read made two targeting heuristics look like a 6-8pp regression; re-running
  at n=350 showed both were statistically indistinguishable from 50% — pure
  noise. A community Discussion post independently reported the same trap at
  their own (much larger) scale: a "hill-climbed" config that looked like
  0.786 → 0.921 over rounds turned out to be a 1.37pp real gap once
  re-measured at n=2,000, because their accept-threshold (0.5pp) was well
  below their own sampling noise. Rule of thumb used in this repo: don't act
  on anything under ~5pp without a larger-N recheck. (exp012, corroborated by
  Discussion thread 713608)
- **Isolate before combining.** When three simultaneous changes regressed
  together (42% head-to-head), testing each in isolation revealed only one
  (damage-targeting) was actually harmful; the other two were neutral. Ablate
  one variable at a time rather than accepting or reverting a whole batch on
  a single combined read. (exp012)
- **A plausible rationale is not evidence.** Damage-targeting ("prefer the
  opponent's lowest-HP Pokémon") was the most intuitively obvious of three
  heuristics tried in exp012 and the one that clearly hurt (39.3%, held up
  under a repeat test). Ship based on measurement, not how reasonable the
  story sounds.
- **Check both directions of a claimed effect.** A Discussion post claiming
  the engine's own option ordering is already strong (a trivial "always pick
  index 0" baseline reportedly beats random ~88-90%) was worth checking
  before trusting our own scoring overrides. We verified: B1 does beat random
  91% locally, *and* our agent beats B1 70-30 — confirming our overrides are
  net-positive rather than fighting the engine's ordering (a failure mode the
  original poster reported for their own naive reorder). (exp011)

## Kaggle-specific / competition-mechanics

- **Score is highly noisy, independent of agent quality.** A well-upvoted
  Discussion thread ("Leaderboard Scoring Inconsistency," 64 votes) documents
  identical agents scoring 150-400+ points apart purely from early-matchmaking
  luck (e.g. one competitor's unchanged agent scored 940.7 on one submission
  and 790.8 on another; another saw a >400-point gap). Don't over-index on a
  single submission's score.
- **Only the latest two submissions per team stay active.** Submitting a new
  experiment stops the *older* one's games — effectively freezing its score
  wherever it happened to be, whether or not it had converged. This means
  resubmitting rapidly (as this project did early on, exp002 → exp003 within
  40 minutes) can leave every prior score essentially meaningless as a
  comparison point.
- **5 submissions/day is a real, easy-to-hit limit.** Discovered by hitting a
  400 error trying to submit a 6th time in a rolling day — not a code or
  format bug, just the daily cap (exp012's second-slot submission attempt).
- **Submission archive format was worth checking, but wasn't the real
  problem.** A competitor's public repo documents `.tar.gz` as the expected
  format (this repo had only ever used `.zip`); switching was cheap to try
  but the actual score gap between experiments was later traced to real
  agent/deck differences and matchmaking variance, not the archive format.
  (exp008)
- **Real replay data is directly downloadable and CC0-licensed.** Kaggle
  publishes daily top-episode datasets explicitly "to help in reviewing
  replays as well as training agents." Individual episode files can be
  selectively downloaded (no need to pull an entire ~21GB daily archive) and
  contain the exact 60-card deck each real competitor submitted, extractable
  via the episode JSON's `steps[1][agent_index]["action"]`. This is a
  stronger source of deck ideas than deriving one from card-database
  heuristics. (exp011)
- **`kaggle` CLI can read the Discussion forum without a browser session.**
  `kaggle competitions topics list <slug>` and
  `kaggle competitions topic-messages <slug> <topic_id>` return full thread
  text using only the API token already configured for downloads/submissions
  — no need to ask the user to paste Discussion content manually.

## Engineering process

- **Turn-sequencing bugs can hide behind "correct" per-option scores.** Every
  individual scoring value in `heuristic_v2_agent` looked reasonable in
  isolation; the bug was in the *relative* ordering (non-lethal ATTACK
  outranking free setup actions), invisible unless you check how often two
  option types are legal at the same decision point. Measured empirically at
  ~45% of this agent's own MAIN decisions before fixing it. (exp010)
- **A Basic can be the pre-evolution of more than one Stage1 card** (reprints
  / alternate forms sharing a name). Deck-building code that maps "pre-
  evolution name → card" and then picks several Stage1s independently can
  silently pick two Stage1s that evolve from the *same* Basic, producing an
  8-copy violation of the 4-copy limit. Dedupe by the Basic's card ID while
  selecting lines. (exp009)
- **Pokémon-count vs. energy-count vs. draw-count is a real three-way
  tradeoff with no free lunch from a fixed copy-count split.** Too few
  evolution lines → "ran out of Pokémon" losses; adding more lines to fix
  that eats into the energy/draw budget instead, and the substitution isn't
  obviously net-positive at a fixed formula. (exp009) Using a real deck
  instead of solving this analytically sidestepped the problem. (exp011)
- **`shutil.make_archive(base_name, format, root_dir)`** puts `root_dir`'s
  *contents* at the archive's top level (equivalent to `cd root_dir` first) —
  the right semantics for `main.py`/`deck.csv`/`cg/` needing to sit at the
  submission archive's root, not nested under a folder name.
- **`.so`/`.dylib` files don't need the executable bit** to be loaded via
  `ctypes.cdll.LoadLibrary` (dlopen-style loading only needs read access) —
  ruled out as a hypothesis for cross-platform submission failures without
  needing to actually test on Linux.

## Communication / process with the user

- The user wants genuine negative results reported as such, not reframed as
  wins — multiple experiments (009's evolution-deck tradeoff, 012's
  damage-targeting regression) were reported honestly as "didn't work,"
  which the user has consistently responded well to.
- Secrets (Kaggle API tokens) must never be pasted into chat, even when the
  user offers to — always redirect to a local terminal action instead. This
  came up twice early in the project and both times the right response was
  to decline and explain why, not to process the secret.
- When a message frames a preference as a durable rule ("don't resubmit for
  every small change"), it belongs in `CLAUDE.md`/README, not just in
  conversation memory — it should survive a fresh session.
