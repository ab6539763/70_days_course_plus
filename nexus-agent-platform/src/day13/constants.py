"""Day 13 常量"""

from __future__ import annotations

DEFAULT_RETRY_POLICY = {
    "max_attempts": 3,
    "base_delay": 0.1,
    "backoff_factor": 2.0,
}
