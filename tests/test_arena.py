from agents.random_agent import agent as random_agent
from arena import play_match, play_n_matches
from conftest import requires_sdk


@requires_sdk
def test_play_match_completes(sample_deck):
    result = play_match(random_agent, random_agent, sample_deck, sample_deck, max_actions=500)
    assert result.winner in (0, 1, 2, -1)
    assert result.n_actions > 0


@requires_sdk
def test_play_n_matches_totals(sample_deck):
    stats = play_n_matches(random_agent, random_agent, sample_deck, sample_deck, n=3, seed=1)
    assert stats.n_matches == 3
