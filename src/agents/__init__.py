"""
Agent policies: pure `Observation -> list[int]` decision functions.

Files in this package (other than __init__.py) must import only the standard
library plus `cg.api` / `cg.game` — never `from src... import` anything — because
src/package_submission.py copies them byte-for-byte into a submission's main.py,
which runs standalone with only the vendored `cg` package alongside it.
"""

from typing import Callable

AgentFn = Callable[[dict], list[int]]
