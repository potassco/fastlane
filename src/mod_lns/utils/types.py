"""
Additional types used in the LNS framework.
"""

from typing import Any, TypedDict


class ConfigCatalog(TypedDict, total=False):  # nocoverage
    """
    TypedDict for configuration catalog.

    :param project_operators: Project operator names mapped to projected predicate signatures.
    :param destroy_operators: Destroy operator names mapped to destruction parameters.
    :param prioritize_operators: Prioritize operator names mapped to heuristic value/modifier pairs.
    :param configs: Config names mapped to selected project/destroy/prioritize operators.
    :param strategy: Name of the adaptive strategy selected for configuration updates.
    """

    project_operators: dict[str, set[tuple[str, int]]]
    destroy_operators: dict[str, list[dict[str, Any]]]
    prioritize_operators: dict[str, dict[str, Any]]
    configs: dict[str, dict[str, list[str]]]
    strategy: str


class ActiveConfig(TypedDict, total=False):  # nocoverage
    """
    TypedDict for active configuration.

    :param name: Name of the active configuration.
    :param project_operators: List of project operators with their signatures.
    :param destroy_operators: List of destroy operators with their percentages or numbers.
    :param prioritize_operators: List of prioritize operators with their values and modifiers.
    :param config_repr: String representation of the active configuration.
    """

    name: str
    project_operators: list[dict[str, Any]]
    destroy_operators: list[dict[str, Any]]
    prioritize_operators: list[dict[str, Any]]
    config_repr: str
