"""
A modifiable large neighborhood search framework.
"""

import random
import signal
import time
from types import FrameType
from typing import Union

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

    def __init__(
        self,
        files: list[str],
        strategy: StrategyInterface = DefaultStrategy(),
    ):
        """
        Initialization of the lns object.
        """

        self.logger = setup_logger("LNS", strategy.config.log_level)
        self.logger.info("info")
        self.logger.warning("warning")
        self.logger.debug("debug")
        self.logger.error("error")

        self.files: list[str] = files
        self.strategy: StrategyInterface = strategy
        self.strategy.init_logger(self.logger)
        self.start_time: float = 0
        self.step_c: int = 0
        self.finished = False

        self.seed = strategy.config.seed
        random.seed(self.seed)

        self.new_model: Model = Model()
        self.current_model: Model = Model()
        self.best_model: Model = Model()

        self.files: list[str] = files

        self.avail_time = self.strategy.config.time_limit

    # pylint: disable=unused-argument
    def interrupt_handler(self, sig: int, frame: Union[None, FrameType]) -> None:
        """
        Signal handler for interrupts (SIGINT, SIGTERM)

        :param sig: Signal number.
        :type sig: int
        :param frame: Current stack frame.
        :type frame: Frame
        :rtype: dict[str, Any]
        """
        print("==================")
        print("INTERRUPTED:")
        self.best_model.print_model()
        print(f"Overall steps: {self.step_c}")
        print(f"Overall time: {time.time() - self.start_time:.3f}s")
        raise SystemExit

    def get_available_solve_time(self, time_limit: int) -> int:
        """
        Calculate available solve time.
        (rounded to int)

        :param time_limit: Time limit for solve call.
        :type time_limit: int
        :return: Available solve time.
        :rtype: int
        """
        avail_time = self.avail_time
        if avail_time >= time_limit:
            return time_limit
        return avail_time

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

        signal.signal(signal.SIGINT, self.interrupt_handler)
        signal.signal(signal.SIGTERM, self.interrupt_handler)

        self.start_time = time.time()
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
        self.finished = self.strategy.solver.finished
        self.strategy.post_first_solution(self)

        while not (self.strategy.check_stop(self) or self.finished):
            self.step_c += 1
            # if self.step_c % 50 == 0:
            #     print(
            #         f"{time.time() - self.start_time:.3f}s: {self.step_c}|{self.param_values['max_steps']}"
            #     )
            print(f"Iteration: {self.step_c} || {self.best_model.get_cost_str()}")

            self.strategy.pre_relax(self)

            fixed_atoms = []
            fixed_atoms = self.strategy.relax(self)

            self.strategy.repair(self, fixed_atoms)

            self.strategy.post_repair(self)

            if self.strategy.check_accept(self):
                self.current_model = self.new_model
                self.strategy.accepted(self)

            if self.strategy.check_better(self):
                self.best_model = self.new_model
                print(
                    #  f'{time.time() - self.start_time:.3f}s: {self.step_c}|{self.param_values["max_steps"]} '
                    f"New best solution: {self.best_model.get_cost_str()}"
                )
                self.strategy.better(self)
        self.strategy.print_result(self)
