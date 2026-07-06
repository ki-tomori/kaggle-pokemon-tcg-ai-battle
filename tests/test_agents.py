import pytest
from conftest import requires_sdk


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
