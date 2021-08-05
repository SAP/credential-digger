import os
import tempfile
import unittest

import pandas as pd

from credentialdigger.cli import cli
from credentialdigger.client_sqlite import SqliteClient
from parameterized import param, parameterize


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

                    'file_name': 'i',
                    'commit_id': 'new',
                    'line_number': 'i',
                    'snippet': 'pwd=pwd',
                    'rule_id': 5,
                    'state': state,
                    'timestamp': '2021-08-05T01:13',
                }
                discoveries.append(discovery)
            discoveries_count += 1
        client.add_discoveries(discoveries, 'test_repo')