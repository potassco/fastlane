"""
Additional types used in the LNS framework.
"""

from dataclasses import dataclass, field
from typing import Any, Iterable, Iterator, TypeAlias, TypedDict

PredicateSignature: TypeAlias = tuple[str, int]  # (predicate_name, arity)


@dataclass
class ProjectOperator:
    """
    Validated container of predicate signatures: (predicate_name, arity).
    Behaves like a set for iteration, membership, and length.
    Additional attribute for operator name.

    :param name: Name of the project operator.
    :ivar _signatures: Set of predicate signatures.
    """

    name: str
    _signatures: set[PredicateSignature] = field(default_factory=set, init=False)

    def __iter__(self) -> Iterator[PredicateSignature]:
        return iter(self._signatures)

    def __contains__(self, item: object) -> bool:
        return item in self._signatures

    def __len__(self) -> int:
        return len(self._signatures)

    def add(self, item: PredicateSignature) -> None:
        """
        Add a predicate signature to the project operator.

        :param item: Predicate signature to add.
        """
        self._signatures.add(self._validate(item))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ProjectOperator):
            raise TypeError(f"Cannot compare ProjectOperator with {type(other).__name__}")
        return self.name == other.name and self._signatures == other._signatures

    @staticmethod
    def _validate(item: tuple[str, int]) -> PredicateSignature:
        if not isinstance(item, tuple) or len(item) != 2:
            raise TypeError("Expected tuple[str, int].")
        name, arity = item
        if not isinstance(name, str):
            raise TypeError(f"predicate name must be str, got {type(name).__name__}")
        if not isinstance(arity, int):
            raise TypeError(f"arity must be int, got {type(arity).__name__}")
        return name, arity

    @classmethod
    def from_signatures(cls, name: str, signatures: Iterable[PredicateSignature]) -> "ProjectOperator":
        """
        Create a ProjectOperator instance from a set of predicate signatures.

        :param name: Name of the project operator.
        :param signatures: Iterable of predicate signatures.
        :return: ProjectOperator instance.
        """
        op = cls(name)
        for sig in signatures:
            op.add(sig)
        return op


class ConfigCatalog(TypedDict, total=False):  # nocoverage
    """
    TypedDict for configuration catalog.

    :ivar project_operators: Project operator names mapped to projected predicate signatures.
    :ivar destroy_operators: Destroy operator names mapped to destruction parameters.
    :ivar prioritize_operators: Prioritize operator names mapped to heuristic value/modifier pairs.
    :ivar configs: Config names mapped to selected project/destroy/prioritize operators.
    :ivar strategy: Name of the adaptive strategy selected for configuration updates.
    """

    project_operators: dict[str, ProjectOperator]
    destroy_operators: dict[str, list[dict[str, Any]]]
    prioritize_operators: dict[str, dict[str, Any]]
    configs: dict[str, dict[str, list[str]]]
    strategy: str


class ActiveConfig(TypedDict, total=False):  # nocoverage
    """
    TypedDict for active configuration.

    :ivar name: Name of the active configuration.
    :ivar project_operators: List of project operators with their signatures.
    :ivar destroy_operators: List of destroy operators with their percentages or numbers.
    :ivar prioritize_operators: List of prioritize operators with their values and modifiers.
    :ivar config_repr: String representation of the active configuration.
    """

    name: str
    project_operators: list[ProjectOperator]
    destroy_operators: list[dict[str, Any]]
    prioritize_operators: list[dict[str, Any]]
    config_repr: str
