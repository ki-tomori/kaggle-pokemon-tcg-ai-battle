import csv

from conftest import requires_sdk
from evaluate_baseline import run_evaluation, write_eval_results, write_loss_cases, write_loss_summary

_FAKE_ROWS = [
    {
        "match_id": 0,
        "agent_module": "agents.heuristic_v2_agent",
        "opponent_module": "agents.random_agent",
        "agent_went_first": True,
        "outcome": "win",
        "winner_index": 0,
        "agent_index": 0,
        "reason": 1,
        "n_actions": 50,
        "aborted": False,
    },
    {
        "match_id": 1,
        "agent_module": "agents.heuristic_v2_agent",
        "opponent_module": "agents.random_agent",
        "agent_went_first": False,
        "outcome": "loss",
        "winner_index": 0,
        "agent_index": 1,
        "reason": 2,
        "n_actions": 200,
        "aborted": False,
    },
]


def test_write_eval_results(tmp_path):
    path = tmp_path / "eval_results.csv"
    write_eval_results(_FAKE_ROWS, path)
    with open(path) as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2


def test_write_loss_cases(tmp_path):
    path = tmp_path / "loss_cases.csv"
    losses = write_loss_cases(_FAKE_ROWS, path)
    assert len(losses) == 1
    with open(path) as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["outcome"] == "loss"


def test_write_loss_summary(tmp_path):
    path = tmp_path / "loss_summary.md"
    losses = [r for r in _FAKE_ROWS if r["outcome"] == "loss"]
    write_loss_summary(_FAKE_ROWS, losses, path)
    text = path.read_text()
    assert "Win rate: 0.500" in text
    assert "deck_out" in text


@requires_sdk
def test_run_evaluation_smoke():
    rows = run_evaluation(n_matches=2, seed=1)
    assert len(rows) == 2
    assert all(r["outcome"] in ("win", "loss", "draw", "aborted") for r in rows)
