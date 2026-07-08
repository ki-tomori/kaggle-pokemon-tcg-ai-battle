# Architecture

How this repo's code fits together, and why it's shaped this way. For *what
the agent currently does strategically*, see [strategy.md](strategy.md). For
*why specific decisions were made over time*, see
[../improvement/lessons_learned.md](../improvement/lessons_learned.md).

## The competition's contract

A submission is a single Python function:

```python
def agent(obs_dict: dict) -> list[int]:
    ...
```

Called once with `obs_dict["select"] is None` to request a 60-card deck
(a list of card IDs), and repeatedly thereafter with a legal-options menu
(`obs_dict["select"]["option"]`) — the return value is a list of *indices*
into that menu (length between `minCount` and `maxCount`, no duplicates).
The engine is a compiled C library (`cg`), shipped as part of the competition
data, wrapped in Python via `ctypes`. This repo never modifies that SDK; it
only imports and drives it.

## Module map

```
src/
├── config.py               Paths, constants (SEED, DECK_SIZE, ...) — the
│                            only place hardcoded values are allowed to live.
├── cg_bridge.py             sys.path bridge so the rest of src/ can
│                            `import cg_bridge` without knowing where the
│                            vendored `cg` SDK sits on disk. Never raises,
│                            even if data/ hasn't been downloaded yet —
│                            check_sdk_available() is how tests skip
│                            gracefully on a fresh clone.
├── deck.py                  Deck construction + legality validation, and
│                            (experiment 011+) extraction of real decks from
│                            downloaded top-episode replay JSON.
├── agents/                  Agent policies. Each file is a pure
│                            Observation -> list[int] function.
│                            *** Kaggle-portable constraint ***
│                            Files here may import only the standard library
│                            and `cg.api`/`cg.game` — never `from src...
│                            import` anything. src/package_submission.py
│                            copies these files byte-for-byte into a
│                            submission's main.py, which runs standalone
│                            with only the vendored `cg` package alongside
│                            it. An agent file that imported from `src`
│                            would work locally and fail silently (or crash)
│                            once packaged.
├── arena.py                 Local self-play match runner + win-rate stats
│                            (play_match, play_n_matches, ArenaStats).
├── evaluate.py               Wilson-CI win-rate summary + plotting for a
│                             single arena run.
├── evaluate_baseline.py      The standing regression harness: run N matches
│                             for a candidate agent/deck against a chosen
│                             opponent and write outputs/{eval_results,
│                             loss_cases}.csv + loss_summary.md. This is what
│                             you run before deciding whether to submit.
└── package_submission.py     Assembles submissions/<name>/{main.py, deck.csv,
                              cg/} from an agent file + deck CSV, and
                              archives it (.tar.gz by default). Contains no
                              agent logic of its own — it only copies files.
```

**Why packaging is decoupled from agent logic**: every experiment needs the
same assembly step (copy agent file → `main.py`, copy deck → `deck.csv`, copy
the vendored `cg/` folder), so that logic lives once in
`package_submission.py` instead of being re-implemented per experiment. The
agent files under `src/agents/` stay simple, portable, and swappable.

**Why `cg_bridge.py` exists at all**: the vendored SDK isn't `pip install`-able
— it's shipped inside the (gitignored, license-restricted) competition
dataset. Every module that needs the engine (`deck.py`, `arena.py`,
`evaluate_baseline.py`) imports through `cg_bridge` instead of hardcoding a
`sys.path.insert` of its own. Agent files under `src/agents/` are the
exception: they use `from cg.api import ...` directly, matching exactly what
a real Kaggle submission's `main.py` would do, because they need to work
standalone once copied out of this repo. `cg_bridge` inserting `SDK_DIR` onto
`sys.path` as a side effect is what makes that work in this repo's own
process too.

## Data flow: local self-play evaluation

```
data/decks/*.csv  ──┐
                    ├──> src/arena.py::play_n_matches
agents/*.py::agent ─┘         │
                               ▼
                        ArenaStats (wins/draws/aborted)
                               │
                 ┌─────────────┼─────────────────┐
                 ▼                                ▼
        src/evaluate.py                  src/evaluate_baseline.py
        (Wilson CI + a single             (per-match CSV rows +
         win-rate figure)                  loss-reason breakdown)
```

`arena.py::play_match` drives the engine directly (`cg.game.battle_start` /
`battle_select` / `battle_finish`), alternating which agent is "player 0" each
match to cancel first-move advantage. It has no knowledge of *why* a match was
won or lost beyond the engine's own `LogType.RESULT` reason code (prize race /
deck-out / no-Pokémon-in-play) — see `deck-out`, etc. in
[strategy.md](strategy.md) for what those reasons have meant in practice.

## Data flow: Kaggle submission

```
src/agents/<agent>.py  ──┐
data/decks/<deck>.csv  ──┼──> src/package_submission.py ──> submissions/<name>/
data/raw/.../cg/       ──┘         (copy, don't rewrite)     {main.py, deck.csv, cg/}
                                                                     │
                                                                     ▼
                                                          kaggle competitions submit
```

The packaged folder's shape is verified to match the official
`sample_submission/` layout. `.tar.gz` is the default archive format (see
`experiments/008-targz-packaging/`); `.zip` is kept as an option since early
experiments used it and it was never conclusively shown to matter.

## Testing strategy

`tests/` mirrors `src/` one-to-one. Every test that touches the `cg` engine
is marked with `conftest.py`'s `requires_sdk` (`pytest.mark.skipif(not
SDK_AVAILABLE, ...)`), so a fresh clone without the (gitignored, license-
restricted) competition data downloaded still gets a clean `pytest` run
instead of failing on missing files. Agent-logic regressions are caught two
ways:

1. **Structural tests** (e.g. `test_nonlethal_attack_scores_below_setup_actions`)
   assert invariants about the scoring constants directly — fast, no engine
   calls needed, and they fail loudly if a future edit reintroduces a bug
   this repo already paid to find and fix.
2. **Self-play regression** via `evaluate_baseline.py` (not part of `pytest`,
   run manually / from documented commands) — this is where actual agent
   *behavior* is checked, always against the previous best (frozen in
   `experiments/baseline_423/` and updated informally per experiment) rather
   than only against `random_agent`, because vs-random win rate has
   repeatedly proven to be a weak predictor of real strength (see
   [lessons_learned.md](../improvement/lessons_learned.md)).

## Branching model

Each experiment is a sibling branch off the strongest prior experiment's tip
(`exp/00N-description`), not a linear chain off `main` — `main` intentionally
stays at the initial scaffold commit until a change is confident enough to
promote (see the [experiments/ README](../experiments/README.md) and
[improvement/roadmap.md](../improvement/roadmap.md) for the current state of
that backlog).
