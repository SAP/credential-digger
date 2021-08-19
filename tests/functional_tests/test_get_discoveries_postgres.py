import os
import random
import tempfile
import unittest

import pandas as pd
from credentialdigger.cli import cli
from credentialdigger.client_postgres import PgClient
from parameterized import param, parameterized

REPO_URL = ''.join(random.choice('0123456789ABCDEF') for i in range(16))


class TestGetDiscoveries(unittest.TestCase):
    dotenv = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')

    @classmethod
    def setUpClass(cls):
        # Add rules
        cli.main(['', 'add_rules', '--dotenv', cls.dotenv,
                  'tests/functional_tests/test_rules.yml'])

        # Set CSV temporary export path
        cls.tmp_path = tempfile.mkdtemp()
        cls.csv_path = os.path.join(cls.tmp_path, 'test.csv')

        # Set up Postgres client
        client = PgClient(dbname=os.getenv('POSTGRES_DB'),
                          dbuser=os.getenv('POSTGRES_USER'),
                          dbpassword=os.getenv('POSTGRES_PASSWORD'),
                          dbhost=os.getenv('DBHOST'),
                          dbport=os.getenv('DBPORT'))

        client.add_repo(REPO_URL)

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
        client.add_discoveries(discoveries, REPO_URL)
        cls.client = client

    @classmethod
    def tearDownClass(cls):
        """ Remove the repo and all its discoveries. """
        cls.client.delete_repo(REPO_URL)
        cls.client.delete_discoveries(REPO_URL)
        os.remove(cls.csv_path)

    @parameterized.expand([
        param(state='new', count=5),
        param(state='false_positive', count=6),
        param(state='addressing', count=7),
        param(state='not_relevant', count=8),
        param(state='fixed', count=9)
    ])
    def test_get_discoveries(self, state, count):
        """ Test if we retrieve the correct number of discoveries for every
        possible state value.

        Parameters
        ----------
        state: str
            The state to filter discoveries on
        count: int
            The expected number of discoveries to be returned
        """
        with self.assertRaises(SystemExit) as cm:
            cli.main(
                [
                    '',
                    'get_discoveries',
                    REPO_URL,
                    '--save',
                    self.csv_path,
                    '--state',
                    state,
                    '--dotenv',
                    self.dotenv
                ]
            )
        self.assertEqual(cm.exception.code, count)

    @parameterized.expand([
        param(file='danger', count=5),
        param(file='fake_file', count=30)
    ])
    def test_get_discoveries_per_file(self, file, count):
        """ Test if we retrieve the correct number of discoveries based on
        filename input.

        Parameters
        ----------
        file: str
            The file name to filter discoveries on
        count: int
            The expected number of discoveries to be returned
        """
        with self.assertRaises(SystemExit) as cm:
            cli.main(
                [
                    '',
                    'get_discoveries',
                    REPO_URL,
                    '--save',
                    self.csv_path,
                    '--filename',
                    file,
                    '--dotenv',
                    self.dotenv
                ]
            )
        self.assertEqual(cm.exception.code, count)

    def test_csv_written(self):
        """ Test if the CLI command writes correctly the CSV file. """
        with self.assertRaises(SystemExit):
            cli.main(
                [
                    '',
                    'get_discoveries',
                    REPO_URL,
                    '--save',
                    self.csv_path,
                    '--dotenv',
                    self.dotenv
                ]
            )
        data_frame = pd.read_csv(self.csv_path)
        try:
            assert data_frame.notna().values.all()
        except AssertionError:
            assert False, 'CSV file contains NaN'
