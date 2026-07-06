from cg_bridge import check_sdk_available


def test_check_sdk_available_returns_bool():
    """Importing cg_bridge must never raise, even on a fresh clone without data/."""
    assert isinstance(check_sdk_available(), bool)
