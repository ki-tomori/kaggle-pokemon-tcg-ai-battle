# Experiment 012 — Gust/Tool/Damage Targeting (mixed result, honestly reported)

## Goal

Per Discussion thread 721338 (Boss's Orders / Ultra Ball usage advice) and
exp011's finding that `meta_v1`'s richer trainer package (Supporters, a Tool,
snipe-style attacks) exercises CARD selects the agent had never handled with
anything but a flat default score, add dedicated targeting logic for:

1. **Gust effects** (forcing one of the opponent's benched Pokémon active):
   prefer a target we can follow up on — low HP, still a Basic (deny future
   evolution), already energized (deny their investment), high retreat cost.
2. **Damage-target selection** (a card effect lets us choose which Pokémon
   takes damage): prefer the opponent's lowest-HP Pokémon.
3. **Attach targeting** (ported from experiment 004's validated logic, never
   previously in this agent): prefer powering up the active attacker.

Verified first that `option.playerIndex` reliably distinguishes "my own
bench" from "the opponent's bench" for these selects, by tracing real matches
with `meta_v1` and confirming card 1182 (one of the deck's 4 Supporters)
actually has switch/opponent/bench text — this card category is really in play,
not just theoretical.

## Result: damage-targeting was a clear regression, not an improvement

All three changes together: **42% head-to-head vs the pre-change agent**
(meta_v1 deck both sides, n=200) — a regression, not a gain. Isolating each:

| Heuristic (isolated) | vs pre-fix, n=150 | vs pre-fix, n=350 (revalidated) |
|---|---|---|
| Attach-targeting only | 46.0% | 51.1% |
| Gust-targeting only | 47.3% | 49.1% |
| Damage-targeting only | 39.3% | *(not revalidated — signal was already clear)* |

The n=150 reads for attach/gust looked like a real (if small) regression;
re-running at n=350 showed both are statistically indistinguishable from 50%
— **noise, not signal**, exactly the "hill-climbing below the noise floor"
trap flagged in Discussion thread 713608. Damage-targeting's negative signal
held up and was clearly the dominant cause of the combined regression.

**Damage-targeting was removed.** Preferring the opponent's lowest-HP Pokémon
as a snipe/damage target sounds reasonable but measurably hurt play in this
deck — possibly because the DAMAGE context here isn't cleanly "assign damage
to whoever's weakest" in every case this deck encounters, or because it
interacts badly with the deck's actual attack/effect set in a way this
project doesn't have full visibility into. Rather than keep a plausible-sounding
but empirically-negative heuristic, it was cut.

**Attach- and gust-targeting were kept**, since neither showed real harm at a
properly-sized sample, both are principled (attach-targeting specifically
was already validated positively on a different, simpler deck in experiment
004), and both replace an arbitrary "first in list" fallback with a reasoned
choice — but this experiment does **not** claim they're a proven win here;
they're neutral-to-plausible, not validated gains.

## Reconfirming the real lever: the deck, again

With this updated agent, `meta_v1` still clearly beats `optimized_v2` head to
head: **73.0%** (n=200), matching exp011's 72.0% finding with the pre-update
agent. vs random: 80.5%. The deck's strength is now confirmed across two
different agent versions — this is the strongest, most reliable signal in
the project, stronger than any single agent-logic tweak tried so far.

## Not submitted yet (this specific change)

The gust/attach targeting additions aren't a demonstrated win on their own,
so they don't meet the submission bar by themselves. However, the
**agent (exp010's sequencing fix + these neutral-but-harmless additions) +
`meta_v1` deck** combination is now validated twice at ~72-73% head-to-head
against the previous best submitted deck — a legitimate candidate for the
next submission, pending the user's go-ahead.

## Lessons

- Confirmed the Discussion's own eval-discipline warning firsthand: a 6-8pp
  gap at n=150 evaporated on revalidation at n=350. Any close result from now
  on should be revalidated at N≥300 before being trusted.
- Not every "sounds right" heuristic survives contact with the actual engine
  — damage-targeting was the most theoretically well-motivated of the three
  changes and the only one that clearly hurt.
