"""
Additional types used in the LNS framework.
"""

from dataclasses import dataclass, field
from typing import Any, Iterable, Iterator, Literal, TypeAlias, TypedDict

PredicateSignature: TypeAlias = tuple[str, int]  # (predicate_name, arity)

DestructionSpec: TypeAlias = dict[
    Literal["type", "value"], Any
]  # {"type": Literal["auto", "p", "n"], "value": None | int | float}


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

    def add(self, item: tuple[str, int]) -> None:
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


@dataclass
class DestroyOperator:
    """
    Container for destroy operator specifications.
    Behaves like a list for iteration, membership, length and assignments.
    Additional attribute for operator name.

    :param name: Name of the destroy operator.
    :ivar _destruction_specs: List of destruction specifications.
    """

    name: str
    _destruction_specs: list[DestructionSpec] = field(default_factory=list, init=False)

    def __iter__(self) -> Iterator[DestructionSpec]:
        return iter(self._destruction_specs)

    def __contains__(self, item: object) -> bool:
        return item in self._destruction_specs

    def __len__(self) -> int:
        return len(self._destruction_specs)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DestroyOperator):
            raise TypeError(f"Cannot compare DestroyOperator with {type(other).__name__}")
        return self.name == other.name and self._destruction_specs == other._destruction_specs

    def __getitem__(self, index: int) -> DestructionSpec:
        return self._destruction_specs[index]

    @staticmethod
    def _validate(item: dict[str, Any]) -> DestructionSpec:
        if not isinstance(item, dict):
            raise TypeError(f"Expected destruction spec dict, got {type(item).__name__}")

        required_keys = {"type", "value"}
        if set(item.keys()) != required_keys:
            raise TypeError("Destruction spec must have exactly keys: {'type', 'value'}.")

        spec_type = item["type"]
        value = item["value"]

        if spec_type == "auto":
            if value is not None:
                raise TypeError("spec 'value' must be None when type is 'auto'.")
            return {"type": "auto", "value": None}
        if spec_type == "p":
            if not isinstance(value, int) and not isinstance(value, float):
                raise TypeError(f"spec 'value' must be int or float when type is 'p', got {type(value).__name__}")
            return {"type": "p", "value": value}
        if spec_type == "n":
            if not isinstance(value, int):
                raise TypeError(f"spec 'value' must be int when type is 'n', got {type(value).__name__}")
            return {"type": "n", "value": value}
        raise TypeError(f"spec 'type' must be one of: 'auto', 'p', 'n'. Got {spec_type!r}")

    def __setitem__(self, index: int, item: dict[str, Any]) -> None:
        self._destruction_specs[index] = self._validate(item)

    def append(self, item: dict[str, Any]) -> None:
        """
        Append a destruction specification to the destroy operator.

        :param item: Destruction specification to add.
        """
        self._destruction_specs.append(self._validate(item))

    @classmethod
    def from_specs(cls, name: str, specs: Iterable[dict[str, Any]]) -> "DestroyOperator":
        """
        Create a DestroyOperator instance from a set of destruction specifications.

        :param name: Name of the destroy operator.
        :param specs: Iterable of destruction specifications.
        :return: DestroyOperator instance.
        """
        op = cls(name)
        for spec in specs:
            op.append(spec)
        return op

    def get_first_spec(self) -> DestructionSpec:
        """
        Get the first destruction specification.

        :return: First destruction specification.
        """
        if not self._destruction_specs:
            raise ValueError("DestroyOperator has no destruction specifications.")
        return self._destruction_specs[0]

    def get_all_specs(self) -> list[DestructionSpec]:
        """
        Get all destruction specifications.

        :return: List of all destruction specifications.
        """
        return self._destruction_specs


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
    destroy_operators: dict[str, DestroyOperator]
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
    destroy_operators: list[DestroyOperator]
    prioritize_operators: list[dict[str, Any]]
    config_repr: str
