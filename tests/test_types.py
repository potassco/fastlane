"""
Test cases for the types module.
"""

from unittest import TestCase

from fastlane.utils.types import DestroyOperator, PrioritizeOperator, ProjectOperator

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

        # __eq__
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


class TestDestroyOperator(TestCase):
    """
    Test cases for the DestroyOperator class.
    """

    def setUp(self):
        self.name = "test_operator"
        self.specs = [{"type": "p", "value": 20}, {"type": "n", "value": 5}, {"type": "auto", "value": None}]
        self.destroy_operator = DestroyOperator(self.name)

    def test_init(self):
        """
        Test the initialization of the DestroyOperator class.
        """
        self.assertEqual(self.destroy_operator.name, self.name)

    def test_from_specs(self):
        """
        Test the from_specs class method of the DestroyOperator class.
        """
        destroy_operator = DestroyOperator.from_specs(self.name, self.specs)
        self.assertEqual(destroy_operator.name, self.name)
        self.assertListEqual(destroy_operator._destruction_specs, self.specs)

    def test_append(self):
        """
        Test the append method of the DestroyOperator class.
        """
        for spec in self.specs:
            self.destroy_operator.append(spec)
        self.assertListEqual(self.destroy_operator._destruction_specs, self.specs)

    def test_get_first_spec(self):
        """
        Test the get_first_spec method of the DestroyOperator class.
        """
        self.destroy_operator.append(self.specs[0])
        self.assertEqual(self.destroy_operator.get_first_spec(), self.specs[0])

        with self.assertRaises(ValueError):
            empty_destroy_operator = DestroyOperator("empty_operator")
            empty_destroy_operator.get_first_spec()

    def test_get_all_specs(self):
        """
        Test the get_all_specs method of the DestroyOperator class.
        """
        for spec in self.specs:
            self.destroy_operator.append(spec)
        self.assertListEqual(self.destroy_operator.get_all_specs(), self.specs)

    def test_helper(self):
        """
        Test the helper methods of the DestroyOperator class.
        """
        self.test_append()
        # __iter__
        for spec in self.destroy_operator:
            self.assertIn(spec, self.specs)
        # __contains__
        for spec in self.specs:
            self.assertIn(spec, self.destroy_operator)
        # __len__
        self.assertEqual(len(self.destroy_operator), len(self.specs))

        # __eq__
        with self.assertRaises(TypeError):
            _ = self.destroy_operator == "not_a_destroy_operator"
        self.assertFalse(self.destroy_operator == DestroyOperator("different_operator"))
        self.assertTrue(self.destroy_operator == DestroyOperator.from_specs(self.name, self.specs))

        # __get_item__
        self.assertEqual(self.destroy_operator[0], self.specs[0])

        # __set_item__
        new_spec = {"type": "p", "value": 50}
        self.destroy_operator[0] = new_spec
        self.assertEqual(self.destroy_operator[0], new_spec)

    def test_validate(self):
        """
        Test the _validate method of the DestroyOperator class.
        """
        valid_specs = [
            {"type": "p", "value": 20},
            {"type": "n", "value": 5},
            {"type": "auto", "value": None},
        ]
        for spec in valid_specs:
            self.assertEqual(self.destroy_operator._validate(spec), spec)

        invalid_specs = [
            "not-dict",
            {"wrong_key": "value"},
            {"type": "p", "value": "not_a_number"},
            {"type": "n", "value": 5.5},
            {"type": "auto", "value": 10},
            {"type": "invalid_type", "value": 10},
        ]
        for spec in invalid_specs:
            with self.assertRaises(TypeError):
                self.destroy_operator._validate(spec)


class TestPrioritizeOperator(TestCase):
    """
    Test cases for the PrioritizeOperator class.
    """

    def setUp(self):
        self.name = "test_operator"
        self.spec = {"value": 1, "modifier": "true"}
        self.prioritize_operator = PrioritizeOperator(self.name)

    def test_init(self):
        """
        Test the initialization of the PrioritizeOperator class.
        """
        self.assertEqual(self.prioritize_operator.name, self.name)

    def test_from_spec(self):
        """
        Test the from_spec class method of the PrioritizeOperator class.
        """
        prioritize_operator = PrioritizeOperator.from_spec(self.name, self.spec)
        self.assertEqual(prioritize_operator.name, self.name)
        self.assertDictEqual(prioritize_operator._prioritization_spec, self.spec)

    def test_set_spec(self):
        """
        Test the set_spec method of the PrioritizeOperator class.
        """
        self.prioritize_operator.set_spec(self.spec)
        self.assertDictEqual(self.prioritize_operator._prioritization_spec, self.spec)

    def test_get_spec(self):
        """
        Test the get_spec method of the PrioritizeOperator class.
        """
        with self.assertRaises(ValueError):
            self.prioritize_operator.get_spec()

        self.test_set_spec()
        self.assertDictEqual(self.prioritize_operator.get_spec(), self.spec)

    def test_helper(self):
        """
        Test the helper methods of the PrioritizeOperator class.
        """
        self.test_set_spec()
        # __iter__
        for key in self.prioritize_operator:
            self.assertIn(key, self.spec)
        for key, value in self.prioritize_operator.items():
            self.assertIn(key, self.spec)
            self.assertEqual(value, self.spec[key])
        for key in self.prioritize_operator.keys():
            self.assertIn(key, self.spec)
        for value in self.prioritize_operator.values():
            self.assertIn(value, self.spec.values())
        # __len__
        self.assertEqual(len(self.prioritize_operator), len(self.spec))
        # __contains__
        for key in self.spec:
            self.assertIn(key, self.prioritize_operator)
        # __getitem__
        for key, value in self.spec.items():
            self.assertEqual(self.prioritize_operator[key], value)
        # __setitem__
        new_spec = {"value": 2, "modifier": "false"}
        self.prioritize_operator["value"] = 2
        self.prioritize_operator["modifier"] = "false"
        self.assertDictEqual(self.prioritize_operator._prioritization_spec, new_spec)
        # __delitem__
        with self.assertRaises(TypeError):
            self.test_set_spec()
            del self.prioritize_operator["value"]

    def test_validate(self):
        """
        Test the _validate method of the PrioritizeOperator class.
        """
        valid_spec = {"value": 1, "modifier": "true"}
        self.assertEqual(self.prioritize_operator._validate(valid_spec), valid_spec)

        invalid_specs = [
            "not-dict",
            {"wrong_key": "value"},
            {"value": "not_a_number", "modifier": "true"},
            {"value": 1, "modifier": 5},
            {"value": 1, "modifier": "invalid_modifier"},
        ]
        for spec in invalid_specs:
            with self.assertRaises(TypeError):
                self.prioritize_operator._validate(spec)
