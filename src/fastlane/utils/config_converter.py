"""
Convert alaspo-style JSON configs into fastlane configuration format.
"""

import json
import sys
from argparse import ArgumentParser
from decimal import Decimal
from itertools import product
from pathlib import Path
from textwrap import dedent
from typing import Any

from clingo import Function, Number, String, Symbol, Tuple_, parse_term

from ..parsers.options_parser import formatter
from .types import SearchOperator


def warn(message: str) -> None:
    """
    Print a warning message to standard error.

    :param message: The warning message to print.
    """
    print(f"Warning: {message}", file=sys.stderr)


def valid_object(value: Any, context: str) -> dict[str, Any]:
    """
    Validate that the value is a JSON object.

    :param value: The value to validate.
    :param context: The context for error messages.
    :return: The validated JSON object.
    """
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be an object.")
    return value


def valid_name(value: Any, context: str) -> str:
    """
    Validate that the value is a nonempty string.

    :param value: The value to validate.
    :param context: The context for error messages.
    :return: The validated nonempty string.
    """
    if not isinstance(value, str) or not value:
        raise ValueError(f"{context} must be a nonempty string.")
    return value


def valid_array(value: Any, context: str) -> list[Any]:
    """
    Validate that the value is a nonempty array.

    :param value: The value to validate.
    :param context: The context for error messages.
    :return: The validated nonempty array.
    """
    if not isinstance(value, list) or not value:
        raise ValueError(f"{context} must be a nonempty array.")
    return value


def get_supported(data: dict[str, Any], *names: str) -> list[Any]:
    """
    Combine array-valued sections in alias order, warning about invalid sections.

    :param data: The JSON data to search.
    :param names: The section names to look for.
    :return: A list of supported entries.
    """
    entries: list[Any] = []
    for name in names:
        if name not in data:
            continue
        if not isinstance(data[name], list):
            warn(f"{name} must be an array; skipping it.")
            continue
        entries.extend(data[name])
    return entries


def _parse_destroy_sizes(sizes: Any) -> list[tuple[str, Symbol]]:
    """
    Convert a validated size array or ``"auto"`` into destruction specifications.

    Fractions must map exactly to whole percentages. Integers are absolute
    counts. Validate the entire entry before its caller emits any rules.
    """
    if sizes == "auto":
        return [("auto", Number(0))]

    specifications: list[tuple[str, Symbol]] = []
    for size in sizes:
        if isinstance(size, float):
            if not 0 <= size <= 1:
                raise ValueError("Float destroy sizes must be between 0 and 1.")
            percentage = Decimal(str(size)) * 100
            if percentage != percentage.to_integral_value():
                raise ValueError("Float destroy sizes must correspond to whole percentages.")
            specifications.append(("p", Number(int(percentage))))
        else:
            if size < 0:
                raise ValueError("Integer destroy sizes must be nonnegative.")
            specifications.append(("n", Number(size)))
    return specifications


def parse_destroy(candidates: list[Any], out_lines: list[str]) -> tuple[list[Symbol], dict[str, Any]]:
    """
    Append declarative destroy rules and collect random-atom search parameters.

    Invalid supported entries are warned about and skipped as a whole.

    :param candidates: The list of candidate destroy operators.
    :param out_lines: The list of output lines to append to.
    :return: A tuple containing the parsed destroy operators and required parameters.
    """
    # ordered sets
    operators: dict[Symbol, None] = {}
    search_parameters: dict[str, Any] = {}
    for candidate in candidates:
        if isinstance(candidate, dict) and candidate.get("type") not in ("randomAtoms", "declarative"):
            continue
        try:
            entry = valid_object(candidate, "destroyOperators entry")
            operator_type = entry["type"]
            name_text = valid_name(
                entry.get("name", "randomAtoms" if operator_type == "randomAtoms" else None), "destroyOperators.name"
            )
            name = parse_term(name_text)
            sizes = entry.get("sizes")
            if sizes != "auto":
                sizes = valid_array(sizes, "destroyOperators.sizes")
                if not (all(isinstance(size, float) for size in sizes) or all(isinstance(size, int) for size in sizes)):
                    raise ValueError("Destroy sizes must be either all floats or all integers.")
            if name_text == "randomAtoms":
                if sizes == "auto":
                    raise ValueError("Automatic sizes are not supported for randomAtoms.")
                search_parameters[name_text] = [int(size * 100) for size in sizes]
                continue
            specifications = _parse_destroy_sizes(sizes)
        except (ValueError, RuntimeError, TypeError, OverflowError) as error:
            warn(f"Failed to parse entry {candidate}: {error}")
            continue

        for size_type, value in specifications:
            operator = Tuple_([name, value])
            if operator in operators:
                warn(f"Duplicate destroy operator {operator}; skipped.")
                continue
            operators[operator] = None
            out_lines.append(f"_destroy_op({operator}, {size_type}({value})).")
    return list(operators), search_parameters


def _collect_search_parameters(entry: dict[str, Any], name: Symbol, parameters: dict[str, Any]) -> None:
    """
    Flatten nested search options into the shared parameter mapping.

    Invalid timeouts and unknown keys warn without discarding other options.
    """
    for key, value in entry.items():
        if key == "name":
            continue
        if key == "timeouts":
            try:
                timeouts = valid_array(value, f"{name}.timeouts")
                if any(
                    isinstance(timeout, bool) or not isinstance(timeout, int) or timeout < 0 for timeout in timeouts
                ):
                    raise ValueError("Timeouts must be nonnegative integers.")
                parameters["time-limit"] = timeouts
            except ValueError as error:
                warn(f"{error} Skipping timeouts for {name}.")
        elif isinstance(value, dict):
            _collect_search_parameters(value, name, parameters)
        # reuse the same allowed options as model parser
        # pylint: disable-next=protected-access
        elif key in SearchOperator._INTEGER_OPTIONS | SearchOperator._STRING_OPTIONS:
            parameters[key] = value
        else:
            warn(f"Unknown key {key} in search operator {name}.")


