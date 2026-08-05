"""
Helper functions for output formatting and logging.
"""

from math import log10
from typing import Optional


def get_output_format(cost_str: str, time_limit: Optional[int], max_steps: Optional[int]) -> tuple[str, str]:
    """
    Get output format string for logging.

    :param cost_str: String representation of the cost.
    :param time_limit: Time limit in seconds (or None for unlimited).
    :param max_steps: Maximum number of steps (or None for unlimited).
    :return: Tuple containing header format and iteration format strings.
    """
    time_digits = 5 + 1 + 3  # 5 digits + dot + 3 digits
    step_digits = 7
    cost_digits = max(len(cost_str), 4)
    if time_limit is not None:
        time_digits = max(int(log10(time_limit)) + 1 + 1 + 3, time_digits)
    if max_steps is not None:
        step_digits = max(int(log10(max_steps)) + 1, step_digits)

    header = f"{{0:>{time_digits}}} - {{1:>{step_digits}}}: {{2:>{cost_digits}}}"
    iter_format = f"{{0:>{time_digits}.3f}} - {{1:>{step_digits}}}: {{2:>{cost_digits}}}"
    return header, iter_format
