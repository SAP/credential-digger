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
                    'file_name': 'fake_file',
                    'commit_id': '0xtmp_commit_id',
                    'line_number': '1',
                    'snippet': 'tmp_snippet',
                    'rule_id': i,
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
        pass

    @parameterized.expand([
        param(state='new', count=5),
        param(state='false_positive', count=6),
        param(state='addressing', count=7),
        param(state='not_relevant', count=8),
        param(state='fixed', count=9),
        param(state='all', count=35)
    ])
    def test_get_discoveries(self, state, count):
        pass