def parse_search(
    candidates: list[Any], add_params: dict[str, Any], out_lines: list[str]
) -> tuple[dict[Symbol, dict[Symbol, None]], dict[Symbol, tuple[Symbol, str]]]:
    """
    Parse search operators from the given candidates and append them to the output lines.

    :param candidates: The list of candidate search operators.
    :param add_params: Additional parameters to include.
    :param out_lines: The list of output lines to append to.
    :return: Ordered parameter operators by name, and auxiliary rules.
    """
    operators: dict[Symbol, dict[Symbol, None]] = {}
    parameters: dict[str, Any] = {}
    aux_rules: dict[Symbol, tuple[Symbol, str]] = {}
    for candidate_index, candidate in enumerate(candidates):
        try:
            entry = valid_object(candidate, "searchParams entry")
            name = String(valid_name(entry.get("name"), "searchParams.name"))
        except ValueError as error:
            warn(f"{error} Skipping search operator.")
            continue

        _collect_search_parameters(entry, name, parameters)
        parameters.update(add_params)

        for key, value in parameters.items():
            if key == "time-limit":
                operator = Tuple_([name, Function("T")])
                timeout_predicate = f"_times_{candidate_index}"
                timeout_rule_body = f"{timeout_predicate}(T)"
                aux_rules[name] = (operator, timeout_rule_body)
                out_lines.append(f"{timeout_predicate}({';'.join(str(timeout) for timeout in value)}).")
                out_lines.append(f'_search_param({operator}, ("time-limit", T)) :- {timeout_rule_body}.')
                continue
            if key == "randomAtoms":
                # not supported for now
                # out_lines.append(f"_rate({';'.join(str(rate) for rate in value)}).")
                # out_lines.append('_search_param(("destroy", R), ("relax-rate", R)) :- _rate(R).')
                continue

            parameter_value = Number(value) if isinstance(value, int) else String(value)
            operator = Tuple_([name, parameter_value])
            out_lines.append(f"_search_param({operator}, ({String(key)}, {parameter_value})).")

            named_operators = operators.setdefault(name, {})
            if operator in named_operators:
                warn(f"Duplicate search operator {operator}; skipped.")
                continue
            named_operators[operator] = None

    return operators, aux_rules


def convert(json_dict: dict[str, Any]) -> str:
    """
    Convert the given JSON dictionary into fastlane configuration format.

    :param json_dict: The JSON data to convert.
    :return: The converted output as a string.
    """
    output_lines: list[str] = []
    destroy_candidates = get_supported(json_dict, "destroyOperators", "relaxOperators")
    destroy_operators, additional_parameters = parse_destroy(destroy_candidates, output_lines)
    search_candidates = get_supported(json_dict, "searchOperators", "searchParams")
    search_operators, aux_rules = parse_search(search_candidates, additional_parameters, output_lines)
    for destroy_operator, search_name in product(destroy_operators, search_operators):
        search_parameters = ";".join(str(parameter) for parameter in search_operators[search_name])
        if aux_rule := aux_rules.get(search_name):
            timeout_operator, rule_body = aux_rule
            configuration = Tuple_([destroy_operator, timeout_operator])
            # Keep timeout and ordinary parameters in separate rules for the same configuration.
            output_lines.append(
                f"_config({configuration}, default, {destroy_operator}, default, ({timeout_operator})) :- {rule_body}."
            )
            output_lines.append(
                f"_config({configuration}, default, {destroy_operator}, default, ({search_parameters})) :- {rule_body}."
            )
        else:
            configuration = Tuple_([destroy_operator, search_name])
            output_lines.append(
                f"_config({configuration}, default, {destroy_operator}, default, ({search_parameters}))."
            )
    if "strategy" in json_dict:
        try:
            strategy = valid_object(json_dict["strategy"], "strategy")
            strategy_name = String(valid_name(strategy.get("name"), "strategy.name"))
            output_lines.append(f"_strategy({strategy_name}, C) :- _config(C, _, _, _, _).")
            output_lines.append(f"_strategy({strategy_name}, C) :- _config(C, _, _, _).")
        except ValueError as error:
            warn(f"{error} Skipping strategy.")
    return "\n".join(output_lines) + ("\n" if output_lines else "")


def main(argv: list[str] | None = None) -> None:
    """
    Read a JSON file and write fastlane rules to standard output.

    :param argv: Converter arguments, or None to read the process arguments.
    """
    parser = ArgumentParser(
        prog="fastlane-convert",
        description=dedent(
            "Convert alaspo-style JSON into fastlane configuration rules.\n"
            "Output can be redirected to a file using standard shell redirection,\n"
            "e.g.: fastlane-convert INPUT.json > OUTPUT.lp"
        ),
        formatter_class=formatter,
    )
    parser.add_argument("input", help="JSON file to be converted", type=Path)
    args = parser.parse_args(argv)

    with args.input.open(encoding="utf-8") as source:
        configuration = convert(json.load(source))
    sys.stdout.write(configuration)


if __name__ == "__main__":  # nocoverage
    main()
