"""
Search-based agent: for the main action choice, uses the engine's own
cg.api.search_begin/search_step hypothetical-search API to try each legal
option one ply deep and pick whichever leads to the best simple evaluation
(prize progress, then total HP differential), instead of only static
heuristics. Falls back to heuristic_v2's scoring whenever search isn't
available or raises for any reason — this agent must never crash.

Hidden information (our own remaining deck/prizes, the opponent's entire
deck/prize/hand) is genuinely unknown, so search_begin's required guesses are
best-effort: our own unseen cards are inferred from our known 60-card decklist
minus what we've directly observed in our hand/discard/play; the opponent's
unseen cards are guessed as a uniform sample over the whole card pool, which is
not informed by anything we've actually seen them play. This makes the search
a rough, not accurate, model of what could happen next — a stretch/experimental
measure, not a refined one.

Kaggle-portable: only stdlib + `cg.api` imports. This file is copied verbatim into
a submission's main.py by src/package_submission.py — do not import from `src`.
"""

import os

from cg.api import (
    CardType,
    Observation,
    Option,
    OptionType,
    SelectType,
    all_attack,
    all_card_data,
    search_begin,
    search_end,
    search_release,
    search_step,
    to_observation_class,
)

_ATTACKS = {atk.attackId: atk for atk in all_attack()}
_CARDS = {card.cardId: card for card in all_card_data()}
_ALL_CARD_IDS = list(_CARDS.keys())
_POKEMON_IDS = [cid for cid, card in _CARDS.items() if card.cardType == CardType.POKEMON]

_PRIORITY: dict[OptionType, float] = {
    OptionType.EVOLVE: 90,
    OptionType.ATTACH: 70,
    OptionType.PLAY: 65,
    OptionType.ABILITY: 55,
    OptionType.YES: 40,
    OptionType.NO: 30,
    OptionType.RETREAT: 5,
    OptionType.END: 0,
}
_DEFAULT_SCORE = 20.0
_LETHAL_BONUS = 1000.0

_my_deck_cache: list[int] | None = None


def _read_deck_csv() -> list[int]:
    """Read deck.csv. Returns a list of 60 card IDs in the deck; cached for search use."""
    global _my_deck_cache
    file_path = "deck.csv"
    if not os.path.exists(file_path):
        file_path = "/kaggle_simulations/agent/deck.csv"
    with open(file_path) as f:
        lines = f.read().splitlines()
    deck = [int(line) for line in lines[:60]]
    _my_deck_cache = deck
    return deck


def _opponent_active_hp(obs: Observation) -> int | None:
    state = obs.current
    opponent = state.players[1 - state.yourIndex]
    if not opponent.active or opponent.active[0] is None:
        return None
    return opponent.active[0].hp


def _attack_damage(option: Option, obs: Observation) -> int:
    attack = _ATTACKS.get(option.attackId)
    if attack is None:
        return 0
    damage = attack.damage
    state = obs.current
    my_active = state.players[state.yourIndex].active
    opp_active = state.players[1 - state.yourIndex].active
    if not my_active or my_active[0] is None or not opp_active or opp_active[0] is None:
        return damage
    my_card = _CARDS.get(my_active[0].id)
    opp_card = _CARDS.get(opp_active[0].id)
    if my_card is None or opp_card is None:
        return damage
    if opp_card.weakness is not None and opp_card.weakness == my_card.energyType:
        damage *= 2
    if opp_card.resistance is not None and opp_card.resistance == my_card.energyType:
        damage = max(0, damage - 20)
    return damage


def _heuristic_score(option: Option, obs: Observation) -> float:
    """Same shape as heuristic_v2_agent's scoring — the fallback when search isn't used."""
    if option.type == OptionType.ATTACK:
        damage = _attack_damage(option, obs)
        opp_hp = _opponent_active_hp(obs)
        if opp_hp is not None and damage >= opp_hp:
            return _LETHAL_BONUS + damage
        return 100.0 + damage
    return _PRIORITY.get(option.type, _DEFAULT_SCORE)


def _alive_pokemon(player_state) -> list:
    result = []
    if player_state.active and player_state.active[0] is not None:
        result.append(player_state.active[0])
    result += [p for p in player_state.bench if p is not None]
    return result


