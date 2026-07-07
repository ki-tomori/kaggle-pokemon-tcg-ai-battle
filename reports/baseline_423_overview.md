# baseline_423 — Current Code Overview

This documents the state of the repo as recorded for **baseline_423**: the
`exp002-heuristic-v2` submission (`agents.heuristic_v2_agent` + the mono-Fire
deck `data/decks/optimized_v2.csv`), which is the best-scoring submission so
far and the reference point for future improvement work. See
`experiments/baseline_423/manifest.yaml` for the frozen, reproducible record.

No agent logic is changed by this document or by the evaluation harness it
describes — this is a survey + tooling pass only.

## 1. Current code structure

```
src/
├── config.py               # paths, constants (SEED, DECK_SIZE, ...)
├── cg_bridge.py             # sys.path bridge to the vendored `cg` SDK; check_sdk_available()
├── deck.py                  # deck construction + legality validation
├── agents/
│   ├── heuristic_agent.py       # v1 (exp001): fixed action-type priority only
│   ├── heuristic_v2_agent.py    # v2 (exp002): + lethal detection + damage scoring — THE BASELINE
│   └── random_agent.py          # legal-random baseline opponent
├── arena.py                 # local self-play match runner + win-rate stats
├── evaluate.py               # Wilson-CI win-rate summary + plotting
└── package_submission.py     # assembles a Kaggle submission folder from an agent file + deck
```

`tests/` holds pytest coverage for all of the above (legality, agent-returns-legal-move,
arena smoke tests). `experiments/NNN-.../` and `reports/NNN_*.md` hold the
history of prior experiments (001: original baseline heuristic, 002: this
deck+agent combo, 003–005: three alternative measures tried after 002, not yet
known which — if any — beat 002 on the real ladder).

## 2. Roles of `agent.py` / `submission.py` in this repo's terms

The competition's own vocabulary (`agent.py`, `submission.py`) doesn't map
1:1 onto file names here, since this repo separates "agent logic" from
"packaging" for reuse across experiments. The mapping:

| Competition concept | This repo's file | Role |
|---|---|---|
| `agent.py` (the `agent(obs_dict) -> list[int]` function Kaggle calls) | `src/agents/heuristic_v2_agent.py` | The actual decision logic. Kaggle-portable: only stdlib + `cg.api` imports, never `from src... import`, because... |
| `submission.py` / the zip you upload | produced by `src/package_submission.py` | ...this script copies the agent file **verbatim** into `submissions/<name>/main.py`, alongside `deck.csv` and a copy of the vendored `cg/` SDK folder, matching the official `sample_submission/` shape. It doesn't contain any logic of its own beyond file assembly — no agent code lives in `package_submission.py`. |

So: **edit `heuristic_v2_agent.py` to change behavior; run `package_submission.py`
to produce something uploadable.** The two are intentionally decoupled so the
same packaging script works for every agent variant (v1, v2, v3, search_agent, ...)
without duplicating that logic per experiment.

## 3. Current action-selection logic (`heuristic_v2_agent.py`)

The agent has **no lookahead** — it scores every legal option in the current
`obs.select.option` list with a static function and picks the top-ranked one(s).

**Deck request** (`obs.select is None`, the very first call): return the 60
card IDs from `deck.csv` (checked at `./deck.csv`, falling back to
`/kaggle_simulations/agent/deck.csv` under Kaggle's runtime).

**Every other call** — score each option, then take the top
`k = clamp(1, minCount, maxCount)` options:

| Option type | Score | Why |
|---|---|---|
| `ATTACK` | `1000 + damage` if the attack would knock out the opponent's active Pokémon (damage ≥ its current HP); else `100 + damage` | Lethal attacks always outrank everything else; otherwise prefer whichever attack does the most damage |
| `EVOLVE` | 90 | Second priority — developing the board |
| `ATTACH` | 70 | Attach energy — no target selection logic (any legal ATTACH scores the same regardless of which Pokémon it goes to) |
| `PLAY` | 65 | Play a card from hand |
| `ABILITY` | 55 | Use an ability |
| `YES` | 40 | Always accept optional effects |
| `NO` | 30 | |
| `RETREAT` | 5 | Deprioritized — no logic for *when* retreating is good (e.g. escaping a bad matchup) |
| `END` | 0 | Last resort |
| anything else (CARD/ENERGY/NUMBER/SPECIAL_CONDITION/... in non-MAIN selections) | 20 (flat default) | No target-selection logic at all for these — ties are broken by whichever option happened to come first in the engine's list |

**Damage estimate** (`_attack_damage`): looks up the attack's base damage, then
applies a crude type adjustment using the *active* Pokémon on each side only
(no bench/pre-evolution consideration): weakness doubles damage, resistance
subtracts a flat 20. This is the full extent of "board awareness" — the agent
does not reason about prizes remaining, future turns, hand contents beyond
what's immediately playable, or the opponent's likely deck.

**Known gaps** (candidates for the improvement work this harness supports,
not touched yet): no retreat timing, no energy-attach targeting, no evaluation
of non-MAIN selections (switch-in choice, discard choice, etc. all fall back
to "first option"), no card-draw/resource planning beyond what's already in
the deck's card mix.
