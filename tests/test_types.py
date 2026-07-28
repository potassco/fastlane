"""
Test cases for the types module.
"""

from unittest import TestCase

from mod_lns.utils.types import ProjectOperator

# pylint: disable=protected-access


class TestProjectOperator(TestCase):
    """
    Test cases for the ProjectOperator class.
    """

    def setUp(self):
        self.name = "test_operator"
        self.signatures = [("arg1", 1), ("arg2", 2)]
        self.project_operator = ProjectOperator(self.name)

    def test_init(self):
        """
        Test the initialization of the ProjectOperator class.
        """
        self.assertEqual(self.project_operator.name, self.name)

    def test_from_signatures(self):
        """
        Test the from_signatures class method of the ProjectOperator class.
        """
        project_operator = ProjectOperator.from_signatures(self.name, set(self.signatures))
        self.assertEqual(project_operator.name, self.name)
        self.assertSetEqual(project_operator._signatures, set(self.signatures))

    def test_add(self):
        """
        Test the add method of the ProjectOperator class.
        """
        for signature in self.signatures:
            self.project_operator.add(signature)
        self.assertSetEqual(self.project_operator._signatures, set(self.signatures))

    def test_helper(self):
        """
        Test the helper methods of the ProjectOperator class.
        """
        self.test_add()
        # __iter__
        for signature in self.project_operator:
            self.assertIn(signature, self.signatures)
        # __contains__
        for signature in self.signatures:
            self.assertIn(signature, self.project_operator)
        # __len__
        self.assertEqual(len(self.project_operator), len(self.signatures))

        with self.assertRaises(TypeError):
            _ = self.project_operator == "not_a_project_operator"

        self.assertFalse(self.project_operator == ProjectOperator("different_operator"))
        self.assertTrue(self.project_operator == ProjectOperator.from_signatures(self.name, set(self.signatures)))

    def test_validate(self):
        """
        Test the _validate method of the ProjectOperator class.
        """
        valid_signature = ("valid", 1)
        self.assertEqual(self.project_operator._validate(valid_signature), valid_signature)

        with self.assertRaises(TypeError):
            self.project_operator._validate(("invalid", "not_an_int"))

        with self.assertRaises(TypeError):
            self.project_operator._validate((5, 1))

        with self.assertRaises(TypeError):
            self.project_operator._validate(("too", "big", "tuple"))

        with self.assertRaises(TypeError):
            self.project_operator._validate("not_a_tuple")
