"""
Test cases for the average auto-destruction converter.
"""

from unittest import TestCase, mock

from clingo.symbol import Function

from mod_lns import Model
from mod_lns.lib.auto_destruction_converters.average import AverageDestructionConverter, _RunningAverage
from mod_lns.utils.types import ProjectOperator

# pylint: disable=protected-access


class TestRunningAverage(TestCase):
    """
    Test cases for the _RunningAverage class.
    """

    def setUp(self) -> None:
        """
        Set up the test case.
        """
        self.running_average = _RunningAverage()

    def test_init(self) -> None:
        """
        Test the initialization of _RunningAverage.
        """
        self.assertEqual(self.running_average.total, 0.0)
        self.assertEqual(self.running_average.count, 0)

    def test_add(self) -> None:
        """
        Test the add methods of _RunningAverage.
        """
        values = [10, 20, 30]
        for value in values:
            self.running_average.add(value)

        self.assertEqual(self.running_average.total, 60.0)
        self.assertEqual(self.running_average.count, 3)

    def test_mean(self) -> None:
        """
        Test the mean method when no values have been added.
        """
        default_value = 5.0
        self.assertEqual(self.running_average.mean(default_value), default_value)
        self.test_add()
        self.assertEqual(self.running_average.mean(0.0), 20.0)


class TestAverageDestructionConverter(TestCase):
    """
    Test cases for the AverageDestructionConverter class.
    """

    def setUp(self) -> None:
        """
        Set up the test case.
        """
        self.converter = AverageDestructionConverter(auto_init_percent=10)

    def test_init(self) -> None:
        """
        Test the initialization of AverageDestructionConverter.
        """
        self.assertEqual(AverageDestructionConverter()._auto_init_percent, 0)
        self.assertEqual(self.converter._auto_init_percent, 10)
        self.assertDictEqual(self.converter._project_operator_names, {})
        self.assertDictEqual(self.converter._running_averages, {})

    def test_compute_actual_destruction_percent(self) -> None:
        """
        Test the _compute_actual_destruction_percent method.
        """
        current_model = mock.Mock()
        new_model = mock.Mock()
        project_operator_names = ["op1", "op2"]
        destroy_operator_name = "destroy_op"
        projected_atoms = [{Function("atom1")}, {Function("atom2")}]
        destruction_candidate_atoms = {Function("atom3"), Function("atom4")}

        with (
            mock.patch(
                "mod_lns.lib.auto_destruction_converters.average.ConfigParser.get_projected_atoms",
                side_effect=projected_atoms,
            ) as mock_get_projected_atoms,
            mock.patch(
                "mod_lns.lib.auto_destruction_converters.average.ConfigParser.get_destruction_candidate_atoms",
                return_value=destruction_candidate_atoms,
            ) as mock_get_destruction_candidate_atoms,
            mock.patch(
                "mod_lns.lib.auto_destruction_converters.average.calculate_actual_destruction_percent",
                return_value=50.0,
            ) as mock_calculate_actual_destruction_percent,
        ):
            self.assertEqual(
                self.converter._compute_actual_destruction_percent(
                    project_operator_names, destroy_operator_name, current_model, new_model
                ),
                50.0,
            )
            self.assertEqual(mock_get_projected_atoms.call_count, len(project_operator_names))
            mock_get_destruction_candidate_atoms.assert_called_once_with(
                current_model, {Function("atom1"), Function("atom2")}, destroy_operator_name
            )
            mock_calculate_actual_destruction_percent.assert_called_once_with(destruction_candidate_atoms, new_model)

    def test_running_averages(self) -> None:
        """
        Test the _register_key and _update_running_averages method.
        """
        key = ("config1", "destroy_op")
        current_model = mock.Mock()
        new_model = mock.Mock()
        self.converter._improvement_models = [(current_model, new_model)]

        with mock.patch.object(
            self.converter, "_compute_actual_destruction_percent", return_value=10.0
        ) as mock_compute_actual_destruction_percent:
            self.converter._register_key(key, ["op1", "op2"])
            mock_compute_actual_destruction_percent.assert_called_once_with(
                ["op1", "op2"], "destroy_op", current_model, new_model
            )
            self.assertDictEqual(self.converter._project_operator_names, {key: ["op1", "op2"]})
            self.assertTrue(key in self.converter._running_averages)
            self.assertIsInstance(self.converter._running_averages[key], _RunningAverage)
            self.assertEqual(self.converter._running_averages[key].total, 10.0)

        with mock.patch.object(
            self.converter, "_compute_actual_destruction_percent", return_value=20.0
        ) as mock_compute_actual_destruction_percent:
            self.converter._update_running_averages(current_model, new_model)
            mock_compute_actual_destruction_percent.assert_called_once_with(
                ["op1", "op2"], "destroy_op", current_model, new_model
            )
            self.assertTrue(key in self.converter._running_averages)
            self.assertIsInstance(self.converter._running_averages[key], _RunningAverage)
            self.assertEqual(self.converter._running_averages[key].total, 30.0)

    def test_convert_auto_in_config(self):
        """
        Test convert_auto_in_config method.
        """
        config = {}
        lns_object = mock.Mock()
        lns_object.current_model = mock.Mock(spec=Model)
        lns_object.new_model = mock.Mock(spec=Model)

        with (
            mock.patch(
                "mod_lns.lib.auto_destruction_converters.average.is_new_model_better", return_value=True
            ) as mock_is_new_model_better,
            mock.patch.object(self.converter, "_update_running_averages") as mock_update_running_averages,
            mock.patch(
                "mod_lns.lib.auto_destruction_converters.average.AutoDestructionConverter.convert_auto_in_config"
            ) as mock_super_convert,
        ):
            self.converter.convert_auto_in_config(config, lns_object)
            self.assertListEqual(self.converter._improvement_models, [(lns_object.current_model, lns_object.new_model)])
            mock_update_running_averages.assert_called_once_with(lns_object.current_model, lns_object.new_model)
            mock_super_convert.assert_called_once_with(config, lns_object)

            mock_is_new_model_better.return_value = False
            self.converter.convert_auto_in_config(config, lns_object)
            self.assertEqual(mock_update_running_averages.call_count, 1)
            self.assertEqual(mock_super_convert.call_count, 2)

            mock_is_new_model_better.return_value = True
            lns_object.new_model = None
            self.converter.convert_auto_in_config(config, lns_object)
            self.assertEqual(mock_update_running_averages.call_count, 1)
            self.assertEqual(mock_super_convert.call_count, 3)

            self.converter.convert_auto_in_config(config)
            self.assertEqual(mock_update_running_averages.call_count, 1)
            self.assertEqual(mock_super_convert.call_count, 4)

    def test_compute_auto_destruction_percent(self):
        """
        Test compute_auto_destruction_percent method.
        """
        config_name = "config1"
        project_operators = [ProjectOperator(name="op1"), ProjectOperator(name="op2")]
        destroy_operator_name = "destroy_op"
        key = (config_name, destroy_operator_name)
        average_mock = mock.Mock()
        average_mock.mean.return_value = 15.0

        with mock.patch.object(
            self.converter,
            "_register_key",
            side_effect=lambda key, operator_names: self.converter._running_averages.__setitem__(key, average_mock),
        ) as mock_register_key:
            self.assertEqual(
                self.converter.compute_auto_destruction_percent(config_name, project_operators, destroy_operator_name),
                15.0,
            )
            mock_register_key.assert_called_once_with(key, ["op1", "op2"])
            average_mock.mean.assert_called_once_with(self.converter._auto_init_percent)
