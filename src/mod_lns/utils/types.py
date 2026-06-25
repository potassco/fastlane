"""
Additional types used in the LNS framework.
"""

from typing import Any, TypedDict


class ConfigCatalog(TypedDict, total=False):
    """
    TypedDict for configuration catalog.

    :param project_operators: Project operator names mapped to projected predicate signatures.
    :type project_operators: dict[str, set[tuple[str, int]]]
    :param destroy_operators: Destroy operator names mapped to destruction parameters.
    :type destroy_operators: dict[str, list[dict[str, Any]]]
    :param prioritized_operators: Prioritize operator names mapped to heuristic value/modifier pairs.
    :type prioritized_operators: dict[str, dict[str, Any]]
    :param configs: Config names mapped to selected project/destroy/prioritize operators.
    :type configs: dict[str, dict[str, list[str]]]
    :param strategy: Name of the adaptive strategy selected for configuration updates.
    :type strategy: str
    """

    project_operators: dict[str, set[tuple[str, int]]]
    destroy_operators: dict[str, list[dict[str, Any]]]
    prioritize_operators: dict[str, dict[str, Any]]
    configs: dict[str, dict[str, list[str]]]
    strategy: str


class ActiveConfig(TypedDict, total=False):
    """
    TypedDict for active configuration.

    :param name: Name of the active configuration.
    :type name: str
    :param project_operators: List of project operators with their signatures.
    :type project_operators: list[dict[str, Any]]
    :param destroy_operators: List of destroy operators with their percentages or numbers.
    :type destroy_operators: list[dict[str, Any]]
    :param prioritize_operators: List of prioritize operators with their values and modifiers.
    :type prioritize_operators: list[dict[str, Any]]
    :param config_repr: String representation of the active configuration.
    :type config_repr: str
    """

    name: str
    project_operators: list[dict[str, Any]]
    destroy_operators: list[dict[str, Any]]
    prioritize_operators: list[dict[str, Any]]
    config_repr: str
