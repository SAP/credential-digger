import unittest
from unittest.mock import Mock, patch

from credentialdigger.client_sqlite import SqliteClient
from parameterized import param, parameterized


class TestScans(unittest.TestCase):

    @classmethod
    @patch("credentialdigger.client_sqlite.connect")
    def setUpClass(cls, mock_connect):
        """ Instatiate a mock client (we don't need any db for these tests) """
        mock_connect.return_value = Mock()
        cls.client = SqliteClient(Mock())

    def test_analyze_discoveries(self):
        """
        Mocking the ML models, assert that analyzed discoveries get retuned
        with their status changed
        """
        # Mock ML models
        model_manager = Mock()
        model_manager.launch_model = lambda d: d["id"] < 5

        # Mock discoveries
        old_discoveries = [{"id": i, "state": "new"} for i in range(10)]

        new_discoveries = self.client._analyze_discoveries(
            model_manager=model_manager,
            discoveries=old_discoveries,
            debug=False)

        for i in range(0, 5):
            self.assertTrue(new_discoveries[i]["state"] == "false_positive")
        for i in range(5, 10):
            self.assertTrue(new_discoveries[i]["state"] == "new")

        # Running the analysis again should not affect already analyzed
        # discoveries
        model_manager.launch_model = lambda d: d["id"] < 6
        new_discoveries = self.client._analyze_discoveries(
            model_manager=model_manager,
            discoveries=old_discoveries,
            debug=False)

        for i in range(0, 6):
            self.assertTrue(new_discoveries[i]["state"] == "false_positive")
        for i in range(6, 10):
            self.assertTrue(new_discoveries[i]["state"] == "new")

    def test_analyze_discoveries_empty(self):
        """ `_analyze_discoveries` should return an empty list if input is
        an empty list """
        model_manager = Mock()
        old_discoveries = []

        new_discoveries = self.client._analyze_discoveries(
            model_manager=model_manager,
            discoveries=old_discoveries,
            debug=False)

        self.assertTrue(len(new_discoveries) == 0)

