import unittest
from unittest.mock import Mock, patch

from credentialdigger.client_sqlite import SqliteClient


class TestScans(unittest.TestCase):
    @classmethod
    @patch("credentialdigger.client_sqlite.connect")
    def setUp(self, mock_connect):
        """ Instatiate a mock client (we don't need any db for these tests) """
        mock_connect.return_value = Mock()
        self.client = SqliteClient(Mock())
        self.client.get_rules = Mock(return_value=[{}])
        self.client.add_discoveries = Mock(return_value=[])
        self.client.delete_discoveries = Mock()
        self.client.delete_repo = Mock()

    def test_analyze_discoveries_with_debug(self):
        """
        Mocking the ML models, assert that analyzed discoveries get retuned
        with their status changed.

        Running this test with debug triggers the model_manager.launch_model
        method.
        """
        # Mock ML models
        model_manager = Mock()
        model_manager.launch_model = lambda d: d["id"] < 5

        # Mock discoveries
        old_discoveries = [{"id": i, "state": "new"} for i in range(10)]

        new_discoveries = self.client._analyze_discoveries(
            model_manager=model_manager,
            discoveries=old_discoveries,
            debug=True)

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
            debug=True)

        for i in range(0, 6):
            self.assertTrue(new_discoveries[i]["state"] == "false_positive")
        for i in range(6, 10):
            self.assertTrue(new_discoveries[i]["state"] == "new")

    # TODO: mock launch_model_batch method
    # def test_analyze_discoveries_without_debug(self):
    #     """
    #     Mocking the ML models, assert that analyzed discoveries get retuned
    #     with their status changed

    #     Running this test without debug triggers the
    #     model_manager.launch_model_batch method.
    #     """
    #     # Mock ML models
    #     model_manager = Mock()
    #     model_manager.launch_model_batch =  # TODO

    #     # Mock discoveries
    #     old_discoveries = [{"id": i, "state": "new"} for i in range(10)]

    #     new_discoveries = self.client._analyze_discoveries(
    #         model_manager=model_manager,
    #         discoveries=old_discoveries,
    #         debug=False)

    #     for i in range(0, 5):
    #         self.assertTrue(new_discoveries[i]["state"] == "false_positive")
    #     for i in range(5, 10):
    #         self.assertTrue(new_discoveries[i]["state"] == "new")

    #     # Running the analysis again should not affect already analyzed
    #     # discoveries
    #     model_manager.launch_model = lambda d: d["id"] < 6
    #     new_discoveries = self.client._analyze_discoveries(
    #         model_manager=model_manager,
    #         discoveries=old_discoveries,
    #         debug=False)

    #     for i in range(0, 6):
    #         self.assertTrue(new_discoveries[i]["state"] == "false_positive")
    #     for i in range(6, 10):
    #         self.assertTrue(new_discoveries[i]["state"] == "new")

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

    def test_get_scan_rules(self):
        """ All rules shoould be returned """
        self.client.get_rules.return_value = [{"id": 1}, {"id": 2}]
        rules = self.client._get_scan_rules()
        self.assertTrue(len(rules) == 2)

    def test_get_scan_rules_empty_rules_result(self):
        """ A resulting empty ruleset should raise an error """
        self.client.get_rules.return_value = []
        with self.assertRaises(ValueError):
            self.client._get_scan_rules()

    @patch('credentialdigger.scanners.git_scanner.GitScanner')
    def test_scan_valid(self, mock_scanner):
        """ No errors should be thrown without optional parameters

        These are unit tests, and are therefore not constructed to test actual
        behavior of the scan funciton. Instead, they are intended to test
        its parameters.
        """
        mock_scanner.scan = Mock(return_value=[])
        self.client._scan("", mock_scanner)

    @patch('credentialdigger.scanners.git_scanner.GitScanner')
    def test_scan_force(self, mock_scanner):
        """ Using `force` should remove all discoveries of the repo """
        mock_scanner.scan = Mock(return_value=[])
        self.client._scan("", mock_scanner, force=True)
        self.client.delete_discoveries.assert_called()

    @patch('credentialdigger.scanners.git_scanner.GitScanner')
    def test_scan_invalid_new_repo(self, mock_scanner):
        """ A newly inserted repo should be removed on scan fail """
        mock_scanner.scan.side_effect = Exception()

        with self.assertRaises(Exception):
            self.client._scan("", mock_scanner)
        self.client.delete_repo.assert_called()

    @patch('credentialdigger.scanners.git_scanner.GitScanner')
    def test_scan_invalid_old_repo(self, mock_scanner):
        """ An existing repo should not be removed on scan fail """
        mock_scanner.scan.side_effect = Exception()
        self.client.add_repo = Mock(return_value=False)

        with self.assertRaises(Exception):
            self.client._scan("", mock_scanner)
        self.client.delete_repo.assert_not_called()