def _evaluate_state(state, your_index: int) -> float:
    """Simple static evaluation of a hypothetical future State: prize progress
    dominates, total remaining HP is the tiebreak."""
    if state is None:
        return 0.0
    if state.result != -1:
        if state.result == your_index:
            return 1e6
        if state.result == 1 - your_index:
            return -1e6
        return 0.0
    me = state.players[your_index]
    opp = state.players[1 - your_index]
    my_hp = sum(p.hp for p in _alive_pokemon(me))
    opp_hp = sum(p.hp for p in _alive_pokemon(opp))
    my_prizes_taken = 6 - len(me.prize)
    opp_prizes_taken = 6 - len(opp.prize)
    return (opp_prizes_taken - my_prizes_taken) * 1000.0 + (my_hp - opp_hp)


def _fill_to_length(pool: list[int], length: int) -> list[int]:
    if length <= 0:
        return []
    if not pool:
        return [_ALL_CARD_IDS[0]] * length
    reps = (length // len(pool)) + 1
    return (pool * reps)[:length]


def _predict_hidden_info(obs: Observation):
    """Best-effort guesses for search_begin's required hidden-information args.
    See module docstring: our own guess is grounded in our known decklist minus
    what we've seen; the opponent's guess is an uninformed uniform sample."""
    state = obs.current
    my_index = state.yourIndex
    me = state.players[my_index]
    opp = state.players[1 - my_index]

    seen_mine = []
    if me.hand:
        seen_mine += [c.id for c in me.hand]
    seen_mine += [c.id for c in me.discard]
    if me.active and me.active[0] is not None:
        seen_mine.append(me.active[0].id)
    seen_mine += [p.id for p in me.bench if p is not None]

    unseen = list(_my_deck_cache or [])
    for card_id in seen_mine:
        if card_id in unseen:
            unseen.remove(card_id)

    needed_deck = me.deckCount
    needed_prize = len(me.prize)
    unseen = _fill_to_length(unseen, needed_deck + needed_prize)
    your_deck = unseen[:needed_deck]
    your_prize = unseen[needed_deck : needed_deck + needed_prize]

    opponent_deck = _fill_to_length(_ALL_CARD_IDS, opp.deckCount)
    opponent_prize = _fill_to_length(_ALL_CARD_IDS, len(opp.prize))
    opponent_hand = _fill_to_length(_ALL_CARD_IDS, opp.handCount)
    opponent_active: list[int] = []
    if opp.active and len(opp.active) > 0 and opp.active[0] is None and _POKEMON_IDS:
        opponent_active = [_POKEMON_IDS[0]]

    return your_deck, your_prize, opponent_deck, opponent_prize, opponent_hand, opponent_active


def _search_rank_options(obs: Observation) -> list[int] | None:
    """Rank every option in obs.select by a 1-ply search_step lookahead. Returns
    None (caller should fall back to heuristic scoring) if search isn't usable."""
    if obs.search_begin_input is None:
        return None
    your_deck, your_prize, opp_deck, opp_prize, opp_hand, opp_active = _predict_hidden_info(obs)
    root = search_begin(obs, your_deck, your_prize, opp_deck, opp_prize, opp_hand, opp_active)

    scores: list[tuple[float, int]] = []
    try:
        for i in range(len(obs.select.option)):
            try:
                child = search_step(root.searchId, [i])
            except Exception:
                scores.append((-1e9, i))
                continue
            score = _evaluate_state(child.observation.current, obs.current.yourIndex)
            scores.append((score, i))
            try:
                search_release(child.searchId)
            except Exception:
                pass
    finally:
        try:
            search_end()
        except Exception:
            pass

    scores.sort(key=lambda pair: pair[0], reverse=True)
    return [i for _, i in scores]


def agent(obs_dict: dict) -> list[int]:
    """Implement a Pokémon TCG agent that ranks MAIN-menu options via a 1-ply
    search_step lookahead when possible, falling back to static heuristic
    scoring (identical to heuristic_v2_agent) otherwise. Never raises.
    """
    obs: Observation = to_observation_class(obs_dict)
    if obs.select is None:
        return _read_deck_csv()

    select = obs.select
    k = max(select.minCount, min(select.maxCount, 1))

    if select.type == SelectType.MAIN and len(select.option) > 1:
        try:
            ranked = _search_rank_options(obs)
        except Exception:
            ranked = None
        if ranked is not None:
            return ranked[:k]

    ranked = sorted(
        range(len(select.option)), key=lambda i: _heuristic_score(select.option[i], obs), reverse=True
    )
    return ranked[:k]
