import os
import tempfile
import unittest

import pandas as pd

from credentialdigger.cli import cli
from credentialdigger.client_sqlite import SqliteClient
from parameterized import param, parameterized


class TestGetDiscoveries(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set up sqlite database and CSV export temporary paths
        cls.tmp_path = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.tmp_path, 'test_db.sqlite')
        cls.csv_path = os.path.join(cls.tmp_path, 'test.csv')

        # Set up sqlite database
        client = SqliteClient(cls.db_path)
        client.add_rules_from_file('tests/functional_tests/test_rules.yml')
        client.add_repo('test_repo')

        # Insert fake discoveries
        discoveries = []
        discoveries_count = 5
        for state in ['new', 'false_positive', 'addressing',
                             'not_relevant', 'fixed']:
            for i in range(discoveries_count):
                discovery = {
                    'file_name': 'danger' if state == 'new' else 'fake_file',
                    'commit_id': '0xtmp_commit_id',
                    'line_number': '1',
                    'snippet': 'tmp_snippet',
                    'rule_id': 1,
                    'state': state,
                    'timestamp': '2021-08-05T01:13',
                }
                discoveries.append(discovery)
            discoveries_count += 1
        client.add_discoveries(discoveries, 'test_repo')

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.db_path)
        os.remove(cls.csv_path)

    @parameterized.expand([
        param(state='new', count=5),
        param(state='false_positive', count=6),
        param(state='addressing', count=7),
        param(state='not_relevant', count=8),
        param(state='fixed', count=9),
        param(state='all', count=35)
    ])
    def test_get_discoveries(self, state, count):
        # Test if retrieve the correct number of discoveries for every possible
        # state
        with self.assertRaises(SystemExit) as cm:
            cli.main(
                [
                    '',
                    'get_discoveries',
                    'test_repo',
                    '--sqlite',
                    self.db_path,
                    '--save',
                    self.csv_path,
                    '--state',
                    state
                ]
            )
        self.assertEqual(cm.exception.code, count)

    @parameterized.expand([
        param(file='danger', count=5),
        param(file='fake_file', count=30)
    ])
    def test_get_discoveries_per_file(self, file, count):
        # Test if retrieve the correct number of discoveries for specific
        # file name
        with self.assertRaises(SystemExit) as cm:
            cli.main(
                [
                    '',
                    'get_discoveries',
                    'test_repo',
                    '--sqlite',
                    self.db_path,
                    '--save',
                    self.csv_path,
                    '--filename',
                    file
                ]
            )
        self.assertEqual(cm.exception.code, count)

    def test_csv_written(self):
        with self.assertRaises(SystemExit):
            cli.main(
                [
                    '',
                    'get_discoveries',
                    'test_repo',
                    '--sqlite',
                    self.db_path,
                    '--save',
                    self.csv_path,
                    '--state',
                    'all'
                ]
            )
        data_frame = pd.read_csv(self.csv_path)
        try:
            assert data_frame.notna().values.all()
        except AssertionError:
            assert False, ' CSV file contains NaN'
