"""
Helper Model class.
"""


class Model:
    "Simplified Model class"

    def __init__(self):
        self.shown = []
        self.true = []
        self.cost = []
        self.assignments = []
        self.opt = False

    def get_cost_str(self) -> str:
        """
        Get cost of model as string.
        :return: Cost as string.
        :rtype: str
        """
        cost = self.cost
        if len(cost) != 0:
            return " ".join([str(c) for c in cost])
        return ""

    def print_model(self) -> str:
        """
        Print model.

        :return: Printed string.
        :rtype: str
        """
        answer_string = " ".join([str(atom) for atom in self.shown])
        if len(self.assignments) != 0:
            answer_string += "\nAssignments:\n" + " ".join(self.assignments)
        s = "Answer\n" f"{answer_string}\n" f"Cost: {self.get_cost_str()}\n"
        print(s)
        return s
