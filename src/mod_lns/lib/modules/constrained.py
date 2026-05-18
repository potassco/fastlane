


def get_opt_bound(cost: list[int]) -> str:
        """
        Calculate bound for next step.

        :param cost: Current cost list
        :type cost: list[int]
        :return: String representing the bound for the next step.
        :rtype: str
        """
        bound = cost[:-1] + [cost[-1] - 1]
        return "opt, " + ", ".join([str(c) for c in bound])