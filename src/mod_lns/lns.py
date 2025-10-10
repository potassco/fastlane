"""
A modifiable large neighborhood search framework.
"""

from argparse import Namespace
from typing import Optional

from mod_lns import Model
from mod_lns.interfaces.strategy import StrategyInterface
from mod_lns.lib.strategies.default_strategy import DefaultStrategy
from mod_lns.utils.logger import setup_logger


# pylint: disable=too-many-instance-attributes
class LNS:
    """
    Class handling and  performing LNS.

    :param files: Problem encodings.
    :type files: list[str]
    :param lns_config: LNSConfig object.
    :type lns_config: mod_lns.lns_config.LNSConfig
    :default lns_config: LNSConfig()
    """

    # pylint: disable=dangerous-default-value
    def __init__(
        self,
        files: list[str],
        strategy: StrategyInterface = DefaultStrategy(),
        args: dict[str, Any] = {},
    ):
        """
        Initialization of the lns object.
        """
        self.strategy: StrategyInterface = strategy
        self.strategy.parse_options(args)
        self.logger = setup_logger("LNS", strategy._log_level)
        self.strategy.init_logger(self.logger)
        self.logger.info("info")
        self.logger.warning("warning")
        self.logger.debug("debug")
        self.logger.error("error")

        self.files: list[str] = files
        
        self.step_c: int = 0

        self.new_model: Optional[Model] = None
        self.current_model: Model = Model()
        self.best_model: Model = Model()

    def main(self) -> None:
        """
        Run Large-Neighbourhood Search according to set parameters.
        """
        # c, b, n: current, best, new model
        # pre_setup()
        # solver_setup()
        # post_setup()
        # c = first_sol()
        # post_first_sol()
        # while check_stop()
        #   pre_relax()
        #   n = repair(relax(c))
        #   post_repair()
        #   check_accept(n)
        #       c = n
        #       accepted()
        #   check_better(n,b)
        #       b = n
        #       better()

        self.step_c = -1

        self.strategy.pre_setup(self)

        self.strategy.setup_solver(self)

        self.strategy.post_setup(self)

        self.step_c = 0

        # get first solution - to be reworked
        if not self.strategy.get_first_solution(
            self,
        ):
            self.logger.error("First solution could not be obtained")
            raise SystemExit

        self.strategy.post_first_solution(self)

        while not self.strategy.check_stop(self):
            self.step_c += 1

            self.strategy.pre_relax(self)

            fixed_atoms = []
            fixed_atoms = self.strategy.relax(self)

            self.new_model = self.strategy.repair(self, fixed_atoms)

            self.strategy.post_repair(self)

            if self.strategy.check_accept(self):
                assert isinstance(self.new_model, Model)
                self.current_model = self.new_model
                self.strategy.accepted(self)

            if self.strategy.check_better(self):
                assert isinstance(self.new_model, Model)
                self.best_model = self.new_model
                self.strategy.better(self)

            self.strategy.pre_next_iteration(self)

        self.strategy.print_result(self)
