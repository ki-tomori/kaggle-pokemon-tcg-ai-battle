import pytest
from conftest import requires_sdk


@requires_sdk
def test_nonlethal_attack_scores_below_setup_actions():
    """heuristic_v2_agent should finish EVOLVE/ATTACH/PLAY/ABILITY this turn
    before taking a non-lethal ATTACK, since attacking ends the turn -- a MAIN
    select offering both isn't rare (measured ~45% of this agent's own MAIN
    decisions in self-play), so getting this ordering wrong is a real loss of
    free value, not just a theoretical edge case."""
    from cg.api import OptionType

    from agents.heuristic_v2_agent import _NONLETHAL_ATTACK_BASE, _NONLETHAL_ATTACK_DAMAGE_CAP, _PRIORITY

    max_nonlethal_attack_score = _NONLETHAL_ATTACK_BASE + _NONLETHAL_ATTACK_DAMAGE_CAP / 10.0
    for setup_type in (OptionType.EVOLVE, OptionType.ATTACH, OptionType.PLAY, OptionType.ABILITY):
        assert _PRIORITY[setup_type] > max_nonlethal_attack_score


@requires_sdk
@pytest.mark.parametrize(
    "agent_module", ["agents.random_agent", "agents.heuristic_agent", "agents.heuristic_v2_agent"]
)
def test_agent_returns_legal_selection(agent_module, sample_deck):
    import importlib

    from cg_bridge import battle_finish, battle_start

    agent_fn = importlib.import_module(agent_module).agent

    obs_dict, start_data = battle_start(sample_deck, sample_deck)
    assert obs_dict is not None, f"battle_start failed: {start_data.errorType}"
    try:
        selection = agent_fn(obs_dict)
        select = obs_dict["select"]
        assert isinstance(selection, list)
        assert select["minCount"] <= len(selection) <= select["maxCount"]
        assert len(set(selection)) == len(selection)
        assert all(0 <= i < len(select["option"]) for i in selection)
    finally:
        battle_finish()
