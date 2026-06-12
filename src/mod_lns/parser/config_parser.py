from typing import TYPE_CHECKING, Any, Optional

from clingo import SymbolicAtoms
from clingo.symbol import Symbol, SymbolType, Tuple_

from mod_lns import Model
from mod_lns.interfaces.solver import Solver

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage


class ConfigParser:
    """
    Parser for extracting and validating configuration from model.
    """

    @staticmethod
    def _is_atom(term: Symbol) -> bool:
        """
        Check if given term is atom.

        :param term: Term.
        :type term: Symbol
        :return: True if given term is atom, False otherwise.
        :rtype: bool
        """
        return term.type == SymbolType.Function and term.name

    # TODO
    # project operator can not be created through _project/2
    # @classmethod
    # def _get_project_operators_and_signatures_from_project2(cls, model: Model) -> tuple[set[str], list[dict[str, Any]]]:
    #     """
    #     Extract and validate project operator names and predicate signatures of projected atoms from atoms of _project/2 in model.

    #     :param model: Model object.
    #     :type model: Model
    #     :return: Set of project operator names and list of predicate names and arities of projected atoms.
    #     :rtype: tuple[set[str], list[dict[str, Any]]]
    #     """
    #     project_operators = set()
    #     projected_signatures = []

    #     for atom in model.true:
    #         if atom.match("_project", 2):
    #             project_operators.add(str(atom.arguments[0]))
    #             second_arg = atom.arguments[1]
    #             if cls._is_atom(second_arg):
    #                 projected_signature = {"name": second_arg.name, "arity": len(second_arg.arguments)}
    #             else:
    #                 #logger.warning(f"_project/2: Second argument {second_arg} is not an atom. (atom: {atom})")
    #                 continue
    #             if projected_signature not in projected_signatures:
    #                 projected_signatures.append(projected_signature)

    #     return project_operators, projected_signatures

    @classmethod
    def _parse_project_operator(cls, solver: Solver, declarative: bool) -> dict[str, set[tuple[str, int]]]:
        """
        Extract project operator names and predicate signatures of projected atoms from model.

        :param solver: Solver interface object.
        :type solver: SolverInterface
        :return: Dictionary of project operator names and their corresponding signatures.
        :rtype: dict[str, set[tuple[str, int]]]]
        """
        project_operators: dict[str, set[tuple[str, int]]] = {}

        if declarative:
            for atom in solver.control.symbolic_atoms.by_signature("_project_op", 2):
                args = atom.symbol.arguments
                if args[0].type != SymbolType.String:
                    operator = str(args[0])
                else:
                    operator = args[0].string
                project_operators.setdefault(operator, set())
                if args[1].type == SymbolType.Function and len(args[1].arguments) == 2:
                    signature = args[1].arguments
                    # TODO catch bad args
                    # project_operators[operator].add({"name": signature[0].name, "arity": signature[1].number})
                    project_operators[operator].add((signature[0].name, signature[1].number))
                else:
                    # logger.warning(f"_project/2: Second argument {args[1]} is not a valid signature.")
                    continue

            # TODO
            # from specifications
            # for atom in solver.control.symbolic_atoms.by_signature("_project", 2):
            #     args = atom.symbol.arguments
            #     operator = str(args[0])
            #     if operator not in project_operators:
            #         project_operators.setdefault(operator, set())
            #         if cls._is_atom(args[1]):
            #             project_operators[operator].add({"name": args[1].name, "arity": len(args[1].arguments)})
            #         else:
            #             #logger.warning(f"_project/2: Second argument {args[1]} is not a valid signature.")
            #             continue

        # no operators defined -> default to all shown
        if not project_operators:
            project_operators.setdefault("default", set())
            for atom in solver.last_model.shown:
                if cls._is_atom(atom):
                    project_operators["default"].add((atom.name, len(atom.arguments)))
                else:
                    continue
            # default empty -> exception

        return project_operators

    @staticmethod
    def _is_percent_or_number(term: Symbol) -> bool:
        """
        Check if given term is atom representing percent or number.

        :param term: Term.
        :type term: Symbol
        :return: True if given term is atom representing percent or number, False otherwise.
        :rtype: bool
        """
        return (term.match("p", 1) or term.match("n", 1)) and term.arguments[0].type == SymbolType.Number

    @classmethod
    def _parse_destroy_operators(cls, solver: Solver, declarative: bool) -> dict[str, list[dict[str, Any]]]:
        """
        Extract and validate destroy operators from atoms of _destroy/2 in model.

        :param solver: Solver interface object.
        :type solver: SolverInterface
        :return: Dictionary mapping destroy operator names to lists of percentages or numbers.
        :rtype: dict[str, list[dict[str, Any]]]
        """
        destroy_operators: dict[str, list[dict[str, Any]]] = {}

        if declarative:
            for atom in solver.control.symbolic_atoms.by_signature("_destroy_op", 2):
                args = atom.symbol.arguments
                if args[0].type != SymbolType.String:
                    operator = str(args[0])
                else:
                    operator = args[0].string
                if operator in destroy_operators:
                    # logger.warning(f"_destroy/2: Multiple definitions of destroy operator {operator}. Ignoring {atom}.")
                    continue
                destroy_operators.setdefault(operator, [{"type": "auto", "value": None}])
                parameter = args[1]
                if parameter.type == SymbolType.Function:
                    percents_or_numbers = []
                    if parameter.name:
                        if parameter.match("auto", 0):
                            # default
                            # percents_or_numbers = [{"type": "auto", "value": None}]
                            continue
                        elif cls._is_percent_or_number(parameter):
                            percents_or_numbers = [{"type": parameter.name, "value": parameter.arguments[0].number}]
                        else:
                            # logger.warning(f"_destroy/2: Second argument {second_arg} is invalid. (atom: {atom})")
                            continue
                    else:
                        for arg in parameter.arguments:
                            if cls._is_percent_or_number(arg):
                                percents_or_numbers.append({"type": arg.name, "value": arg.arguments[0].number})
                            else:
                                # logger.warning(f"_destroy/2: Second argument {second_arg} is invalid. (atom: {atom})")
                                break
                        # ?? TODO check arg missmatch
                        # _destroy_op("random_n", (p(10),p(20))).
                        # _destroy("random_n", plays(P,W,G), P,W,G) :- plays(P,W,G).
                        # --
                        # _destroy_op("random_n", (p(10),p(20))).
                        # _destroy("random_n", plays(P,W,G), W) :- plays(P,W,G).
                        if len(percents_or_numbers) < len(parameter.arguments):
                            continue
                else:
                    # logger.warning(f"_destroy/2: Second argument {second_arg} is invalid. (atom: {atom})")
                    continue

                destroy_operators[operator] = percents_or_numbers

        if not destroy_operators:
            destroy_operators["default"] = [{"type": "auto", "value": None}]

        return destroy_operators

    # TODO
    # destroy op can not be created through _destroy/3
    # @classmethod
    # def _get_destroy_operators_from_destroy3(cls, model: Model) -> dict[str, list[list[dict[str, Any]]]]:
    #     """
    #     Extract and validate destroy operators from atoms of _destroy/3 in model.

    #     :param model: Model object.
    #     :type model: Model
    #     :return: Dictionary mapping destroy operator names to default percentage.
    #     :rtype: dict[str, list[list[dict[str, Any]]]]
    #     """
    #     destroy_operators = {}

    #     for atom in model.true:
    #         if atom.match("_destroy", 3):
    #             name = str(atom.arguments[0])
    #             if name not in destroy_operators:
    #                 destroy_operators[name] = [[{"type": "auto", "value": None}]]

    #             second_arg = atom.arguments[1]
    #             if not cls._is_atom(second_arg):
    #                 #logger.warning(f"_destroy/3: Second argument {second_arg} is not an atom. (atom: {atom})")
    #                 pass
    #     return destroy_operators

    @staticmethod
    def _is_heuristic_modifier(term: Symbol) -> bool:
        """
        Check if given term is modifier used in #heuristic statements.

        :param term: Term.
        :type term: Symbol
        :return: True if given term is heuristic modifier, False otherwise.
        :rtype: bool
        """
        return (
            term.match("sign", 0)
            or term.match("level", 0)
            or term.match("true", 0)
            or term.match("false", 0)
            or term.match("init", 0)
            or term.match("factor", 0)
        )

    @classmethod
    def _parse_prioritize_operators(cls, solver: Solver, declarative: bool) -> dict[str, dict[str, Any]]:
        """
        Extract and validate prioritize operators from atoms of _prioritize/3 in model.

        :param solver: SolverInterface object.
        :type solver: SolverInterface
        :return: Dictionary mapping prioritize operator names to dictionaries of heuristic modifiers and their values.
        :rtype: dict[str, dict[str, Any]]
        """
        prioritize_operators: dict[str, dict[str, Any]] = {}

        if declarative:
            for atom in solver.control.symbolic_atoms.by_signature("_prioritize_op", 3):
                args = atom.symbol.arguments
                if args[0].type != SymbolType.String:
                    operator = str(args[0])
                else:
                    operator = args[0].string
                if operator in prioritize_operators:
                    # logger.warning(f"_prioritize/3: Multiple definitions of prioritize operator {operator}. Ignoring {atom}.")
                    continue
                prioritize_operators.setdefault(operator, {"value": 1, "modifier": "true"})

                value_param = args[1]
                if value_param.match("inf", 0):
                    value = "inf"
                elif value_param.type == SymbolType.Number:
                    value = value_param.number
                else:
                    # logger.warning(f"_prioritize/3: Second argument {value_param} is neither an integer nor inf. (atom: {atom})")
                    continue

                modifier_param = args[2]
                if cls._is_heuristic_modifier(modifier_param):
                    prioritize_operators[operator] = {"value": value, "modifier": modifier_param.name}
                else:
                    # logger.warning(f"_prioritize/3: Third argument {modifier_param} is not one of: sign, level, true, false, init, factor. (atom: {atom})")
                    continue

        if not prioritize_operators:
            prioritize_operators["default"] = {"value": 1, "modifier": "true"}

        return prioritize_operators

    # TODO
    # prioritize op can not be created through _prioritize/2
    # @classmethod
    # def _get_prioritize_operators_from_prioritize2(cls, model: Model) -> dict[str, list[dict[str, Any]]]:
    #     """
    #     Extract and validate prioritize operators from atoms of _prioritize/2 in model.

    #     :param model: Model object.
    #     :type model: Model
    #     :return: Dictionary mapping prioritize operator names to default heuristic modifier and its value.
    #     :rtype: dict[str, list[dict[str, Any]]]
    #     """
    #     prioritize_operators = {}

    #     for atom in model.true:
    #         if atom.match("_prioritize", 2):
    #             name = str(atom.arguments[0])
    #             if name not in prioritize_operators:
    #                 prioritize_operators[name] = [{"value": 1, "modifier": "true"}]

    #             second_arg = atom.arguments[1]
    #             if not cls._is_atom(second_arg):
    #                 #logger.warning(f"_prioritize/2: Second argument {second_arg} is not an atom. (atom: {atom})")
    #                 pass

    #     return prioritize_operators

    @classmethod
    def _parse_configs(
        cls,
        solver: Solver,
        defined_project_operators: list[str],
        defined_destroy_operators: list[str],
        defined_prioritize_operators: list[str],
        declarative: bool,
    ) -> dict[str, dict[str, list[str]]]:
        """
        Extract and validate configurations from atoms of _config/4.

        :param solver: SolverInterface object.
        :type solver: SolverInterface
        :param defined_project_operators: List of available project operator names.
        :type defined_project_operators: list[str]
        :param defined_destroy_operators: List of available destroy operator names.
        :type defined_destroy_operators: list[str]
        :param defined_prioritize_operators: List of available prioritize operator names.
        :type defined_prioritize_operators: list[str]
        :return: Dictionary mapping configuration names to lists of operator names.
        :rtype: dict[str, dict[str, list[str]]]
        """
        configs: dict[str, dict[str, set[str]]] = {}
        defined_operators = {
            "project_operators": set(defined_project_operators),
            "destroy_operators": set(defined_destroy_operators),
            "prioritize_operators": set(defined_prioritize_operators),
        }
        operator_args_info = [
            {"index": 1, "key": "project_operators", "type": "Project"},
            {"index": 2, "key": "destroy_operators", "type": "Destroy"},
            {"index": 3, "key": "prioritize_operators", "type": "Prioritize"},
        ]

        if declarative:
            for atom in solver.control.symbolic_atoms.by_signature("_config", 4):
                args = atom.symbol.arguments
                if args[0].type != SymbolType.String:
                    config_name = str(args[0])
                else:
                    config_name = args[0].string
                configs.setdefault(
                    config_name, {"project_operators": set(), "destroy_operators": set(), "prioritize_operators": set()}
                )

                # TODO support for multi ops required? _config("Random", "plays_3", ("random_n";"random_40"), "1_true").
                for info in operator_args_info:
                    key = info["key"]
                    operator_atom = args[info["index"]]
                    if operator_atom.type != SymbolType.String:
                        operator_name = str(operator_atom)
                    else:
                        operator_name = operator_atom.string
                    if operator_name in defined_operators[key]:
                        configs[config_name][key].add(operator_name)
                    else:
                        raise RuntimeError(
                            f"_config/4: {info['type']} operator {operator_name} is not defined. (atom: {atom})"
                        )

        if not configs:
            configs["default"] = defined_operators

        # TODO why sort?
        sorted_configs = {
            config_name: {key: sorted(operator_names) for key, operator_names in operators.items()}
            for config_name, operators in configs.items()
        }

        return sorted_configs

    @classmethod
    def _parse_strategy(
        cls,
        solver: Solver,
        defined_configs: dict[str, dict[str, list[str]]],
        supported_strategies: list[str],
        default_strategy: str,
        declarative: bool,
    ) -> tuple[str, dict[str, dict[str, list[str]]]]:
        """
        Extract and validate strategy and configurations subject to selection from atoms of _strategy/2.

        :param solver: SolverInterface object.
        :type solver: SolverInterface
        :param defined_configs: Dictionary mapping names of available configurations to lists of operator names.
        :type defined_configs: dict[str, dict[str, list[str]]]
        :param supported_strategies: List of available strategy names.
        :type supported_strategies: list[str]
        :param default_strategy: Name of strategy to use when not specified.
        :type default_strategy: str
        :return: Strategy name and Dictionary mapping names of configurations subject to selection to lists of operator names.
        :rtype: tuple[str, dict[str, dict[str, list[str]]]]
        """
        strategy: Optional[str] = None
        candidate_configs = {}

        if declarative:
            for atom in solver.control.symbolic_atoms.by_signature("_strategy", 2):
                args = atom.symbol.arguments
                if args[0].type != SymbolType.String:
                    strategy_name = str(args[0])
                else:
                    strategy_name = args[0].string
                if strategy_name not in supported_strategies:
                    # logger.warning(f"_strategy/2: Strategy {strategy_name} is not supported. (atom: {atom})")
                    continue

                if strategy is not None:
                    # logger.warning(f"_strategy/2: Multiple strategies specified. Using {strategy} and ignoring {strategy_name}. (atom: {atom})")
                    break
                strategy = strategy_name

                config_name = str(args[1])
                if config_name in defined_configs:
                    candidate_configs[config_name] = defined_configs[config_name]
                else:
                    # logger.warning(f"_strategy/2: Config {config_name} is not defined. (atom: {atom})")
                    continue

        if not candidate_configs:
            # TODO maybe deep copy needed
            candidate_configs = defined_configs.copy()
        if strategy is None:
            strategy = default_strategy

        return strategy, candidate_configs

    # TODO update docstrings
    @classmethod
    def parse_lns_config(cls, lns_object: "LNS") -> dict[str, Any]:
        """
        Extract and validate LNS configuration from model.

        LNS configuration includes project operator names, predicate signatures of projected atoms,
        destroy operator definitions, prioritize operator definitions,
        configuration definitions and strategy name.

        :param solver: Solver interface object.
        :type solver: SolverInterface
        :param supported_strategies: List of available strategy names.
        :type supported_strategies: list[str]
        :param default_strategy: Name of strategy to use when not specified.
        :type default_strategy: str
        :return: LNS configuration dictionary with the following keys:
            - "project_operators" (set[str]): Set of project operator names.
            - "projected_signatures" (list[dict[str, Any]]): List of dictionaries with the following keys:
                - "name" (str): Predicate name of projected atom.
                - "arity" (int): Arity of projected atom.
            - "destroy_operators" (dict[str, list[list[dict[str, Any]]]]): Dictionary mapping destroy operator names to nested lists of dictionaries with the following keys:a
                - "type" (str): Type of percentage or number ("p", "n", or "auto").
                - "value" (int | None): Value of percentage or number.
            - "prioritize_operators" (dict[str, list[dict[str, Any]]]): Dictionary mapping prioritize operator names to lists of dictionaries with the following keys:
                - "value" (int | str): Value of heuristic modifier (integer or "inf").
                - "modifier" (str): Heuristic modifier ("sign", "level", "true", "false", "init", or "factor").
            - "configs" (dict[str, dict[str, list[str]]]): Dictionary mapping configuration names to dictionaries with the following keys:
                - "project_operators" (list[str]): List of project operator names.
                - "destroy_operators" (list[str]): List of destroy operator names.
                - "prioritize_operators" (list[str]): List of prioritize operator names.
            - "strategy" (str): Strategy name
        :rtype: dict[str, Any]
        """
        solver = lns_object.solver
        config = lns_object.options
        declarative = config.declarative
        project_operators = cls._parse_project_operator(solver, declarative)
        destroy_operators = cls._parse_destroy_operators(solver, declarative)
        if not declarative:
            if config.relax_rate > 0:
                dest_op = [{"type": "p", "value": config.relax_rate}]
            else:
                dest_op = [{"type": "auto", "value": None}]
            destroy_operators = {"default": dest_op}

        prioritize_operators = cls._parse_prioritize_operators(solver, declarative)
        config_catalog = {
            "project_operators": project_operators,
            "destroy_operators": destroy_operators,
            "prioritize_operators": prioritize_operators,
        }

        defined_configs = cls._parse_configs(
            solver,
            list(project_operators.keys()),
            list(destroy_operators.keys()),
            list(prioritize_operators.keys()),
            declarative,
        )
        strategy, candidate_configs = cls._parse_strategy(
            solver,
            defined_configs,
            config.get_supported_adaptive_strategy_names(),
            config.default_adaptive_strategy_name,
            declarative,
        )
        config_catalog["configs"] = candidate_configs
        config_catalog["strategy"] = strategy
        lns_object.logger.debug("LNS configuration: %s", cls._format_lns_config(config_catalog))
        return config_catalog

    @classmethod
    def _format_lns_config(cls, config_catalog: dict[str, Any]) -> str:
        """
        Convert LNS configuration into string.

        :param config_catalog: LNS configuration.
        :type config_catalog: dict[str, Any]
        :return: String representing LNS configuration.
        :rtype: str
        """
        project_operators = ",".join(
            name + "{" + ",".join(f"{signature[0]}/{signature[1]}" for signature in signatures) + "}"
            for name, signatures in config_catalog["project_operators"].items()
        )

        destroy_operators = ",".join(
            name
            + "{"
            + ",".join(
                f"{pn['type']}({pn['value']})" if pn["value"] is not None else pn["type"]
                for pn in percents_or_numbers_list
            )
            + "}"
            for name, percents_or_numbers_list in config_catalog["destroy_operators"].items()
        )

        prioritize_operators = ",".join(
            name + "{" + f"{modifiers_and_values['value']},{modifiers_and_values['modifier']}" + "}"
            for name, modifiers_and_values in config_catalog["prioritize_operators"].items()
        )

        out = f"project_operators={{{project_operators}}}, destroy_operators={{{destroy_operators}}}, prioritize_operators={{{prioritize_operators}}}"

        if "configs" in config_catalog:
            configs = ",".join(
                config
                + "["
                + "project_operators={"
                + ",".join(operators["project_operators"])
                + "},destroy_operators={"
                + ",".join(operators["destroy_operators"])
                + "},prioritize_operators={"
                + ",".join(operators["prioritize_operators"])
                + "}"
                + "]"
                for config, operators in config_catalog["configs"].items()
            )
            out += f", configs={{{configs}}}"

        if "strategy" in config_catalog:
            strategy = config_catalog["strategy"]
            out += f", strategy={strategy}"

        return out

    @classmethod
    def get_op_specs(cls, model: Model) -> dict[str, set[Symbol]]:
        """
        Extract operation specifications from the model.

        :param model: Model containing the atoms.
        :type model: Model
        :return: Dictionary mapping operation names to sets of symbols.
        :rtype: dict[str, set[Symbol]]
        """
        specs: dict[str, set[Symbol]] = {}
        for atom in model.true:
            if atom.match("_project", 2):
                specs.setdefault("_project", set()).add(atom)
            elif atom.match("_destroy", 3):
                specs.setdefault("_destroy", set()).add(atom)
            elif atom.match("_prioritize", 2):
                specs.setdefault("_prioritize", set()).add(atom)
        return specs

    @classmethod
    def get_projected_atoms(
        cls, model: Model, op_specs: dict[str, set[Symbol]], project_operator_name: str
    ) -> set[Symbol]:
        """
        Extract subset of atoms included in answer set from atoms of _project/2.

        :param model: Model containing the atoms.
        :type model: Model
        :param op_specs: Operation specifications.
        :type op_specs: dict[str, set[Symbol]]
        :param project_operator_name: Project operator name.
        :type project_operator_name: str
        :return: Projected atoms.
        :rtype: set[Symbol]
        """
        projected_atoms = set()
        is_project2_defined = False

        for atom in op_specs.get("_project", set()):
            args = atom.arguments
            if args[0].type != SymbolType.String:
                operator_name = str(args[0])
            else:
                operator_name = args[0].string
            if operator_name == project_operator_name:
                is_project2_defined = True
                second_arg = args[1]
                if cls._is_atom(second_arg) and second_arg in model.shown:
                    projected_atoms.add(second_arg)

        # default project all shown
        if not is_project2_defined:
            for atom in model.shown:
                if cls._is_atom(atom):
                    projected_atoms.add(atom)

        return projected_atoms

    @classmethod
    def get_atom_term_pairs(
        cls, op_specs: dict[str, set[Symbol]], projected_atoms: set[Symbol], destroy_operator_name: str
    ) -> list[dict[str, Symbol]]:
        """
        Extract atoms subject to destruction and corresponding terms from atoms of _destroy/3.

        :param op_specs: Operation specifications.
        :type op_specs: dict[str, set[Symbol]]
        :param projected_atoms: Projected atoms.
        :type projected_atoms: set[Symbol]
        :param destroy_operator_name: Destroy operator name.
        :type destroy_operator_name: str
        :return: Atoms subject to destruction and corresponding terms.
        :rtype: list[dict[str, Symbol]]
        """
        atom_term_pairs: list[dict[str, Symbol]] = []
        is_destroy3_defined = False

        for atom in op_specs.get("_destroy", set()):
            args = atom.arguments
            if args[0].type != SymbolType.String:
                operator_name = str(args[0])
            else:
                operator_name = args[0].string
            if operator_name == destroy_operator_name:
                is_destroy3_defined = True
                candidate_atom = args[1]
                if candidate_atom in projected_atoms:
                    atom_term_pairs.append({"atom": candidate_atom, "term": args[2]})

        # default destroy all projected
        if not is_destroy3_defined:
            for atom in projected_atoms:
                atom_term_pairs.append({"atom": atom, "term": Tuple_(atom.arguments)})

        return atom_term_pairs

    @classmethod
    def get_destruction_candidate_atoms(
        cls, op_specs: dict[str, set[Symbol]], projected_atoms: set[Symbol], destroy_operator_name: str
    ) -> set[Symbol]:
        """
        Extract atoms subject to destruction from atoms of _destroy/3.

        :param op_specs: Operation specifications.
        :type op_specs: dict[str, set[Symbol]]
        :param projected_atoms: Projected atoms.
        :type projected_atoms: set[Symbol]
        :param destroy_operator_name: Destroy operator name.
        :type destroy_operator_name: str
        :return: Atoms subject to destruction.
        :rtype: set[Symbol]
        """
        atom_term_pairs = cls.get_atom_term_pairs(op_specs, projected_atoms, destroy_operator_name)
        return set(pair["atom"] for pair in atom_term_pairs)

    @classmethod
    def get_heuristic_targets(
        cls,
        op_specs: dict[str, set[Symbol]],
        undestroyed_atoms: set[Symbol],
        prioritize_operator_name: str,
    ) -> set[Symbol]:
        """
        Extract atoms subject to prioritization from atoms of _prioritize/2.

        :param op_specs: Operation specifications.
        :type op_specs: dict[str, set[Symbol]]
        :param undestroyed_atoms: Undestroyed atoms.
        :type undestroyed_atoms: set[Symbol]
        :param prioritize_operator_name: Prioritize operator name.
        :type prioritize_operator_name: str
        :return: Atoms subject to prioritization.
        :rtype: set[Symbol]
        """
        heuristic_targets: set[Symbol] = set()
        is_prioritize2_defined = False

        for atom in op_specs.get("_prioritize", set()):
            args = atom.arguments
            if args[0].type != SymbolType.String:
                operator_name = str(args[0])
            else:
                operator_name = args[0].string
            if operator_name == prioritize_operator_name:
                is_prioritize2_defined = True
                candidate_atom = args[1]
                if candidate_atom in undestroyed_atoms:
                    heuristic_targets.add(candidate_atom)

        # default prioritize all undestroyed
        if not is_prioritize2_defined:
            heuristic_targets = undestroyed_atoms.copy()

        return heuristic_targets
